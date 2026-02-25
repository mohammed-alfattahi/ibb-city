from django.views.generic import ListView, DetailView, View
from django.db.models import Q
from .models import InvestmentOpportunity, Advertisement
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.cache import cache
from django.conf import settings
from .selectors import get_random_active_ad

class InvestmentListView(ListView):
    model = InvestmentOpportunity
    template_name = 'investments/list.html'
    context_object_name = 'investments'
    paginate_by = 9

    def get_queryset(self):
        return InvestmentOpportunity.objects.filter(status='Open').order_by('-created_at')

class InvestmentDetailView(DetailView):
    model = InvestmentOpportunity
    template_name = 'investments/detail.html'
    context_object_name = 'investment'

class OfferListView(ListView):
    model = Advertisement
    template_name = 'offers/offer_list.html'
    context_object_name = 'offers'
    paginate_by = 12

    def get_queryset(self):
        today = timezone.localdate()
        queryset = Advertisement.objects.filter(
            status='active',
            start_date__lte=today
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        ).select_related('place').order_by('-created_at')
        
        # Filter by category (if passed via GET)
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(place__category__id=category_id)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from places.models import Category
        # Pass category objects for iteration (id, name)
        context['categories'] = [(c.id, c.name) for c in Category.objects.all()]
        return context

class OfferDetailView(DetailView):
    model = Advertisement
    template_name = 'offers/offer_detail.html'
    context_object_name = 'offer'

    def get_queryset(self):
        # Allow viewing active ads only
        today = timezone.localdate()
        return Advertisement.objects.filter(
            status='active',
            start_date__lte=today
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        )


class AdSlotView(View):
    """
    Lightweight endpoint to fetch ad slots on demand (HTMX/AJAX).
    """
    TEMPLATE_MAP = {
        'navbar': 'partials/components/ad_navbar.html',
        'sidebar': 'partials/components/ad_sidebar.html',
        'banner': 'partials/components/ad_banner.html',
    }

    def get(self, request, placement):
        cache_key = f"adslot_html:{placement}"
        cached_html = cache.get(cache_key)
        
        if cached_html is not None:
            if cached_html == "":
                return HttpResponse('', status=204)
            return HttpResponse(cached_html)

        template = self.TEMPLATE_MAP.get(placement)
        if not template:
            return HttpResponse('', status=204)

        ad = get_random_active_ad(placement)
        
        ttl = getattr(settings, 'AD_SLOT_HTML_CACHE_SECONDS', 30)
        
        if not ad:
            # Cache empty marker to avoid repeated DB hits
            cache.set(cache_key, "", ttl)
            return HttpResponse('', status=204)

        # Render WITHOUT request to avoid triggering global context processors
        html = render_to_string(template, {'ad': ad})
        cache.set(cache_key, html, ttl)
        return HttpResponse(html)


# ============================================
# Weather Alerts Public View
# ============================================
from .models import WeatherAlert
from django.utils import timezone

class WeatherAlertPublicView(ListView):
    """عرض تنبيهات الطقس النشطة للسياح"""
    model = WeatherAlert
    template_name = 'pages/weather_alerts.html'
    context_object_name = 'active_alerts'
    
    def get_queryset(self):
        now = timezone.now()
        # عرض التنبيهات التي لم تنتهِ صلاحيتها أو التي ليس لها تاريخ انتهاء
        return WeatherAlert.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).order_by('-severity', '-created_at')
