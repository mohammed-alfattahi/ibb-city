"""
Cache Signals
Automatic cache invalidation on model changes.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from ibb_guide.services.cache_service import (
    invalidate_establishment,
    invalidate_category,
    invalidate_home
)


@receiver(post_save, sender='places.Establishment')
def invalidate_establishment_on_save(sender, instance, **kwargs):
    """Invalidate cache when establishment is saved."""
    invalidate_establishment(instance.pk)


@receiver(post_delete, sender='places.Establishment')
def invalidate_establishment_on_delete(sender, instance, **kwargs):
    """Invalidate cache when establishment is deleted."""
    invalidate_establishment(instance.pk)


@receiver(post_save, sender='places.EstablishmentMedia')
def invalidate_on_media_change(sender, instance, **kwargs):
    """Invalidate establishment cache when media changes."""
    if hasattr(instance, 'establishment') and instance.establishment:
        invalidate_establishment(instance.establishment.pk)


@receiver(post_delete, sender='places.EstablishmentMedia')
def invalidate_on_media_delete(sender, instance, **kwargs):
    """Invalidate establishment cache when media is deleted."""
    if hasattr(instance, 'establishment') and instance.establishment:
        invalidate_establishment(instance.establishment.pk)


@receiver(post_save, sender='places.EstablishmentUnit')
def invalidate_on_unit_change(sender, instance, **kwargs):
    """Invalidate establishment cache when units change."""
    if hasattr(instance, 'establishment') and instance.establishment:
        invalidate_establishment(instance.establishment.pk)


@receiver(post_delete, sender='places.EstablishmentUnit')
def invalidate_on_unit_delete(sender, instance, **kwargs):
    """Invalidate establishment cache when unit is deleted."""
    if hasattr(instance, 'establishment') and instance.establishment:
        invalidate_establishment(instance.establishment.pk)


@receiver(post_save, sender='places.Category')
def invalidate_on_category_change(sender, instance, **kwargs):
    """Invalidate category caches."""
    invalidate_category()


@receiver(post_save, sender='places.Amenity')
def invalidate_on_amenity_change(sender, instance, **kwargs):
    """Invalidate amenity caches."""
    from django.core.cache import cache
    cache.delete_pattern('amenities:*')
