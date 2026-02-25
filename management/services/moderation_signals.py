"""
Moderation Signals
Invalidate cache when banned words change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from management.models.moderation import BannedWord
from management.services.moderation_service import invalidate_word_cache


@receiver(post_save, sender=BannedWord)
def on_banned_word_change(sender, instance, **kwargs):
    invalidate_word_cache()


@receiver(post_delete, sender=BannedWord)
def on_banned_word_delete(sender, instance, **kwargs):
    invalidate_word_cache()
