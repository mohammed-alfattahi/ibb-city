from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from users.models import User, UserRegistrationLog
from places.models import Place, Establishment
from interactions.models import Review, Report
from management.models import Request, AuditLog, Advertisement, Invoice
from django.db import connection
from django.core.cache import cache
import time


class AdminDashboardService:
    """Service to gather statistics for the custom admin dashboard"""
    
    @staticmethod
    def get_system_health():
        """Check status of critical system components"""
        health = {
            'database': False,
            'cache': False,
            'db_latency': 0,
            'status': 'healthy',
        }
        
        # Check Database
        try:
            start = time.time()
            connection.ensure_connection()
            User.objects.count()
            health['db_latency'] = round((time.time() - start) * 1000, 2)
            health['database'] = True
        except Exception:
            health['database'] = False
            health['status'] = 'critical'
            
        # Check Cache
        try:
            cache.set('health_check', 'ok', 30)
            if cache.get('health_check') == 'ok':
                health['cache'] = True
        except Exception:
            health['cache'] = False
            health['status'] = 'degraded'
        
        # Overall status
        if health['database'] and health['cache']:
            health['status'] = 'healthy'
        elif health['database']:
            health['status'] = 'degraded'
        else:
            health['status'] = 'critical'
            
        return health

    @staticmethod
    def get_kpi_stats():
        """Get key performance indicators"""
        now = timezone.now()
        today = now.date()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        # Users
        total_users = User.objects.count()
        new_users_today = User.objects.filter(date_joined__date=today).count()
        new_users_week = User.objects.filter(date_joined__gte=last_week).count()
        new_users_month = User.objects.filter(date_joined__gte=last_month).count()
        
        # Places
        total_places = Place.objects.count()
        active_places = Place.objects.filter(is_active=True).count()
        
        # Establishments
        total_establishments = Establishment.objects.count()
        pending_establishments = Establishment.objects.filter(approval_status='pending').count()
        approved_establishments = Establishment.objects.filter(approval_status='approved').count()
        
        # Requests
        pending_requests = Request.objects.filter(status='pending').count()
        resolved_today = Request.objects.filter(
            status__in=['approved', 'rejected'],
            updated_at__date=today
        ).count()
        
        # Reviews
        total_reviews = Review.objects.count()
        reviews_today = Review.objects.filter(created_at__date=today).count()
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Reports
        pending_reports = Report.objects.filter(status='pending').count()
        
        # Ads & Revenue
        active_ads = Advertisement.objects.filter(status='active').count()
        pending_ads = Advertisement.objects.filter(status='pending').count()
        
        # Revenue (this month)
        month_start = today.replace(day=1)
        revenue_month = Invoice.objects.filter(
            is_paid=True,
            issue_date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month,
            'total_places': total_places,
            'active_places': active_places,
            'total_establishments': total_establishments,
            'pending_establishments': pending_establishments,
            'approved_establishments': approved_establishments,
            'pending_requests': pending_requests,
            'resolved_today': resolved_today,
            'total_reviews': total_reviews,
            'reviews_today': reviews_today,
            'avg_rating': round(avg_rating, 1),
            'pending_reports': pending_reports,
            'active_ads': active_ads,
            'pending_ads': pending_ads,
            'revenue_month': revenue_month,
        }

    @staticmethod
    def get_recent_activity(limit=10):
        """Get recent important system activities"""
        logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:limit]
        return logs

    @staticmethod
    def get_pending_items():
        """Get counts of all pending items for quick action"""
        return {
            'requests': Request.objects.filter(status='pending').count(),
            'establishments': Establishment.objects.filter(approval_status='pending').count(),
            'ads': Advertisement.objects.filter(status='pending').count(),
            'reports': Report.objects.filter(status='pending').count(),
        }

    @staticmethod
    def get_chart_data():
        """Get data for Chart.js visualizations"""
        now = timezone.now()
        
        # 1. User Growth (Last 7 days)
        user_growth = []
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).date()
            count = User.objects.filter(date_joined__date=day).count()
            user_growth.append({
                'day': day.strftime('%a'),
                'date': day.strftime('%m/%d'),
                'count': count
            })
        
        # 2. Places by Category
        places_by_category = list(
            Place.objects.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:6]
        )
        
        # 3. Request Status Distribution
        request_status = {
            'pending': Request.objects.filter(status='pending').count(),
            'approved': Request.objects.filter(status='approved').count(),
            'rejected': Request.objects.filter(status='rejected').count(),
        }
        
        # 4. Establishment Approval Status
        establishment_status = {
            'draft': Establishment.objects.filter(approval_status='draft').count(),
            'pending': Establishment.objects.filter(approval_status='pending').count(),
            'approved': Establishment.objects.filter(approval_status='approved').count(),
            'rejected': Establishment.objects.filter(approval_status='rejected').count(),
        }
        
        # 5. Reviews by Rating
        reviews_by_rating = []
        for rating in range(1, 6):
            count = Review.objects.filter(rating=rating).count()
            reviews_by_rating.append({'rating': rating, 'count': count})
        
        # 6. Revenue Trend (Last 6 months)
        revenue_trend = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=i*30)
            month_start = month_date.replace(day=1).date()
            if month_date.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            revenue = Invoice.objects.filter(
                is_paid=True,
                issue_date__gte=month_start,
                issue_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            revenue_trend.append({
                'month': month_start.strftime('%b'),
                'revenue': float(revenue)
            })
        
        return {
            'user_growth': user_growth,
            'places_by_category': places_by_category,
            'request_status': request_status,
            'establishment_status': establishment_status,
            'reviews_by_rating': reviews_by_rating,
            'revenue_trend': revenue_trend,
        }

    @staticmethod
    def get_top_places(limit=5):
        """Get top rated places"""
        return Place.objects.filter(
            is_active=True,
            avg_rating__gt=0
        ).order_by('-avg_rating', '-rating_count')[:limit]

    @staticmethod
    def get_weekly_comparison():
        """Compare this week vs last week"""
        now = timezone.now()
        this_week_start = now - timedelta(days=now.weekday())
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start
        
        this_week_users = User.objects.filter(date_joined__gte=this_week_start).count()
        last_week_users = User.objects.filter(
            date_joined__gte=last_week_start,
            date_joined__lt=last_week_end
        ).count()
        
        this_week_reviews = Review.objects.filter(created_at__gte=this_week_start).count()
        last_week_reviews = Review.objects.filter(
            created_at__gte=last_week_start,
            created_at__lt=last_week_end
        ).count()
        
        def calc_trend(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 1)
        
        return {
            'users': {
                'current': this_week_users,
                'previous': last_week_users,
                'trend': calc_trend(this_week_users, last_week_users)
            },
            'reviews': {
                'current': this_week_reviews,
                'previous': last_week_reviews,
                'trend': calc_trend(this_week_reviews, last_week_reviews)
            }
        }
