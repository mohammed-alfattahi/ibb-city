"""
Place Service - Business Logic for Place Operations.

This service encapsulates all business logic for:
- Searching and filtering places
- Nearby places calculation
- Place recommendations
"""
import math
from django.db.models import Q, Avg, Count
from places.models import Place, Category


class PlaceService:
    """Service for handling place-related operations."""
    
    @staticmethod
    def search_places(query: str, category_id: int = None, directorate: str = None, 
                      min_rating: float = None, limit: int = 20) -> list:
        """
        Search places with multiple filters.
        
        Args:
            query: Search query (name, description)
            category_id: Filter by category ID
            directorate: Filter by directorate
            min_rating: Minimum rating filter
            limit: Maximum results
            
        Returns:
            QuerySet of matching places
        """
        places = Place.objects.filter(is_active=True)
        
        if query:
            places = places.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category_id:
            places = places.filter(category_id=category_id)
        
        if directorate:
            places = places.filter(directorate__icontains=directorate)
        
        if min_rating:
            places = places.filter(avg_rating__gte=min_rating)
        
        return places.order_by('-avg_rating', '-created_at')[:limit]
    
    @staticmethod
    def get_nearby_places(lat: float, lng: float, radius_km: float = 10, 
                          category: str = None, limit: int = 20) -> list:
        """
        Find places near a given location.
        Delegates to GeoService for consistent calculation.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius in kilometers
            category: Optional category filter
            limit: Maximum results
            
        Returns:
            List of places with distance info
        """
        # Delegate to GeoService for consistent nearby logic
        from places.services.geo_service import GeoService
        
        result = GeoService.get_nearby_places(lat, lng, radius_km, limit)
        
        # Apply category filter if specified
        if category:
            result = [r for r in result if category.lower() in r['place'].category.name.lower()]
        
        return result[:limit]
    
    @staticmethod
    def get_top_rated(category_id: int = None, limit: int = 10) -> list:
        """
        Get top-rated places.
        
        Args:
            category_id: Optional category filter
            limit: Maximum results
            
        Returns:
            QuerySet of top-rated places
        """
        places = Place.objects.filter(is_active=True)
        
        if category_id:
            places = places.filter(category_id=category_id)
        
        return places.order_by('-avg_rating')[:limit]
    
    @staticmethod
    def get_similar_places(place, limit: int = 4) -> list:
        """
        Get places similar to a given place (same category, different place).
        
        Args:
            place: The reference place
            limit: Maximum results
            
        Returns:
            QuerySet of similar places
        """
        return Place.objects.filter(
            category=place.category,
            is_active=True
        ).exclude(id=place.id).order_by('-avg_rating')[:limit]
    
    @staticmethod
    def get_nearby_services(place, service_types: list = None, limit: int = 5) -> list:
        """
        Get nearby services for a place (hotels, restaurants, ATMs, etc.).
        
        Args:
            place: The reference place
            service_types: List of service types to filter (e.g. ['atm', 'bank'])
            limit: Maximum results
            
        Returns:
            QuerySet of nearby ServicePoints
        """
        from places.models import ServicePoint
        
        qs = ServicePoint.objects.filter(is_active=True).exclude(id=place.id)
        
        if service_types:
            qs = qs.filter(service_type__in=service_types)
            
        # Filter by directorate for simple proximity if coordinates missing
        if not (place.latitude and place.longitude):
            return qs.filter(directorate=place.directorate).order_by('?')[:limit]
            
        # Calculate real distance
        nearby = []
        for service in qs:
            if not (service.latitude and service.longitude):
                continue
                
            dist = PlaceService._haversine(
                float(place.latitude), float(place.longitude),
                float(service.latitude), float(service.longitude)
            )
            
            if dist <= 5:  # 5km radius for services
                nearby.append({
                    'service': service,
                    'distance': dist
                })
        
        nearby.sort(key=lambda x: x['distance'])
        return [item['service'] for item in nearby[:limit]]
    
    @staticmethod
    def get_trending_places(days: int = 7, limit: int = 10) -> list:
        """
        Get trending places based on recent reviews.
        
        Args:
            days: Time period in days
            limit: Maximum results
            
        Returns:
            QuerySet of trending places
        """
        from django.utils import timezone
        from datetime import timedelta
        from interactions.models import Review
        
        since = timezone.now() - timedelta(days=days)
        
        trending = Place.objects.filter(
            is_active=True,
            reviews__created_at__gte=since
        ).annotate(
            recent_reviews=Count('reviews', filter=Q(reviews__created_at__gte=since))
        ).order_by('-recent_reviews')[:limit]
        
        return trending
    
    @staticmethod
    def get_place_statistics(place) -> dict:
        """
        Get statistics for a place.
        
        Args:
            place: The place object
            
        Returns:
            Dictionary with statistics
        """
        from interactions.models import Review, Favorite
        
        reviews = Review.objects.filter(place=place, visibility_state='visible')
        
        return {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'favorites_count': Favorite.objects.filter(place=place).count(),
            'rating_distribution': {
                i: reviews.filter(rating=i).count() for i in range(1, 6)
            }
        }
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
