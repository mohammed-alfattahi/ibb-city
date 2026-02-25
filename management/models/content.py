from django.db import models
from django.utils.translation import gettext_lazy as _

# ============================================
# Phase 1: Culture & Emergency (Retained)
# ============================================

class CulturalLandmark(models.Model):
    title = models.CharField(_("العنوان"), max_length=200)
    description = models.TextField(_("الوصف"))
    icon = models.CharField(_("أيقونة FontAwesome"), max_length=50, default="fas fa-mosque", help_text="مثال: fas fa-mosque")
    color = models.CharField(_("لون الأيقونة"), max_length=50, default="primary", choices=[
        ('primary', 'Primary (Blue)'),
        ('secondary', 'Secondary (Grey)'),
        ('success', 'Success (Green)'),
        ('danger', 'Danger (Red)'),
        ('warning', 'Warning (Yellow)'),
        ('info', 'Info (Cyan)'),
    ])
    image1 = models.ImageField(_("صورة 1"), upload_to='culture/', blank=True, null=True)
    image2 = models.ImageField(_("صورة 2"), upload_to='culture/', blank=True, null=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("مَعلم ثقافي")
        verbose_name_plural = _("المعالم الثقافية")
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

class PublicEmergencyContact(models.Model):
    COLOR_CHOICES = [
        ('danger', _('أحمر (خطر)')),
        ('warning', _('أصفر (تحذير)')),
        ('success', _('أخضر (نجاح)')),
        ('primary', _('أزرق (أساسي)')),
        ('info', _('سماوي (معلومات)')),
        ('dark', _('داكن')),
    ]

    title = models.CharField(_("الجهة"), max_length=100)
    number = models.CharField(_("رقم الهاتف"), max_length=20)
    description = models.CharField(_("الوصف المختصر"), max_length=200, blank=True)
    icon = models.CharField(_("أيقونة FontAwesome"), max_length=50, help_text="مثال: fas fa-ambulance")
    color = models.CharField(_("اللون"), max_length=20, choices=COLOR_CHOICES, default='danger')
    is_primary_card = models.BooleanField(_("عرض كبطاقة كبيرة"), default=False, help_text="تظهر في أعلى الصفحة كبطاقة كبيرة (مثل: الشرطة، الإسعاف)")
    is_hospital = models.BooleanField(_("مستشفى؟"), default=False, help_text="تظهر في قائمة المستشفيات")
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("رقم طوارئ عام")
        verbose_name_plural = _("أرقام الطوارئ العامة")
        ordering = ['order', 'title']

    def __str__(self):
        if self.is_hospital:
            return f"{self.title} (مستشفى)"
        return f"{self.title} ({self.number})"

class SafetyGuideline(models.Model):
    COLOR_CHOICES = [
         ('danger', _('أحمر (خطر)')),
        ('warning', _('أصفر (تحذير)')),
        ('success', _('أخضر (نجاح)')),
        ('primary', _('أزرق (أساسي)')),
    ]
    title = models.CharField(_("العنوان"), max_length=200)
    description = models.TextField(_("التفاصيل"))
    icon = models.CharField(_("أيقونة FontAwesome"), max_length=50)
    color = models.CharField(_("اللون"), max_length=20, choices=COLOR_CHOICES, default='primary')
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("إرشادات السلامة")
        verbose_name_plural = _("إرشادات السلامة")
        ordering = ['order']

    def __str__(self):
        return self.title

# ============================================
# Phase 2: Base Architecture (Core)
# ============================================

class SiteSetting(models.Model):
    site_name = models.CharField(_("اسم الموقع"), max_length=200, default="دليل إب السياحي")
    logo = models.ImageField(_("الشعار"), upload_to="site/", default="site/default_logo.png")
    primary_color = models.CharField(_("اللون الأساسي"), max_length=20, default="#0d6efd")
    
    # Footer Content
    footer_text = models.TextField(_("نص الفوتر"), blank=True)
    copyright_text = models.CharField(_("نص الحقوق"), max_length=200, blank=True)
    
    # Contact Info
    contact_email = models.EmailField(_("البريد الإلكتروني للتواصل"), blank=True)
    contact_phone = models.CharField(_("رقم الهاتف للتواصل"), max_length=50, blank=True)
    address = models.CharField(_("العنوان"), max_length=255, blank=True)
    
    # Meta / SEO
    meta_description = models.TextField(_("وصف الموقع (SEO)"), blank=True)
    keywords = models.CharField(_("الكلمات المفتاحية"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("إعدادات الموقع")
        verbose_name_plural = _("إعدادات الموقع")

    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSetting.objects.exists():
            return
        return super(SiteSetting, self).save(*args, **kwargs)

class SocialLink(models.Model):
    label = models.CharField(_("الاسم"), max_length=50, help_text="مثال: Facebook, Twitter")
    url = models.URLField(_("الرابط"))
    icon = models.CharField(_("أيقونة FontAwesome"), max_length=50, blank=True, help_text="مثال: fab fa-facebook")
    order = models.IntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("رابط تواصل اجتماعي")
        verbose_name_plural = _("روابط التواصل الاجتماعي")
        ordering = ['order']

    def __str__(self):
        return self.label

class Menu(models.Model):
    LOCATION_CHOICES = [
        ("header", _("القائمة العلوية (Header)")),
        ("footer", _("القائمة السفلية (Footer)")),
        ("sidebar", _("القائمة الجانبية (Sidebar)")),
    ]
    
    title = models.CharField(_("العنوان"), max_length=100)
    url = models.CharField(_("الرابط"), max_length=200)
    location = models.CharField(_("المكان"), max_length=20, choices=LOCATION_CHOICES)
    order = models.IntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name=_("العنصر الأب"))
    
    # Role-based visibility
    visible_for_guests = models.BooleanField(_("ظاهر للزوار"), default=True)
    visible_for_users = models.BooleanField(_("ظاهر للمستخدمين المسجلين"), default=True)
    visible_for_admins = models.BooleanField(_("ظاهر للمسؤولين"), default=True)

    class Meta:
        verbose_name = _("قائمة")
        verbose_name_plural = _("القوائم")
        ordering = ['location', 'order']
        indexes = [
            models.Index(fields=['location', 'is_active', 'order']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_location_display()})"

class SidebarWidget(models.Model):
    WIDGET_TYPES = [
        ("text", _("نص (Text)")),
        ("links", _("روابط (Links)")),
        ("stats", _("إحصائيات (Statistics)")),
        ("cta", _("دعوة لاتخاذ إجراء (CTA)")),
        ("custom_html", _("HTML مخصص")),
    ]

    title = models.CharField(_("العنوان"), max_length=200)
    widget_type = models.CharField(_("نوع الوجت"), max_length=20, choices=WIDGET_TYPES, default="text")
    content = models.TextField(_("المحتوى"), blank=True, help_text=_("للنص، HTML، أو رابط زر CTA"))
    
    # Control
    order = models.IntegerField(_("الترتيب"), default=0)
    is_visible = models.BooleanField(_("ظاهر"), default=True)

    # Customization
    pages = models.JSONField(_("الصفحات"), default=list, blank=True, help_text='["home", "places"] list of url names')
    roles = models.JSONField(_("الأدوار"), default=list, blank=True, help_text='["guest", "user", "admin"]')

    class Meta:
        verbose_name = _("وجت جانبي")
        verbose_name_plural = _("وجتات الشريط الجانبي")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"

class SidebarLink(models.Model):
    widget = models.ForeignKey(SidebarWidget, related_name="links", on_delete=models.CASCADE, verbose_name=_("الويدجت"))
    title = models.CharField(_("العنوان"), max_length=150)
    url = models.CharField(_("الرابط"), max_length=300)
    order = models.IntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)
    
    class Meta:
        verbose_name = _("رابط جانبي")
        verbose_name_plural = _("روابط جانبية")
        ordering = ['order']
        
    def __str__(self):
        return self.title


# ============================================
# Phase 3: Dynamic Pages (Home, etc)
# ============================================

class HomePageSection(models.Model):
    SECTION_TYPES = [
        ('hero', _('Hero Section - العرض الرئيسي')),
        ('featured_grid', _('Featured Grid - شبكة المميزات')),
        ('quick_access', _('Quick Access - الوصول السريع')),
        ('partners', _('Partners Slider - شريط الشركاء')),
        ('custom_html', _('Custom HTML - محتوى مخصص')),
    ]

    title = models.CharField(_("عنوان القسم"), max_length=200, help_text=_("للعرض في لوحة التحكم"))
    section_type = models.CharField(_("نوع القسم"), max_length=50, choices=SECTION_TYPES, default='custom_html')
    content = models.TextField(_("المحتوى (HTML)"), blank=True, help_text=_("يستخدم فقط مع نوع Custom HTML"))
    
    is_visible = models.BooleanField(_("ظاهر"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("قسم الصفحة الرئيسية")
        verbose_name_plural = _("أقسام الصفحة الرئيسية")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_section_type_display()})"

class HeroSlide(models.Model):
    title = models.CharField(_("العنوان الرئيسي"), max_length=200)
    subtitle = models.CharField(_("العنوان الفرعي"), max_length=200, blank=True)
    image = models.ImageField(_("صورة الخلفية"), upload_to='hero/')
    button_text = models.CharField(_("نص الزر"), max_length=50, blank=True)
    button_link = models.CharField(_("رابط الزر"), max_length=200, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("شريحة العرض (Hero Slide)")
        verbose_name_plural = _("شرائح العرض الرئيسية")
        ordering = ['order']

    def __str__(self):
        return self.title

class TeamMember(models.Model):
    name = models.CharField(_("الاسم"), max_length=100)
    role = models.CharField(_("المسمى الوظيفي"), max_length=100)
    bio = models.TextField(_("نبذة مختصرة"), blank=True)
    image = models.ImageField(_("الصورة الشخصية"), upload_to='team/')
    
    # Social Links
    twitter = models.URLField(_("تويتر"), blank=True)
    linkedin = models.URLField(_("لينكد إن"), blank=True)
    
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("عضو فريق")
        verbose_name_plural = _("فريق العمل")
        ordering = ['order']

    def __str__(self):
        return self.name

class TransportCompany(models.Model):
    name = models.CharField(_("اسم الشركة"), max_length=100)
    logo = models.ImageField(_("الشعار"), upload_to='transport/', blank=True, null=True)
    phone = models.CharField(_("رقم الحجز"), max_length=20)
    whatsapp = models.CharField(_("واتساب"), max_length=20, blank=True)
    description = models.TextField(_("نبذة عن الشركة"), blank=True)
    destinations = models.CharField(_("الوجهات الرئيسية"), max_length=200, help_text="مثال: صنعاء، عدن، الحديدة")
    is_active = models.BooleanField(_("نشط"), default=True)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("شركة نقل")
        verbose_name_plural = _("شركات النقل")
        ordering = ['order']

    def __str__(self):
        return self.name

class ListingConfiguration(models.Model):
    PAGE_CHOICES = [
        ('place_list', _('دليل الأماكن (Place List)')),
        ('nature_list', _('الطبيعة (Nature)')),
        ('investment_list', _('الاستثمار (Investment)')),
        ('events_list', _('المناسبات (Events)')),
        ('place_detail', _('تفاصيل المكان (Place Detail)')),
    ]

    page_name = models.CharField(_("الصفحة"), max_length=50, choices=PAGE_CHOICES, unique=True)
    
    # Hero Section
    hero_title = models.CharField(_("عنوان البانر"), max_length=200, default="استكشف الأماكن", help_text="يستخدم كعنوان افتراضي إذا لم يكن للمكان صورة")
    hero_subtitle = models.CharField(_("وصف البانر"), max_length=300, blank=True)
    hero_image = models.ImageField(_("صورة البانر"), upload_to='pages/hero/', blank=True, null=True, help_text="صورة افتراضية للمكان")
    
    # Filter Configuration (Lists)
    show_search = models.BooleanField(_("إظهار البحث"), default=True)
    show_category_filter = models.BooleanField(_("إظهار فلتر التصنيف"), default=True)
    show_rating_filter = models.BooleanField(_("إظهار فلتر التقييم"), default=True)
    show_price_filter = models.BooleanField(_("إظهار فلتر الأسعار"), default=False)
    show_district_filter = models.BooleanField(_("إظهار فلتر المديرية"), default=False)
    
    # Detail Configuration (Detail Pages)
    show_gallery = models.BooleanField(_("إظهار المعرض"), default=True)
    show_reviews = models.BooleanField(_("إظهار التقييمات"), default=True)
    show_similar_places = models.BooleanField(_("إظهار أماكن مشابهة"), default=True)
    show_sidebar = models.BooleanField(_("إظهار الشريط الجانبي"), default=True)
    show_weather_widget = models.BooleanField(_("إظهار حالة الطقس"), default=True)
    
    # Display Configuration
    items_per_page = models.IntegerField(_("عدد العناصر في الصفحة"), default=9)
    default_view_style = models.CharField(_("نمط العرض الافتراضي"), max_length=20, choices=[('grid', 'شبكة'), ('list', 'قائمة')], default='grid')

    def __str__(self):
        return self.get_page_name_display()

    class Meta:
        verbose_name = _("إعدادات صفحة القوائم")
        verbose_name_plural = _("إعدادات صفحات القوائم")


class PlaceDetailBlock(models.Model):
    BLOCK_TYPES = [
        ("hero", _("Hero Section - العرض الرئيسي")),
        ("gallery", _("Image Gallery - معرض الصور")),
        ("overview", _("Overview - نظرة عامة")),
        ("services", _("Services/Units - الوحدات والخدمات")),
        ("map", _("Map - الخريطة")),
        ("contact", _("Contact Info - معلومات التواصل")),
        ("reviews", _("Reviews - التقييمات")),
        ("ad_banner", _("Ad Banner - إعلان عرضي")),
    ]

    block_type = models.CharField(_("نوع القسم"), max_length=30, choices=BLOCK_TYPES)
    title = models.CharField(_("عنوان القسم"), max_length=200, blank=True)
    order = models.IntegerField(_("الترتيب"), default=0)
    is_visible = models.BooleanField(_("ظاهر"), default=True)
    
    # Optional customization
    custom_class = models.CharField(_("CSS Class مخصص"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("قسم تفاصيل المكان")
        verbose_name_plural = _("أقسام تفاصيل المكان")
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_block_type_display()})"


class FeatureToggle(models.Model):
    key = models.CharField(max_length=100, unique=True, help_text="enable_reviews, show_weather, etc.")
    label = models.CharField(_("اسم الميزة"), max_length=200, default="")
    is_enabled = models.BooleanField(_("مفعل"), default=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("ميزة (Feature Toggle)")
        verbose_name_plural = _("ميزات النظام")
        indexes = [
            models.Index(fields=['key']),
        ]

    def __str__(self):
        return self.key


class CommunitySetting(models.Model):
    auto_approve_posts = models.BooleanField(_("موافقة تلقائية على المنشورات"), default=False)
    auto_approve_comments = models.BooleanField(_("موافقة تلقائية على التعليقات"), default=False)
    max_post_length = models.IntegerField(_("الحد الأقصى لطول المنشور"), default=500)
    max_comment_length = models.IntegerField(_("الحد الأقصى لطول التعليق"), default=300)
    
    class Meta:
        verbose_name = _("إعدادات المجتمع")
        verbose_name_plural = _("إعدادات المجتمع")

    def __str__(self):
        return "إعدادات المجتمع"

    def save(self, *args, **kwargs):
        if not self.pk and CommunitySetting.objects.exists():
            return
        return super(CommunitySetting, self).save(*args, **kwargs)


class NotificationSetting(models.Model):
    retention_days = models.IntegerField(_("مدة الاحتفاظ (أيام)"), default=30)
    allow_mark_all = models.BooleanField(_("السماح بتحديد الكل كمقروء"), default=True)
    allow_delete = models.BooleanField(_("السماح بحذف الإشعارات"), default=True)

    class Meta:
        verbose_name = _("إعدادات الإشعارات")
        verbose_name_plural = _("إعدادات الإشعارات")

    def __str__(self):
        return "إعدادات الإشعارات"
    
    def save(self, *args, **kwargs):
        if not self.pk and NotificationSetting.objects.exists():
            return
        return super(NotificationSetting, self).save(*args, **kwargs)


class NotificationType(models.Model):
    key = models.CharField(max_length=50, unique=True, help_text="comment, like, system, etc.")
    label = models.CharField(_("اسم النوع"), max_length=100)
    is_enabled = models.BooleanField(_("مفعل"), default=True)
    order = models.IntegerField(_("الترتيب"), default=0)

    class Meta:
        verbose_name = _("نوع إشعار")
        verbose_name_plural = _("أنواع الإشعارات")
        ordering = ['order']

    def __str__(self):
        return self.label


class WizardStep(models.Model):
    key = models.CharField(max_length=50, unique=True)  # basic, location, services, media, review
    title = models.CharField(_("عنوان الخطوة"), max_length=200)
    order = models.IntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("خطوة المعالج")
        verbose_name_plural = _("خطوات المعالج")
        ordering = ['order']

    def __str__(self):
        return self.title


class WizardField(models.Model):
    step = models.ForeignKey(WizardStep, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    label = models.CharField(_("تسمية الحقل"), max_length=200)
    is_required_on_submit = models.BooleanField(_("إلزامي عند الإرسال"), default=False)
    is_visible = models.BooleanField(_("ظاهر"), default=True)

    class Meta:
        verbose_name = _("حقل المعالج")
        verbose_name_plural = _("حقول المعالج")

    def __str__(self):
        return self.field_name

