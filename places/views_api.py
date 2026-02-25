from django.utils import timezone
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Place
from .models.analytics import PlaceDailyView

@method_decorator(csrf_exempt, name='dispatch')
class TrackContactClickView(View):
    def post(self, request, pk):
        place = get_object_or_404(Place, pk=pk)
        today = timezone.now().date()
        
        
        # If created, update_or_create sets default, but F() works on existing.
        # To be safe and simple for high concurrency:
        obj, created = PlaceDailyView.objects.get_or_create(place=place, date=today)
        if not created:
            obj.contact_clicks = F('contact_clicks') + 1
            obj.save(update_fields=['contact_clicks'])
        else:
            obj.contact_clicks = 1
            obj.save(update_fields=['contact_clicks'])
            
        return JsonResponse({'status': 'ok', 'clicks': obj.contact_clicks})
