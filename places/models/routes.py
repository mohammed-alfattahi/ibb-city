"""
Routes & Analytics Models
نماذج المسارات والتحليلات
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel
from ibb_guide.core_utils import get_client_ip
from .base import Place


class TouristRoute(TimeStampedModel):
    """Predefined tourist routes with multiple waypoints."""
    
    DIFFICULTY_LEVELS = [
        ('easy', 'سهل'),
        ('moderate', 'متوسط'),
        ('difficult', 'صعب'),
    ]
    ROUTE_TYPES = [
        ('historical', 'تاريخي'),
        ('natural', 'طبيعي'),
        ('religious', 'ديني'),
        ('cultural', 'ثقافي'),
        ('adventure', 'مغامرة'),
        ('family', 'عائلي'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="اسم المسار")
    description = models.TextField(verbose_name="وصف المسار")
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPES, default='historical', verbose_name="نوع المسار")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='easy', verbose_name="مستوى الصعوبة")
    
    estimated_duration = models.PositiveIntegerField(help_text="بالدقائق", verbose_name="المدة التقديرية")
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="المسافة (كم)")
    
    waypoints = models.ManyToManyField(
        'Place',
        through='RouteWaypoint',
        related_name='routes',
        verbose_name="نقاط المسار"
    )
    
    best_time = models.CharField(max_length=100, blank=True, verbose_name="أفضل وقت للزيارة")
    tips = models.TextField(blank=True, verbose_name="نصائح للزوار")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    is_featured = models.BooleanField(default=False, verbose_name="مميز")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_routes',
        verbose_name="أنشئ بواسطة"
    )
    
    class Meta:
        verbose_name = "مسار سياحي"
        verbose_name_plural = "المسارات السياحية"
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.name
    
    def get_waypoints_ordered(self):
        return self.routewaypoint_set.all().order_by('order').select_related('place')
    
    def get_coordinates(self):
        return [
            {'lat': wp.place.latitude, 'lng': wp.place.longitude, 'name': wp.place.name}
            for wp in self.get_waypoints_ordered()
            if wp.place.latitude and wp.place.longitude
        ]


class RouteWaypoint(models.Model):
    """Through model for route waypoints with ordering."""
    route = models.ForeignKey(TouristRoute, on_delete=models.CASCADE)
    place = models.ForeignKey('Place', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")
    stop_duration = models.PositiveIntegerField(default=30, help_text="بالدقائق", verbose_name="مدة التوقف")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    class Meta:
        verbose_name = "نقطة مسار"
        verbose_name_plural = "نقاط المسار"
        ordering = ['order']
        unique_together = ['route', 'place']
    
    def __str__(self):
        return f"{self.route.name} - {self.order}. {self.place.name}"


class PlaceViewLog(models.Model):
    """سجل مشاهدات المعالم - View Tracking"""
    
    place = models.ForeignKey(
        Place, on_delete=models.CASCADE,
        related_name='view_logs', verbose_name=_('المعلم')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='place_views', verbose_name=_('المستخدم')
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('عنوان IP'))
    user_agent = models.TextField(blank=True, verbose_name=_('متصفح المستخدم'))
    referer = models.URLField(max_length=500, blank=True, verbose_name=_('الصفحة المرجعية'))
    session_key = models.CharField(max_length=40, blank=True, verbose_name=_('مفتاح الجلسة'))
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('وقت المشاهدة'))
    
    class Meta:
        verbose_name = _('سجل مشاهدة')
        verbose_name_plural = _('سجلات المشاهدات')
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['-viewed_at']),
            models.Index(fields=['place']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.place.name} - {self.viewed_at}"
    
    @classmethod
    def log_view(cls, request, place):
        """تسجيل مشاهدة معلم"""
        ip_address = get_client_ip(request)  # استخدام الدالة الموحدة
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        referer = request.META.get('HTTP_REFERER', '')[:500] if request.META.get('HTTP_REFERER') else ''
        session_key = request.session.session_key or ''
        
        log = cls.objects.create(
            place=place,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            session_key=session_key
        )
        
        Place.objects.filter(pk=place.pk).update(view_count=models.F('view_count') + 1)
        return log
    
    @classmethod
    def get_popular_places(cls, days=30, limit=10):
        """الحصول على المعالم الأكثر مشاهدة"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        since = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            viewed_at__gte=since
        ).values('place').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:limit]
