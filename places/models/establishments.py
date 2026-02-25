"""
Establishment Models
نماذج المنشآت التجارية

Visibility Rules:
- Public pages only show: approval_status='approved' AND is_active=True AND is_suspended=False
- Use Establishment.public for public queries
- Use Establishment.objects for internal/admin queries
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .base import Place, Amenity

User = get_user_model()


class EstablishmentQuerySet(models.QuerySet):
    """Optimized queryset for Establishment."""
    
    def approved(self):
        """Filter only approved and active establishments."""
        return self.filter(
            approval_status='approved',
            is_active=True,
            is_suspended=False
        )
    
    def pending(self):
        """Filter pending establishments."""
        return self.filter(approval_status='pending')
    
    def with_owner(self):
        """Select related owner."""
        return self.select_related('owner')
    
    def with_category(self):
        """Select related category."""
        return self.select_related('category')
    
    def with_relations(self):
        """Optimize for detail view - all relations."""
        return self.select_related(
            'owner',
            'category',
            'approved_by'
        ).prefetch_related(
            'amenities',
            'media',
            'units'
        )
    
    def for_list(self):
        """Optimized for list display."""
        return self.select_related(
            'owner',
            'category'
        ).only(
            'id', 'name', 'description', 'cover_image',
            'approval_status', 'is_active', 'is_open_now',
            'created_at', 'owner__username', 'category__name'
        )


class PublicEstablishmentManager(models.Manager):
    """
    Manager that returns only publicly visible establishments.
    Use Establishment.public.all() for public-facing queries.
    """
    def get_queryset(self):
        return EstablishmentQuerySet(self.model, using=self._db).filter(
            approval_status='approved',
            is_active=True,
            is_suspended=False
        )
    
    def with_relations(self):
        """Get public establishments with all relations."""
        return self.get_queryset().with_relations()
    
    def for_list(self):
        """Get public establishments optimized for list."""
        return self.get_queryset().for_list()


class EstablishmentManager(models.Manager):
    """Default manager with optimization helpers."""
    
    def get_queryset(self):
        return EstablishmentQuerySet(self.model, using=self._db)
    
    def approved(self):
        return self.get_queryset().approved()
    
    def pending(self):
        return self.get_queryset().pending()
    
    def with_relations(self):
        return self.get_queryset().with_relations()
    
    def for_list(self):
        return self.get_queryset().for_list()


class Establishment(Place):
    """Partner-owned establishment extending Place."""
    
    SENSITIVE_FIELDS = [
        'name', 'description', 'address_text', 'latitude', 'longitude',
        'category', 'directorate', 'road_condition', 'classification'
    ]
    NON_SENSITIVE_FIELDS = [
        'contact_info', 'working_hours', 'amenities', 'is_open_status',
        'price_range', 'opening_hours_text', 'cover_image', 'discounts',
        'features', 'units', 'media'  # إضافات بدون موافقة مع إشعار
    ]
    
    # Approval Status Choices
    APPROVAL_STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('pending', _('قيد المراجعة')),
        ('approved', _('معتمد')),
        ('rejected', _('مرفوض')),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='establishments')
    working_hours = models.JSONField(default=dict, blank=True)
    license_status = models.CharField(max_length=50, default='Pending')
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='establishments')
    pending_updates = models.JSONField(default=dict, blank=True)
    
    UPDATE_STATUS_CHOICES = [
        ('none', 'No Updates'),
        ('pending', 'Pending Review'),
        ('needs_info', 'Needs More Info'),
    ]
    update_status = models.CharField(max_length=20, choices=UPDATE_STATUS_CHOICES, default='none')
    update_note = models.TextField(blank=True)

    # === حقول التراخيص والسجل التجاري ===
    license_number = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name=_('رقم الترخيص')
    )
    license_image = models.ImageField(upload_to='establishments/licenses/', blank=True, null=True)
    commercial_registration = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name=_('رقم السجل التجاري')
    )
    commercial_registry_image = models.ImageField(upload_to='establishments/registries/', blank=True, null=True)
    
    is_open_now = models.BooleanField(default=True, verbose_name=_("مفتوح الآن (يدوي)"))
    open_status_updated_at = models.DateTimeField(auto_now=True)
    open_status_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='status_updates')

    is_verified = models.BooleanField(default=False)
    license_expiry_date = models.DateField(null=True, blank=True)

    # Resuming Establishment fields


    is_suspended = models.BooleanField(default=False, verbose_name=_("معلق"))
    suspension_reason = models.TextField(blank=True, verbose_name=_("سبب التعليق"))
    suspension_end_date = models.DateField(null=True, blank=True, verbose_name=_("تاريخ انتهاء التعليق"))

    # === Approval Workflow Fields ===
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name=_('حالة الاعتماد')
    )
    rejected_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('سبب الرفض')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_establishments',
        verbose_name=_('معتمد بواسطة')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('تاريخ الاعتماد')
    )

    # === Stored Aggregates (updated via signals) ===
    cached_avg_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        verbose_name=_('متوسط التقييم')
    )
    cached_rating_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('عدد التقييمات')
    )
    cached_review_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('عدد المراجعات')
    )

    # Managers
    objects = EstablishmentManager()  # Default manager with optimizations
    public = PublicEstablishmentManager()  # Public-facing queries only


    @property
    def is_badged(self):
        if not self.is_verified:
            return False
        if self.license_expiry_date:
            return self.license_expiry_date >= timezone.localdate()
        return True
    
    @property
    def is_publicly_visible(self):
        """Check if establishment is visible to public."""
        return (
            self.approval_status == 'approved' and
            self.is_active and
            not self.is_suspended
        )
    
    @property
    def approval_status_badge(self):
        """Return CSS class and icon for approval status."""
        badges = {
            'draft': ('secondary', 'fa-pencil-alt', 'مسودة'),
            'pending': ('warning', 'fa-clock', 'قيد المراجعة'),
            'approved': ('success', 'fa-check-circle', 'معتمد'),
            'rejected': ('danger', 'fa-times-circle', 'مرفوض'),
        }
        return badges.get(self.approval_status, ('secondary', 'fa-question', 'غير محدد'))

    def submit_for_approval(self, by_user, ip=None):
        """Submit establishment for office approval."""
        from django.db import transaction
        from management.models import AuditLog
        
        with transaction.atomic():
            old_status = self.approval_status
            self.approval_status = 'pending'
            self.rejected_reason = None
            self.save(update_fields=['approval_status', 'rejected_reason'])
            
            AuditLog.objects.create(
                user=by_user,
                action='SUBMIT_FOR_APPROVAL',
                table_name='places_establishment',
                record_id=str(self.pk),
                old_values={'approval_status': old_status},
                new_values={'approval_status': 'pending'},
                ip_address=ip
            )
        
        return True, _('تم إرسال المنشأة للمراجعة')
    
    def approve(self, by_admin, ip=None):
        """Approve establishment (admin only)."""
        from django.db import transaction
        from management.models import AuditLog
        from interactions.notifications.partner import PartnerNotifications
        
        with transaction.atomic():
            old_status = self.approval_status
            self.approval_status = 'approved'
            self.approved_by = by_admin
            self.approved_at = timezone.now()
            self.rejected_reason = None
            self.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejected_reason'])
            
            AuditLog.objects.create(
                user=by_admin,
                action='APPROVE_ESTABLISHMENT',
                table_name='places_establishment',
                record_id=str(self.pk),
                old_values={'approval_status': old_status},
                new_values={'approval_status': 'approved', 'approved_by': by_admin.pk},
                ip_address=ip
            )
            
            # Notify partner
            PartnerNotifications.notify_establishment_approved(self)
        
        return True, _('تمت الموافقة على المنشأة')
    
    def reject(self, by_admin, reason, ip=None):
        """Reject establishment with reason (admin only)."""
        from django.db import transaction
        from management.models import AuditLog
        from interactions.notifications.partner import PartnerNotifications
        
        with transaction.atomic():
            old_status = self.approval_status
            self.approval_status = 'rejected'
            self.rejected_reason = reason
            self.approved_by = None
            self.approved_at = None
            self.save(update_fields=['approval_status', 'rejected_reason', 'approved_by', 'approved_at'])
            
            AuditLog.objects.create(
                user=by_admin,
                action='REJECT_ESTABLISHMENT',
                table_name='places_establishment',
                record_id=str(self.pk),
                old_values={'approval_status': old_status},
                new_values={'approval_status': 'rejected', 'rejected_reason': reason},
                ip_address=ip
            )
            
            # Notify partner with reason
            PartnerNotifications.notify_establishment_rejected(self, reason)
        
        return True, _('تم رفض المنشأة')

    def __str__(self):
        return f"{self.name} (Establishment)"
    
    def clean(self):
        from ibb_guide.validators import ValidationService
        super().clean()
        ValidationService.validate_establishment_name(self.name, self.owner, directorate=self.directorate, exclude_pk=self.pk)
    
    def save(self, *args, **kwargs):
        # Only validate if not a draft (allow incomplete drafts)
        if self.approval_status != 'draft':
            self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "منشأة"
        verbose_name_plural = "المنشآت"
        indexes = [
            models.Index(fields=['approval_status']),
            models.Index(fields=['owner']),
        ]


class EstablishmentUnit(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='establishments/units/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.establishment.name}"


class EstablishmentWorkingHour(models.Model):
    """Structured working hours for an establishment."""
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name='hours')
    day_of_week = models.IntegerField(
        choices=[
            (0, _('الاثنين')), (1, _('الثلاثاء')), (2, _('الأربعاء')),
            (3, _('الخميس')), (4, _('الجمعة')), (5, _('السبت')), (6, _('الأحد'))
        ],
        verbose_name=_('اليوم')
    )
    open_time = models.TimeField(null=True, blank=True, verbose_name=_('وقت الفتح'))
    close_time = models.TimeField(null=True, blank=True, verbose_name=_('وقت الإغلاق'))
    is_closed_day = models.BooleanField(default=False, verbose_name=_('مغلق طوال اليوم'))

    class Meta:
        ordering = ['day_of_week']
        constraints = [
            models.UniqueConstraint(fields=['establishment', 'day_of_week'], name='unique_working_hour_per_day')
        ]
        verbose_name = _('ساعات العمل')
        verbose_name_plural = _('ساعات العمل')

    def __str__(self):
        return f"{self.establishment.name} - {self.get_day_of_week_display()}"
