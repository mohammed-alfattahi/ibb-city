from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel
from ibb_guide.core_utils import get_client_ip
# الادوار و الصلاخيات
class Role(models.Model):
    # الادوار
    name = models.CharField(max_length=50, unique=True)

    # وصف ال
    description = models.TextField(blank=True)
    # الصلاحيات
    permissions = models.ManyToManyField('auth.Permission', blank=True, help_text="Specific permissions for this role")

    def __str__(self):
        # عرض اسم الدور
        return self.name
# المناصب الموظيفيه
class JobPosition(models.Model):
    # المسمى الوظيفي
    title = models.CharField(max_length=100)
    # القسم
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        # عرض المسمى الوظيفي والقسم
        return f"{self.title} ({self.department})"
# الاهتمامات
class Interest(models.Model):
    # الاهتمامات
    name = models.CharField(max_length=50, unique=True, verbose_name=_('اسم الاهتمام'))
    # الايقونة
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome class (e.g., fa-tree)", verbose_name=_('الأيقونة'))

    def __str__(self):
        # عرض اسم الاهتمام
        return self.name


class User(AbstractUser, TimeStampedModel):
    """نموذج المستخدم المخصص مع حالة الحساب"""
    
    # حالات الحساب
    ACCOUNT_STATUS_CHOICES = [
        ('active', _('نشط')),
        ('pending', _('قيد المراجعة')),
        ('rejected', _('مرفوض')),
        ('suspended', _('موقوف')),
    ]
    # الدور
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    # الاسم الكامل
    full_name = models.CharField(max_length=100, blank=True)
    # رقم الهاتف
    phone_number = models.CharField(max_length=20, blank=True)
    # صورة الملف الشخصي
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    # صوره الخلفيه الواجهه
    cover_image = models.ImageField(upload_to='profile_covers/', blank=True, null=True, verbose_name=_('صورة غلاف'))
    # النبذه التعريفيه
    bio = models.TextField(max_length=500, blank=True, verbose_name=_('نبذة تعريفية'))
    # رمز التحقق
    fcm_token = models.TextField(blank=True, null=True)
    # المناصب الموظيفيه
    job_positions = models.ManyToManyField(JobPosition, blank=True)
    # الاهتمامات
    interests = models.ManyToManyField(Interest, blank=True, verbose_name=_('الاهتمامات'))
    # الحالة
    account_status = models.CharField(
        max_length=20, 
        choices=ACCOUNT_STATUS_CHOICES, 
        default='active',
        verbose_name=_('حالة الحساب')
    )
    # سبب الإيقاف
    suspension_reason = models.TextField(blank=True, verbose_name=_('سبب الإيقاف'))
    
    # Email Verification Fields
    is_email_verified = models.BooleanField(default=False, verbose_name=_('تم التحقق من البريد'))

    email_verification_token = models.CharField(max_length=64, blank=True, verbose_name=_('رمز التحقق'))
    # تاريخ إرسال التحقق
    email_verification_sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ إرسال التحقق'))

    def __str__(self):
        return self.username
    
    def is_account_active(self):
        """التحقق من أن الحساب نشط"""
        return self.account_status == 'active'
    
    def can_login(self):
        """التحقق من إمكانية تسجيل الدخول"""
        return self.account_status in ['active', 'pending']
    
    def get_status_display_ar(self):
        """عرض حالة الحساب بالعربية"""
        status_map = {
            'active': 'نشط',
            'pending': 'قيد المراجعة',
            'rejected': 'مرفوض',
            'suspended': 'موقوف',
        }
        return status_map.get(self.account_status, self.account_status)


