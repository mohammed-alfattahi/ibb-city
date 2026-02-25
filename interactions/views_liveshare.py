from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from .models import LiveShareSession, LiveLocationPing
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class StartShareView(LoginRequiredMixin, View):
    def post(self, request):
        # Create session
        expiry = timezone.now() + timedelta(hours=2)
        session = LiveShareSession.objects.create(
            user=request.user,
            expires_at=expiry
        )
        return JsonResponse({
            'success': True,
            'token': session.token,
            'redirect_url': f"/tools/live-share/control/{session.token}/"
        })

class StopShareView(LoginRequiredMixin, View):
    def post(self, request, token):
        session = get_object_or_404(LiveShareSession, token=token, user=request.user)
        session.is_active = False
        session.save()
        return JsonResponse({'success': True})

@method_decorator(csrf_exempt, name='dispatch')
class PingView(View):
    def post(self, request):
        token = request.POST.get('token')
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')

        try:
            session = LiveShareSession.objects.get(token=token, is_active=True)
            if timezone.now() > session.expires_at:
                session.is_active = False
                session.save()
                return JsonResponse({'success': False, 'error': 'Expired'})
            
            LiveLocationPing.objects.create(
                session=session,
                latitude=lat,
                longitude=lon
            )
            return JsonResponse({'success': True})
        except LiveShareSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid Session'})

class ControlPanelView(LoginRequiredMixin, View):
    def get(self, request, token):
        session = get_object_or_404(LiveShareSession, token=token, user=request.user)
        return render(request, 'interactions/live_share/control.html', {'session': session})

class PublicShareView(View):
    def get(self, request, token):
        session = get_object_or_404(LiveShareSession, token=token)
        if not session.is_active or timezone.now() > session.expires_at:
            return render(request, 'interactions/live_share/expired.html')
        
        return render(request, 'interactions/live_share/public.html', {'session': session})

class LatestLocationAPI(View):
    def get(self, request, token):
        session = get_object_or_404(LiveShareSession, token=token)
        ping = session.pings.first() # Ordered by -created_at
        
        if ping:
            return JsonResponse({
                'lat': float(ping.latitude),
                'lon': float(ping.longitude),
                'ts': ping.created_at.isoformat()
            })
        return JsonResponse({'lat': None})
