from django.db.models import QuerySet, Exists, OuterRef
from .models import Place, Establishment
from .filters import PlaceFilter
from interactions.models import Favorite

def get_public_places(user=None) -> QuerySet[Place]:
    """
    Returns a filtered queryset of places that are publicly visible.
    Annotates with is_favorited if a user is provided.
    """
    qs = Place.objects.filter(is_active=True).select_related('category', 'establishment')
    
    if user and user.is_authenticated:
        favs = Favorite.objects.filter(user=user, place=OuterRef('pk'))
        qs = qs.annotate(is_favorited=Exists(favs))
    
    return qs.order_by('-created_at')

def get_public_establishments() -> QuerySet[Establishment]:
    """
    Returns approved and active establishments.
    """
    return Establishment.public.all().select_related('category', 'owner')

def get_nature_places(user=None) -> QuerySet[Place]:
    return get_public_places(user).filter(
        category__name__in=[
            'Nature', 'Parks', 'Mountains', 'Valley', 'Waterfalls', 'Falls',
            'شلالات', 'طبيعة', 'حدائق', 'منتزهات', 'وديان', 'جبال', 'شلال'
        ]
    )

def get_landmarks(user=None) -> QuerySet[Place]:
    return get_public_places(user).filter(
        category__name__in=[
            'Historical', 'Landmark', 'Archeological', 'Castle', 'Museum', 'History', 'Heritage',
            'معلم', 'تاريخي', 'قلعة', 'حصن', 'متحف', 'أثري', 'معالم', 'قلاع'
        ]
    )

def get_restaurants(user=None) -> QuerySet[Place]:
    return get_public_places(user).filter(
        category__name__in=[
            'Restaurant', 'Food', 'Cafe', 'Dining', 'Fast Food',
            'مطعم', 'مأكولات', 'كافيه', 'وجبات سريعة', 'مطاعم', 'مقاهي'
        ]
    )

def get_hotels(user=None) -> QuerySet[Place]:
    return get_public_places(user).filter(
        category__name__in=[
            'Hotel', 'Accommodation', 'Resort', 'Hostel', 'Apartment',
            'فندق', 'سكن', 'منتجع', 'شقق فندقية', 'فنادق', 'استراحة'
        ]
    )

def get_parks(user=None) -> QuerySet[Place]:
    return get_public_places(user).filter(
        category__name__in=[
            'Park', 'Garden', 'Entertainment', 'Amusement',
            'منتزه', 'حديقة', 'ترفيه', 'ألعاب', 'حدائق', 'منتزهات'
        ]
    )

def get_filtered_places(queryset: QuerySet, params: dict) -> QuerySet:
    """
    Apply PlaceFilter to a queryset.
    """
    return PlaceFilter(params, queryset=queryset).qs

def get_public_places_for_map() -> QuerySet[Place]:
    """
    Optimized queryset for Map View (fetches necessary fields).
    """
    return Place.objects.filter(is_active=True).select_related('category').only(
        'id', 'name', 'latitude', 'longitude', 'category__name', 'cover_image', 'slug'
    )

def get_recommended_places(user) -> QuerySet[Place]:
    """
    Returns places matching user interests.
    """
    if not user.is_authenticated or not hasattr(user, 'interests'):
        return Place.objects.none()

    interest_names = user.interests.values_list('name', flat=True)
    if not interest_names:
         # Fallback to featured or random if no interests
        return get_public_places(user).filter(is_featured=True)[:6]

    return get_public_places(user).filter(
        category__name__in=interest_names
    ).order_by('-avg_rating', '-created_at')[:6]
