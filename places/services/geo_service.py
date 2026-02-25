"""
Geo Service
Centralized geospatial calculations and nearby queries.

All location-based features MUST use this service.
No raw geo math in views.
"""
import math
import logging
from typing import Optional, Tuple
from decimal import Decimal
from django.db.models import QuerySet, F, FloatField, ExpressionWrapper
from django.db.models.functions import Sqrt, Power, Cos, Radians

logger = logging.getLogger(__name__)


# ==========================================
# Constants
# ==========================================

EARTH_RADIUS_KM = 6371.0
MAX_RADIUS_KM = 50.0
DEFAULT_RADIUS_KM = 10.0
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


# ==========================================
# Haversine Distance Calculation
# ==========================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


# ==========================================
# Bounding Box Prefilter
# ==========================================

def get_bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for prefiltering.
    
    Returns:
        (min_lat, max_lat, min_lon, max_lon)
    """
    # Approximate degrees per km at given latitude
    lat_delta = radius_km / 111.0  # ~111 km per degree of latitude
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
    
    return (
        lat - lat_delta,
        lat + lat_delta,
        lon - lon_delta,
        lon + lon_delta
    )


def apply_bounding_box(queryset: QuerySet, lat: float, lon: float, radius_km: float) -> QuerySet:
    """
    Apply bounding box filter to queryset for performance.
    This is a fast rectangular prefilter before exact distance calculation.
    """
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_km)
    
    return queryset.filter(
        latitude__gte=min_lat,
        latitude__lte=max_lat,
        longitude__gte=min_lon,
        longitude__lte=max_lon
    )


# ==========================================
# Distance Annotation (Approximate)
# ==========================================

def annotate_distance(queryset: QuerySet, lat: float, lon: float) -> QuerySet:
    """
    Annotate queryset with approximate distance in km.
    Uses simplified Euclidean approximation for speed.
    
    For exact distance, use haversine_distance() on individual results.
    """
    # Simplified Pythagorean approximation (accurate for small distances)
    lat_diff = Power(F('latitude') - lat, 2)
    lon_diff = Power((F('longitude') - lon) * Cos(Radians(lat)), 2)
    
    return queryset.annotate(
        distance_approx=ExpressionWrapper(
            Sqrt(lat_diff + lon_diff) * 111,  # Convert degrees to km
            output_field=FloatField()
        )
    )


def order_by_distance(queryset: QuerySet, lat: float, lon: float) -> QuerySet:
    """Order queryset by distance from point."""
    return annotate_distance(queryset, lat, lon).order_by('distance_approx')


# ==========================================
# Main API
# ==========================================

def get_nearby_establishments(
    lat: float,
    lon: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    limit: int = DEFAULT_LIMIT,
    category_id: int = None,
    exclude_ids: list = None
) -> QuerySet:
    """
    Get nearby approved establishments ordered by distance.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Search radius in kilometers (max 50)
        limit: Maximum results to return (max 100)
        category_id: Optional category filter
        exclude_ids: List of establishment IDs to exclude
        
    Returns:
        QuerySet of Establishment ordered by distance
    """
    from places.models import Establishment
    
    # Enforce limits
    radius_km = min(radius_km, MAX_RADIUS_KM)
    limit = min(limit, MAX_LIMIT)
    
    # Start with public establishments only (approved + active)
    queryset = Establishment.public.all()
    
    # Exclude nulls
    queryset = queryset.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Apply bounding box prefilter
    queryset = apply_bounding_box(queryset, lat, lon, radius_km)
    
    # Apply category filter
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    # Exclude specific IDs
    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)
    
    # Annotate and order by distance
    queryset = order_by_distance(queryset, lat, lon)
    
    # Filter by exact radius using annotation
    queryset = queryset.filter(distance_approx__lte=radius_km)
    
    # Optimize for list display
    queryset = queryset.select_related('owner', 'category')
    
    # Apply limit
    return queryset[:limit]


def get_nearby_places(
    lat: float,
    lon: float,
    radius_km: float = DEFAULT_RADIUS_KM,
    limit: int = DEFAULT_LIMIT,
    place_type: str = None,
    exclude_ids: list = None
) -> QuerySet:
    """
    Get nearby places (landmarks, attractions) ordered by distance.
    """
    from places.models import Place
    
    radius_km = min(radius_km, MAX_RADIUS_KM)
    limit = min(limit, MAX_LIMIT)
    
    queryset = Place.objects.filter(is_active=True)
    queryset = queryset.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    queryset = apply_bounding_box(queryset, lat, lon, radius_km)
    
    if place_type:
        queryset = queryset.filter(place_type=place_type)
        
    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)
    
    queryset = order_by_distance(queryset, lat, lon)
    queryset = queryset.filter(distance_approx__lte=radius_km)
    
    return queryset[:limit]


def calculate_distances_for_results(results: list, lat: float, lon: float) -> list:
    """
    Calculate exact Haversine distances for a list of results.
    Use after fetching to get accurate distances for display.
    
    Args:
        results: List of objects with latitude/longitude attributes
        lat, lon: Reference point
        
    Returns:
        Same list with 'exact_distance_km' attribute added
    """
    for item in results:
        if item.latitude and item.longitude:
            item.exact_distance_km = haversine_distance(
                lat, lon,
                float(item.latitude), float(item.longitude)
            )
        else:
            item.exact_distance_km = None
    
    return results