class PartnerProfile(TimeStampedModel):
    """ملف الشريك التجاري"""
    
    # حالات طلب الشراكة
    PARTNER_STATUS_CHOICES = [
        ('pending', _('قيد المراجعة')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
        ('needs_info', _('بحاجة إلى معلومات إضافية')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='partner_profile')
    # اسم المنظمة/النشاط
    organization_name = models.CharField(max_length=200, blank=True, verbose_name=_('اسم المنظمة/النشاط'))
    # رقم التسجيل التجاري
    commercial_reg_no = models.CharField(max_length=50, blank=True)
    # صورة البطاقة الشخصية
    id_card_image = models.ImageField(upload_to='partners/id_cards/', blank=True, null=True, verbose_name=_('صورة البطاقة الشخصية'))
    # ملف السجل التجاري
    commercial_registry_file = models.FileField(upload_to='partners/registries/', blank=True, null=True, verbose_name=_('السجل التجاري'))
    # الموافقة
    is_approved = models.BooleanField(default=False)
    # حالة الطلب
    status = models.CharField(
        max_length=20,
        choices=PARTNER_STATUS_CHOICES,
        default='pending',
        verbose_name=_('حالة الطلب')
    )
    # سبب الرفض
    rejection_reason = models.TextField(blank=True, verbose_name=_('سبب الرفض'))
    # رسالة طلب المعلومات
    info_request_message = models.TextField(blank=True, verbose_name=_('رسالة طلب المعلومات'))
    # تاريخ تقديم الطلب
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ تقديم الطلب'))
    # تاريخ المراجعة
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ المراجعة'))
    # المراجع
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_partners',
        verbose_name=_('تمت المراجعة بواسطة')
    )
    
    # Rate Limiting لطلبات الترقية
    upgrade_request_count = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('عدد محاولات طلب الترقية')
    )
    # تاريخ آخر طلب ترقية
    last_upgrade_request = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_('آخر طلب ترقية')
    )
    
    # تاريخ انتهاء الاشتراك
    subscription_end = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_('تاريخ انتهاء الاشتراك')
    )

    def __str__(self):
        return f"Partner: {self.user.username}"
    # صف عمل الدالة
    def save(self, *args, **kwargs):
        # 1. Sync is_approved <-> status (Bidirectional)
        if self.is_approved and self.status != 'approved':
            self.status = 'approved'
        elif not self.is_approved and self.status == 'approved':
             # If manually unapproved, move to rejected or pending? 
             # Let's say rejected if it was approved before.
            self.status = 'rejected'
            
        # Ensure consistency
        if self.status == 'approved':
            self.is_approved = True
        else:
            self.is_approved = False
            
        super().save(*args, **kwargs)
        
        # 2. Update User Role & Permissions based on Approval
        try:
            if self.is_approved:
                # Upgrade to Partner
                partner_role, _ = Role.objects.get_or_create(name='partner')
                if self.user.role != partner_role or not self.user.is_staff:
                    self.user.role = partner_role
                    self.user.is_staff = True
                    self.user.save(update_fields=['role', 'is_staff'])
            else:
                # Downgrade to User (if they were partner)
                # Only if they currently have partner role (don't demote admins)
                if self.user.role and self.user.role.name == 'partner':
                    user_role, _ = Role.objects.get_or_create(name='user')
                    self.user.role = user_role
                    self.user.is_staff = False
                    self.user.save(update_fields=['role', 'is_staff'])
        except Exception:
            # Handle cases where Role table might be empty during migration
            pass
    
    def get_status_display_ar(self):
        """عرض حالة الطلب بالعربية"""
        status_map = {
            'pending': 'قيد المراجعة',
            'approved': 'موافق عليه',
            'rejected': 'مرفوض',
            'needs_info': 'بحاجة إلى معلومات إضافية',
        }
        return status_map.get(self.status, self.status)
    
    def can_access_dashboard(self):
        """التحقق من إمكانية الوصول للوحة التحكم"""
        return self.status == 'approved'
    
    def can_request_upgrade(self):
        """التحقق من إمكانية طلب ترقية جديدة (Rate Limiting)"""
        from django.utils import timezone
        from datetime import timedelta
        
        # الحد: 3 طلبات كحد أقصى خلال 24 ساعة
        MAX_REQUESTS = 3
        COOLDOWN_HOURS = 24
        
        if self.upgrade_request_count >= MAX_REQUESTS:
            if self.last_upgrade_request:
                cooldown_end = self.last_upgrade_request + timedelta(hours=COOLDOWN_HOURS)
                if timezone.now() < cooldown_end:
                    return False, cooldown_end
                # إعادة تعيين العداد بعد انتهاء فترة الانتظار
                self.upgrade_request_count = 0
                self.save(update_fields=['upgrade_request_count'])
        return True, None
    
    def record_upgrade_request(self):
        """تسجيل محاولة طلب ترقية"""
        from django.utils import timezone
        self.upgrade_request_count += 1
        self.last_upgrade_request = timezone.now()
        self.save(update_fields=['upgrade_request_count', 'last_upgrade_request'])
    
    @property
    def is_subscription_active(self):
        """التحقق من صلاحية الاشتراك"""
        from django.utils import timezone
        if not self.subscription_end:
            return True  # لا يوجد حد
        return self.subscription_end >= timezone.now().date()



