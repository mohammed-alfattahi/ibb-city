import logging
from django.shortcuts import get_object_or_404, redirect
from django.db.models import F
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import caches, cache
from django.conf import settings
from ibb_guide.core_utils import get_client_ip
from management.models.advertisements import Advertisement
from management.models.analytics import AdDailyStats

logger = logging.getLogger(__name__)

DEDUP_SECONDS = getattr(settings, 'AD_TRACKING_DEDUP_SECONDS', 600)
TRACKING_ENABLED = getattr(settings, 'AD_IMPRESSION_TRACKING_ENABLED', True)
CACHE_ALIAS = getattr(settings, 'AD_TRACKING_CACHE_ALIAS', 'default')
ad_cache = caches[CACHE_ALIAS] if CACHE_ALIAS in settings.CACHES else cache


class AdTrackingMixin:
    def _is_trackable(self, ad):
        today = timezone.localdate()
        if ad.status != 'active':
            return False
        if ad.start_date and ad.start_date > today:
            return False
        if ad.end_date and ad.end_date < today:
            return False
        return True

    def _identity_key(self, request):
        session_key = None
        try:
            session_key = request.session.session_key
        except Exception:
            session_key = None
        if session_key:
            return f"s:{session_key}"
        ip = get_client_ip(request) or "unknown"
        return f"ip:{ip}"

    def _should_count(self, request, ad_id, event_type):
        cache_key = f"adtrack:{event_type}:{ad_id}:{self._identity_key(request)}"
        if ad_cache.get(cache_key):
            return False
        ad_cache.set(cache_key, True, timeout=DEDUP_SECONDS)
        return True


class AdClickView(AdTrackingMixin, View):
    def get(self, request, pk):
        ad = get_object_or_404(Advertisement.objects.select_related('place'), pk=pk)
        
        if self._is_trackable(ad) and self._should_count(request, pk, 'click'):
            # Increment total clicks atomically
            Advertisement.objects.filter(pk=pk).update(clicks=F('clicks') + 1)
            
            # Increment daily stats
            try:
                today = timezone.localdate()
                stats, _ = AdDailyStats.objects.get_or_create(advertisement=ad, date=today)
                AdDailyStats.objects.filter(pk=stats.pk).update(clicks=F('clicks') + 1)
            except Exception:
                # Don't fail the click if stats fail
                pass
        
        # Redirect to target
        if ad.target_url:
            return redirect(ad.target_url)
        if ad.place:
            return redirect(ad.place.get_absolute_url())
        return redirect('home') # Fallback

@method_decorator(csrf_exempt, name='dispatch')
class AdImpressionView(AdTrackingMixin, View):
    def post(self, request, pk):
        self._record_impression(request, pk)
        return JsonResponse({'status': 'ok'})
    
    def get(self, request, pk):
        self._record_impression(request, pk)
        # Return 1x1 transparent pixel GIF
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return HttpResponse(pixel, content_type='image/gif')

    def _record_impression(self, request, pk):
        if not TRACKING_ENABLED:
            logger.debug(f"Impression tracking disabled. Skipping ad {pk}")
            return

        ad = Advertisement.objects.filter(pk=pk).only('id', 'status', 'start_date', 'end_date').first()
        if not ad:
            return
        
        if not self._is_trackable(ad):
            return
            
        if not self._should_count(request, pk, 'view'):
            return

        # Increment total views atomically
        Advertisement.objects.filter(pk=pk).update(views=F('views') + 1)
        
        # Increment daily stats
        try:
            today = timezone.localdate()
            stats, _ = AdDailyStats.objects.get_or_create(advertisement_id=pk, date=today)
            AdDailyStats.objects.filter(pk=stats.pk).update(views=F('views') + 1)
            logger.debug(f"Recorded impression for ad {pk}")
        except Exception as e:
            logger.error(f"Error recording impression for ad {pk}: {e}")
            pass
