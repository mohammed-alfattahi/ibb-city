"""
Review Service - Business Logic for Reviews and Replies.

This service encapsulates all business logic for:
- Creating and updating reviews
- Pinning reviews
- Managing replies
- Content validation
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from interactions.models import Review
from management.models import AuditLog


class ReviewService:
    """Service for handling review-related operations."""
    
    @staticmethod
    def create_review(user, place, rating: int, comment: str, ip_address: str = None) -> tuple[bool, object]:
        """
        Create a new review with moderation.
        Returns: (success, result_obj) where result_obj is Review or Message String or ModerationResult
        """
        # 1. Check existing
        if Review.objects.filter(user=user, place=place).exists():
            return False, "لديك تقييم سابق لهذا المكان. يمكنك تعديله بدلاً من إضافة تقييم جديد."
        
        # 2. Basic Validation
        if not 1 <= rating <= 5:
            return False, "التقييم يجب أن يكون بين 1 و 5."
        
        # 3. Moderation
        from management.services.moderation_service import analyze_text, log_moderation_event
        
        mod_result = analyze_text(comment, user=user)
        if mod_result.action == 'block':
            log_moderation_event(user, comment, mod_result, place, ip_address)
            return False, mod_result  # Return result object to let view handle message
            
        # 4. Anti-Abuse (Rate Limit - handled by view decorator usually, but business rule here too?)
        # Keeping view decorator for strictness, but maybe check here for logic?
        # Leaving rate limit to view/decorator for now as per Architecture doc "lightweight services". 
        # Actually Service should enforce rules.
        from django.utils import timezone
        from datetime import timedelta
        last_24h = timezone.now() - timedelta(hours=24)
        if Review.objects.filter(user=user, created_at__gte=last_24h).count() >= 10:
             return False, "لقد تجاوزت الحد اليومي للتقييمات."

        # 5. Create
        try:
            with transaction.atomic():
                review = Review.objects.create(
                    user=user,
                    place=place,
                    rating=rating,
                    comment=comment.strip()
                )
                
                # Update Aggregates
                ReviewService._update_place_rating(place)
                
                # Warn if needed
                if mod_result.action == 'warn':
                    log_moderation_event(user, comment, mod_result, place, ip_address)
                    # We return review, but view needs to know about warning.
                    # We can attach it to review object temporarily
                    review._moderation_warning = mod_result.message
                
                # Notify
                ReviewService._notify_establishment_owner(place, review)
                
                return True, review
        except Exception as e:
            return False, f"Error: {str(e)}"

    @staticmethod
    def update_review(user, review_id: int, rating: int = None, comment: str = None, ip_address: str = None) -> tuple[bool, object]:
        """Update review with moderation."""
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return False, "التقييم غير موجود."
            
        if review.user != user and not user.is_staff:
             return False, "ليس لديك صلاحية."

        # Moderation check if comment changes
        from management.services.moderation_service import analyze_text, log_moderation_event
        mod_warning = None
        
        if comment is not None:
            if len(comment.strip()) < 10:
                 return False, "10 chars min."
            
            mod_result = analyze_text(comment, user=user)
            if mod_result.action == 'block':
                log_moderation_event(user, comment, mod_result, review.place, ip_address)
                return False, mod_result
            
            if mod_result.action == 'warn':
                log_moderation_event(user, comment, mod_result, review.place, ip_address)
                mod_warning = mod_result.message
                
            review.comment = comment.strip()
            
        if rating is not None:
             if not 1 <= rating <= 5:
                  return False, "1-5 only."
             review.rating = rating
             
        review.save()
        ReviewService._update_place_rating(review.place)
        
        if mod_warning:
            review._moderation_warning = mod_warning
            
        return True, review

    @staticmethod
    def _update_place_rating(place):
        from django.db.models import Avg, Count
        qs = Review.objects.filter(place=place, visibility_state='visible')
        stats = qs.aggregate(avg=Avg('rating'), count=Count('id'))
        place.avg_rating = round(stats['avg'] or 0, 2)
        place.rating_count = stats['count'] or 0
        place.save(update_fields=['avg_rating', 'rating_count'])

    @staticmethod
    def _notify_establishment_owner(place, review):
        # Notify establishment owner about a new review (if applicable).
        try:
            from interactions.notifications.notification_service import NotificationService

            owner = None
            if hasattr(place, 'establishment'):
                owner = place.establishment.owner
            elif hasattr(place, 'owner'):
                owner = place.owner

            if not owner:
                return

            NotificationService.emit_event(
                event_name='NEW_REVIEW',
                payload={
                    'place_name': getattr(place, 'name', ''),
                    'rating': getattr(review, 'rating', None),
                    'url': f"/partner/establishments/{place.pk}/"
                },
                audience_criteria={'user_id': owner.id},
                priority='normal'
            )
        except Exception:
            # Never let notification failures break review flow
            return

