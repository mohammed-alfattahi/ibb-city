import csv
import io
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, F
from django.contrib.auth import get_user_model
from interactions.models import Report, Review
from places.models import Establishment
# from management.models import Advertisement # If needed

User = get_user_model()

class ReportingService:
    """
    Service for generating system reports and calculating KPIs.
    """

    @staticmethod
    def get_dashboard_kpis():
        """
        Calculate high-level KPIs for Executive Dashboard.
        """
        now = timezone.now()
        last_month = now - timedelta(days=30)

        # 1. Growth Metrics
        total_users = User.objects.count()
        new_users = User.objects.filter(date_joined__gte=last_month).count()
        growth_rate = (new_users / total_users * 100) if total_users > 0 else 0

        # 2. Operational Efficiency (Reports)
        resolved_reports = Report.objects.filter(status='RESOLVED', resolved_at__gte=last_month)
        avg_resolution_time = 0
        if resolved_reports.exists():
             # Approximation: We'd need created_at vs resolved_at difference
             # Logic placeholder
             pass

        # 3. Content Health
        total_reviews = Review.objects.count()
        avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0

        return {
            'growth': {
                'total_users': total_users,
                'new_users_30d': new_users,
                'growth_rate_pct': round(growth_rate, 2)
            },
            'content': {
                'total_reviews': total_reviews,
                'avg_rating': round(avg_rating, 2)
            },
            'efficiency': {
                'pending_reports': Report.objects.filter(status__in=['NEW', 'IN_PROGRESS']).count()
            }
        }

    @staticmethod
    def export_users_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['ID', 'Username', 'Email', 'Role', 'Date Joined', 'Is Active'])
        
        # Data
        users = User.objects.all().values_list('id', 'username', 'email', 'role__name', 'date_joined', 'is_active')
        for user in users:
            writer.writerow(user)
            
        return output.getvalue()

    @staticmethod
    def export_places_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['ID', 'Name', 'Category', 'Owner', 'Status', 'Rating', 'Views'])
        
        # Data
        places = Establishment.objects.all().select_related('category', 'owner')
        for p in places:
            writer.writerow([
                p.id, 
                p.name, 
                p.category.name if p.category else 'N/A', 
                p.owner.username if p.owner else 'Admin',
                'Active' if p.is_active else 'Inactive',
                p.avg_rating,
                p.view_count
            ])
            
        return output.getvalue()

    @staticmethod
    def export_partners_csv():
        # TODO: Implement Partner specifics (Application date, approval status)
        return ""
