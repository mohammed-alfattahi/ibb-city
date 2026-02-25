import random

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from .models.advertisements import Advertisement


def get_random_active_ad(placement: str, cache_seconds: int = 60):
    """
    Return a random active ad for a placement with short caching.
    Avoids ORDER BY '?' which is expensive on large tables.
    """
    today = timezone.localdate()
    cache_key = f"active_ad:{placement}:{today}"

    cached_id = cache.get(cache_key)
    if cached_id == 0:
        return None
    if cached_id:
        return Advertisement.objects.filter(pk=cached_id, status='active').first()

    base_qs = Advertisement.objects.filter(
        status='active',
        placement=placement,
        start_date__lte=today,
    ).filter(Q(end_date__gte=today) | Q(end_date__isnull=True))

    ids = list(base_qs.values_list('id', flat=True))
    if not ids:
        cache.set(cache_key, 0, cache_seconds)
        return None

    ad_id = random.choice(ids)
    cache.set(cache_key, ad_id, cache_seconds)
    return base_qs.filter(pk=ad_id).first()
