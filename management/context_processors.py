from django.core.cache import cache
import json
from .models import SiteSetting, Menu, SidebarWidget, SocialLink, FeatureToggle

def site_ui(request):
    """
    Context processor to provide global site settings and menus to templates.
    Optimized with role-based caching to reduce DB queries on every request.
    """
    # Determine user role for cache key
    role = "admin" if request.user.is_staff else ("user" if request.user.is_authenticated else "guest")
    cache_key = f"site_ui:{role}"
    
    # Try to get cached UI data
    cached_data = cache.get(cache_key)
    if cached_data is None:
        # Build menu filter based on role
        menu_filter = {"is_active": True}
        if role == "admin":
            menu_filter["visible_for_admins"] = True
        elif role == "user":
            menu_filter["visible_for_users"] = True
        else:
            menu_filter["visible_for_guests"] = True

        # Feature Toggles
        defaults = {
            'enable_reviews': True,
            'enable_notifications': True,
            'enable_favorites': True,
            'enable_comments': True,
            'enable_weather': True,
        }
        
        try:
            db_toggles = {t.key: t.is_enabled for t in FeatureToggle.objects.all()}
        except Exception:
            db_toggles = {}
            
        toggles = {**defaults, **db_toggles}
        
        # Prepare data for cache (300 seconds TTL)
        cached_data = {
            "site_settings": SiteSetting.objects.first(),
            "header_menu": list(Menu.objects.filter(location="header", **menu_filter).order_by("order")),
            "sidebar_menu": list(Menu.objects.filter(location="sidebar", **menu_filter).order_by("order")),
            "footer_menu": list(Menu.objects.filter(location="footer", **menu_filter).order_by("order")),
            "social_links": list(SocialLink.objects.filter(is_active=True).order_by("order")),
            "sidebar_widgets": list(SidebarWidget.objects.filter(is_visible=True).prefetch_related("links").order_by("order")),
            "feature_toggles": toggles,
            "features_json": json.dumps(toggles),
        }
        from django.conf import settings
        ttl = getattr(settings, 'CACHE_TTL_MEDIUM', 300)
        cache.set(cache_key, cached_data, ttl)

    # Add per-request dynamic data
    context = {
        **cached_data,
        "current_page": request.resolver_match.url_name if request.resolver_match else None,
        "current_role": role,
        "ui": {
            "show_sidebar": True,
        },
    }
    
    return context
