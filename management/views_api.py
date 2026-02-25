from django.http import JsonResponse
from django.views import View
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.utils import timezone
from .models.analytics import AdDailyStats

@method_decorator(login_required, name='dispatch')
class PartnerAnalyticsAPI(View):
    def get(self, request):
        if not request.user.role or request.user.role.name != 'Partner':
             return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get data for last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        
        # Aggregate clicks/views per day for ALL partner's ads
        data = AdDailyStats.objects.filter(
            advertisement__owner=request.user,
            date__range=[start_date, end_date]
        ).values('date').annotate(
            total_clicks=Sum('clicks'),
            total_views=Sum('views')
        ).order_by('date')
        
        # Prepare response (fill missing dates with 0?)
        # For simplicity, sending raw data, frontend can fill gaps or ChartJS handles it.
        # Actually, filling gaps is better for UX.
        
        stats_map = {str(d['date']): d for d in data}
        
        labels = []
        clicks = []
        views = []
        
        current = start_date
        while current <= end_date:
            date_str = str(current)
            stat = stats_map.get(date_str, {'total_clicks': 0, 'total_views': 0})
            
            labels.append(current.strftime('%d/%m')) # Format DD/MM
            clicks.append(stat['total_clicks'])
            views.append(stat['total_views'])
            
            current += timedelta(days=1)
            
        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Clicks',
                    'data': clicks,
                    'borderColor': '#0d6efd',
                    'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                },
                {
                    'label': 'Views',
                    'data': views,
                    'borderColor': '#198754',
                    'backgroundColor': 'rgba(25, 135, 84, 0.1)',
                }
            ]
        })