class UserRegistrationLog(models.Model):
    """
    سجل تسجيل المستخدمين - Audit Log
    يسجل معلومات عملية التسجيل لأغراض الأمان والتحليل
    """
    
    STATUS_CHOICES = [
        ('success', _('ناجح')),
        ('failed', _('فاشل')),
        ('pending', _('معلق')),
    ]
    
    REGISTRATION_TYPE_CHOICES = [
        ('tourist', _('سائح')),
        ('partner', _('شريك')),
        ('api', _('تسجيل API')),  # Fix Gap 2: API registration type
    ]
    
    # العلاقة مع المستخدم (اختيارية لأن التسجيل ربما يفشل)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registration_logs',
        verbose_name=_('المستخدم')
    )
    
    # معلومات التسجيل
    email = models.EmailField(verbose_name=_('البريد الإلكتروني'))
    # اسم المستخدم
    username = models.CharField(max_length=150, verbose_name=_('اسم المستخدم'))
    # نوع التسجيل
    registration_type = models.CharField(
        max_length=20, 
        choices=REGISTRATION_TYPE_CHOICES,
        default='tourist',
        verbose_name=_('نوع التسجيل')
    
    )
    # الحالة
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('الحالة')
    )
    # معلومات الجلسة والأمان
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('عنوان IP'))
    # متصفح المستخدم
    user_agent = models.TextField(blank=True, verbose_name=_('متصفح المستخدم'))
    # الصفحة المرجعية
    referer = models.URLField(max_length=500, blank=True, verbose_name=_('الصفحة المرجعية'))
    
    # معلومات إضافية
    failure_reason = models.TextField(blank=True, verbose_name=_('سبب الفشل'))
    # البيانات الإضافية
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('بيانات إضافية'))
    
    # الوقت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ التسجيل'))
    
    class Meta:
        # اسم الجدول
        verbose_name = _('سجل تسجيل')
        # اسم الجدول بالعربية
        verbose_name_plural = _('سجلات التسجيل')
        # الترتيب
        ordering = ['-created_at']
        # الفهرس
        indexes = [
            
            models.Index(fields=['-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        # عرض معلومات التسجيل
        return f"{self.email} - {self.get_status_display()} - {self.created_at}"
    
    @classmethod
    # تسجيل عملية تسجيل جديدة
    def log_registration(cls, request, user=None, email='', username='', 
                         registration_type='tourist', status='success', failure_reason=''):
        """
        تسجيل عملية تسجيل جديدة
        
        Args:
            request: HTTP request object
            user: User instance (if successful)
            email: Email used for registration
            username: Username used for registration
            registration_type: 'tourist' or 'partner'
            status: 'success', 'failed', or 'pending'
            failure_reason: Reason for failure (if any)
        """
        # استخراج معلومات الطلب
        ip_address = get_client_ip(request)
        # متصفح المستخدم
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        # الصفحة المرجعية
        referer = request.META.get('HTTP_REFERER', '')[:500]
        
        # إنشاء السجل
        return cls.objects.create(
            user=user,
            email=email,
            username=username,
            registration_type=registration_type,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            failure_reason=failure_reason,
            metadata={
                'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                'content_type': request.content_type,
            }
        )
    
    # تم نقل _get_client_ip إلى ibb_guide.core_utils.get_client_ip


class UserLoginLog(models.Model):
    """
    سجل تسجيل الدخول - Login Audit Log
    يسجل جميع محاولات تسجيل الدخول لأغراض الأمان والتحليل
    """
    
    STATUS_CHOICES = [
        ('success', _('ناجح')),
        ('failed', _('فاشل')),
        ('blocked', _('محظور')),
    ]    
    # الحالة
    FAILURE_REASON_CHOICES = [
        ('invalid_credentials', _('بيانات اعتماد غير صحيحة')),
        ('account_suspended', _('حساب موقوف')),
        ('account_rejected', _('حساب مرفوض')),
        ('email_not_verified', _('بريد غير مؤكد')),
        ('account_locked', _('حساب مقفل مؤقتاً')),
        ('rate_limited', _('تجاوز الحد المسموح')),
        ('other', _('سبب آخر')),
    ]
    
    # العلاقة مع المستخدم (اختيارية لأن المحاولات الفاشلة قد لا تكون مرتبطة بمستخدم)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='login_logs',
        verbose_name=_('المستخدم')
    )
    
    # معلومات المحاولة
    username_or_email = models.CharField(max_length=255, verbose_name=_('اسم المستخدم أو البريد'))
    # الحالة
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        verbose_name=_('الحالة')
    )
    # السبب
    failure_reason = models.CharField(
        max_length=50, 
        choices=FAILURE_REASON_CHOICES,
        blank=True,
        verbose_name=_('سبب الفشل')
    )
    # التفاصيل
    failure_details = models.TextField(blank=True, verbose_name=_('تفاصيل الفشل'))
    
    # معلومات الجلسة والأمان
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('عنوان IP'))
    # متصفح المستخدم
    user_agent = models.TextField(blank=True, verbose_name=_('متصفح المستخدم'))
    
    # معلومات إضافية
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('بيانات إضافية'))
    
    # الوقت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('وقت المحاولة'))
    
    class Meta:
        # اسم الجدول
        verbose_name = _('سجل دخول')
        # اسم الجدول بالعربية
        verbose_name_plural = _('سجلات الدخول')
        # الترتيب
        ordering = ['-created_at']
        # الفهرس
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['username_or_email']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.username_or_email} - {self.get_status_display()} - {self.created_at}"
    
    @classmethod
    def log_attempt(cls, request, user=None, username_or_email='', 
                    status='success', failure_reason='', failure_details=''):
        """
        تسجيل محاولة تسجيل دخول
        
        Args:
            request: HTTP request object
            user: User instance (if found)
            username_or_email: The login identifier used
            status: 'success', 'failed', or 'blocked'
            failure_reason: Reason code for failure
            failure_details: Additional details about failure
        """
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(
            user=user,
            username_or_email=username_or_email,
            status=status,
            failure_reason=failure_reason,
            failure_details=failure_details,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
                'referer': request.META.get('HTTP_REFERER', '')[:500] if request.META.get('HTTP_REFERER') else '',
            }
        )
    
    # تم نقل _get_client_ip إلى ibb_guide.core_utils.get_client_ip
    
    @classmethod
    def get_recent_failures(cls, ip_address=None, username=None, minutes=30):
        """
        الحصول على المحاولات الفاشلة الأخيرة
        مفيد لتحليل الهجمات المحتملة
        """
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(minutes=minutes)
        queryset = cls.objects.filter(
            status='failed',
            created_at__gte=since
        )
        
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        if username:
            queryset = queryset.filter(username_or_email=username)
        
        return queryset
