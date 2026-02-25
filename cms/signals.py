from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from cms.models import UIZone, UIComponent, ZoneComponent
from cms.services.ui_builder import bump_version


@receiver(post_save, sender=UIZone)
@receiver(post_delete, sender=UIZone)
@receiver(post_save, sender=UIComponent)
@receiver(post_delete, sender=UIComponent)
@receiver(post_save, sender=ZoneComponent)
@receiver(post_delete, sender=ZoneComponent)
def _bump_cms_cache_version(**kwargs):
    bump_version()
