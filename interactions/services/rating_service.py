
from django.db import transaction
from places.models import Establishment, Place
from interactions.models import Review
from django.db.models import Avg, Count
from management.models import AuditLog

class RatingService:
    """
    Service for managing User Ratings (Reviews with stars).
    Enforces one rating per user per place.
    """
    
    @staticmethod
    def upsert_rating(user, place, rating_value, comment_text='', ip=None):
        """
        Create or Update a rating.
        """
        # Clean inputs
        try:
            rating_value = int(rating_value)
        except (ValueError, TypeError):
            return None, False, "Invalid rating value"
            
        if not (1 <= rating_value <= 5):
            return None, False, "Rating must be between 1 and 5"

        # Moderation Check
        if comment_text:
            from interactions.services.moderation_service import ModerationService
            is_safe, status, terms = ModerationService.check_content(user, place, comment_text)
            if status == 'BLOCKED':
                return None, False, f"Review content blocked due to restricted terms: {', '.join(terms)}"
            
        with transaction.atomic():
            review, created = Review.objects.update_or_create(
                user=user,
                place=place,
                defaults={
                    'rating': rating_value,
                    'comment': comment_text or '',
                    # 'is_visible': True # Assuming reviews are visible by default
                }
            )
            
            if created:
                action = 'RATING_CREATED'
            else:
                action = 'RATING_UPDATED'
                review.is_edited = True
                from django.utils import timezone
                review.edited_at = timezone.now()
                review.save()
            
            # Additional logic for Warning status could go here (e.g. flag review)
                
            # Audit Log if needed
            # AuditLog.objects.create(...) 
            
            # Update Aggregates
            RatingService.update_place_statistics(place)
            
            return review, True, "Rating saved successfully"

    @staticmethod
    def update_place_statistics(place):
        """
        Recompute avg_rating, rating_count, rating_distribution.
        """
        # Filter only visible reviews if we had is_hidden? 
        # Requirement: "A user may submit ONLY ONE rating...". Hiding guidelines were for Comments.
        # But usually we hide ratings if bad. Review model doesn't have is_hidden anymore in my refactor? 
        # Wait, I removed is_hidden from Review in my write_to_file.
        # Check interactions/models/reviews.py content I wrote.
        # I removed is_hidden.
        # If I want to support Admin Hiding of ratings, I should have kept it. 
        # But prompt said "Partner can "hide" comments... Office/admin can "admin hide" (final hide)".
        # It didn't explicitly say Ratings can be hidden, but implied "Comments and ratings system".
        # Safe to assume Ratings should be hideable too.
        # I'll check if I should add is_active to Review or if I missed it.
        # I did add is_active to BannedWord, but Review?
        qs = Review.objects.filter(place=place, visibility_state='visible')
        
        aggregates = qs.aggregate(
            avg=Avg('rating'),
            count=Count('id')
        )
        
        avg = aggregates['avg'] or 0.0
        count = aggregates['count'] or 0
        
        # Distribution (Optimized)
        rating_counts = qs.values('rating').annotate(c=Count('id'))
        dist = {str(k): 0 for k in range(1, 6)}
        for entry in rating_counts:
            # entry['rating'] is int (1-5)
            r_key = str(entry['rating'])
            if r_key in dist:
                dist[r_key] = entry['c']
            
        place.avg_rating = avg
        place.rating_count = count
        place.rating_distribution = dist
        place.save(update_fields=['avg_rating', 'rating_count', 'rating_distribution'])
