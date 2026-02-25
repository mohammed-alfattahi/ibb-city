from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import F
from .models import Advertisement

class AdClickView(View):
    def get(self, request, pk):
        ad = get_object_or_404(Advertisement, pk=pk)
        
        # Increment Clicks (Atomic update)
        # Avoid counting multiple clicks from same session if desired, 
        # but for simplicity we just increment.
        Advertisement.objects.filter(pk=pk).update(clicks=F('clicks') + 1)
        
        # Redirect to target
        if ad.place:
            return redirect('place_detail', pk=ad.place.pk)
        return redirect('home')

class AdImpressionView(View):
    def post(self, request, pk):
        # API to record view
        # Should be called via AJAX/Fetch when ad is rendered
        Advertisement.objects.filter(pk=pk).update(views=F('views') + 1)
        return JsonResponse({'status': 'ok'})
