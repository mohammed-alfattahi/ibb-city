"""management.signals

Cache invalidation hooks.

Whenever admin edits UI CMS entities (menus/sidebars/footer/site config), we invalidate
the cached UI context so the public site updates instantly without extra DB load.
"""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from management.services.ui_service import invalidate_ui_cache


def _invalidate(**kwargs):
    invalidate_ui_cache()


# Import models locally to avoid side effects at import time.
from management.models import MenuItem, SidebarItem, FooterLink, QuickAccessItem, SiteConfiguration


@receiver(post_save, sender=MenuItem)
@receiver(post_delete, sender=MenuItem)
@receiver(post_save, sender=SidebarItem)
@receiver(post_delete, sender=SidebarItem)
@receiver(post_save, sender=FooterLink)
@receiver(post_delete, sender=FooterLink)
@receiver(post_save, sender=QuickAccessItem)
@receiver(post_delete, sender=QuickAccessItem)
@receiver(post_save, sender=SiteConfiguration)
@receiver(post_delete, sender=SiteConfiguration)
def ui_cms_changed(sender, instance, **kwargs):
    _invalidate()
