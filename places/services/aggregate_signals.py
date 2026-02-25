"""
Aggregate Signals
Automatically update cached aggregates when ratings/comments change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='interactions.Review')
def update_aggregates_on_review_save(sender, instance, **kwargs):
    """Update establishment aggregates when review is created/updated."""
    from places.services.aggregate_service import update_establishment_aggregates
    
    if hasattr(instance, 'place_id') and instance.place_id:
        update_establishment_aggregates(instance.place_id)


@receiver(post_delete, sender='interactions.Review')
def update_aggregates_on_review_delete(sender, instance, **kwargs):
    """Update establishment aggregates when review is deleted."""
    from places.services.aggregate_service import update_establishment_aggregates
    
    if hasattr(instance, 'place_id') and instance.place_id:
        update_establishment_aggregates(instance.place_id)


@receiver(post_save, sender='interactions.PlaceComment')
def update_aggregates_on_comment_save(sender, instance, **kwargs):
    """Update establishment aggregates when comment is created/updated."""
    from places.services.aggregate_service import update_establishment_aggregates
    
    if hasattr(instance, 'place_id') and instance.place_id:
        update_establishment_aggregates(instance.place_id)


@receiver(post_delete, sender='interactions.PlaceComment')
def update_aggregates_on_comment_delete(sender, instance, **kwargs):
    """Update establishment aggregates when comment is deleted."""
    from places.services.aggregate_service import update_establishment_aggregates
    
    if hasattr(instance, 'place_id') and instance.place_id:
        update_establishment_aggregates(instance.place_id)
