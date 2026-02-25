"""management.services.ui_service

UI CMS aggregation + caching.

Why this exists
--------------
The project relies on context processors to inject UI content (menus, sidebars, footer,
site configuration) into *every* template.

Doing DB queries on every request is costly and doesn't scale. This service adds:

1) A single function to build the UI context.
2) A cache layer (safe for Redis/LocMem).
3) Automatic invalidation via model signals.

This is also a stepping stone to a full Page/Zone/Component builder and multi-tenant
deployment (Organization-scoped content).
"""

from __future__ import annotations

from typing import Any, Dict

from django.core.cache import cache


UI_CONTEXT_CACHE_KEY = "ui_context:v1"


def invalidate_ui_cache() -> None:
    """Invalidate cached UI context."""
    cache.delete(UI_CONTEXT_CACHE_KEY)


def get_ui_context() -> Dict[str, Any]:
    """Return the UI context dict used by templates.

    The returned structure matches what templates already use:
    - menu_items
    - sidebar_main / sidebar_features / sidebar_services
    - footer_tourism / footer_company / footer_explore / footer_social
    - quick_access_items
    - site_config
    """
    cached = cache.get(UI_CONTEXT_CACHE_KEY)
    if cached is not None:
        return cached

    # Local imports to avoid app-loading issues
    from management.models import MenuItem, SidebarItem, FooterLink, QuickAccessItem, SiteConfiguration

    # NOTE: we cache evaluated lists (not lazy QuerySets) so the cache stores actual results.
    ctx: Dict[str, Any] = {
        # Navbar with children prefetched
        "menu_items": list(
            MenuItem.objects.filter(is_active=True, parent__isnull=True)
            .prefetch_related("children")
            .order_by("order")
        ),
        # Sidebar
        "sidebar_main": list(SidebarItem.objects.filter(is_active=True, section="main").order_by("order")),
        "sidebar_features": list(SidebarItem.objects.filter(is_active=True, section="features").order_by("order")),
        "sidebar_services": list(SidebarItem.objects.filter(is_active=True, section="services").order_by("order")),
        # Footer
        "footer_tourism": list(FooterLink.objects.filter(column="tourism").order_by("order")),
        "footer_company": list(FooterLink.objects.filter(column="company").order_by("order")),
        "footer_explore": list(FooterLink.objects.filter(column="explore").order_by("order")),
        "footer_social": list(FooterLink.objects.filter(column="social").order_by("order")),
        # Quick access
        "quick_access_items": list(QuickAccessItem.objects.filter(is_active=True).order_by("order")),
        # Site config
        "site_config": SiteConfiguration.get_solo(),
    }

    # Cache for 10 minutes. Changes invalidate via signals.
    cache.set(UI_CONTEXT_CACHE_KEY, ctx, timeout=600)
    return ctx
