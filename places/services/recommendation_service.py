from django.db.models import Avg, Count
from django.utils import timezone
from places.models import Place
from interactions.models import UserInteraction

class RecommendationService:
    """
    Context-Aware Recommendation Engine.
    Scores candidates based on Quality, Context, and Personalization.
    """

    @staticmethod
    def get_recommendations(user, limit=5, lat=None, lon=None):
        """
        Get top N recommended places for the user.
        """
        # 1. Candidate Generation (All active places for now, in real app use elasticsearch/spatial)
        candidates = Place.objects.filter(is_active=True).select_related('category')
        
        scored_candidates = []
        context = RecommendationService._get_current_context(lat, lon)
        
        # Prefetch interactions for personalization
        user_interactions = {}
        if user.is_authenticated:
            # Simple Category Preferences based on favorites
            # Fixed: Use Favorite model with direct FK instead of GenericFK join
            from interactions.models import Favorite
            fav_categories = Favorite.objects.filter(
                user=user
            ).select_related('place__category').values_list(
                'place__category_id', flat=True
            ).distinct()
            user_interactions['fav_categories'] = set(fav_categories)

        for place in candidates:
            score = RecommendationService._calculate_score(place, user, context, user_interactions)
            scored_candidates.append((place, score))
        
        # Sort by Score Descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [item[0] for item in scored_candidates[:limit]]

    @staticmethod
    def _calculate_score(place, user, context, interactions):
        """
        Calculate weighted score for a single place.
        """
        score = 0.0
        
        # 1. Base Score (Quality) - Weight 40%
        # Normalize rating (0-5) to 0-100 score? Or just use raw rating * 10
        avg_rating = place.avg_rating or 0
        score += avg_rating * 10 
        
        # 2. Context Score (Time/Weather) - Weight 30%
        # Night Logic (Reuse Op 14 thought process)
        if context['is_night']:
            # Penalty for Mountains/Nature at night
            if place.category.name in ['Mountain', 'Nature', 'Jibal']: # Mock category names
                score -= 20
            # Bonus for Restaurants/Cafes
            if place.category.name in ['Restaurant', 'Cafe']:
                score += 10
        
        # 3. Personalization Score - Weight 30%
        if user.is_authenticated:
            if place.category.id in interactions.get('fav_categories', set()):
                score += 15
        
        # 4. Decay / Freshness (Optional)
        # score += 1 / (days_since_update + 1)
        
        return score

    @staticmethod
    def _get_current_context(lat, lon):
        hour = timezone.now().hour
        return {
            'is_night': hour < 6 or hour > 18,
            'weather': 'CLEAR' # Mock, would come from WeatherService
        }
