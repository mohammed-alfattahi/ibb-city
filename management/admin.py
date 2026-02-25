from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import (
    Request, Advertisement, InvestmentOpportunity, WeatherAlert, 
    AuditLog, GeneralGuideline, RequestStatusLog, ApprovalDecision,
    CulturalLandmark, PublicEmergencyContact, SafetyGuideline
)


# ============ Custom Filters ============
class PendingOnlyFilter(admin.SimpleListFilter):
    title = 'سريع'
    parameter_name = 'quick_filter'

    def lookups(self, request, model_admin):
        return [
            ('pending', '⏳ المعلقة فقط'),
            ('today', '📅 اليوم'),
        ]

    def queryset(self, request, queryset):
        from django.utils import timezone
        if self.value() == 'pending':
            return queryset.filter(status='pending')
        if self.value() == 'today':
            return queryset.filter(created_at__date=timezone.now().date())
        return queryset


class ExpiredAdsFilter(admin.SimpleListFilter):
    title = 'حالة الإعلان'
    parameter_name = 'ad_status'

    def lookups(self, request, model_admin):
        return [
            ('active', '✅ نشط'),
            ('expired', '⏰ منتهي'),
            ('pending', '⏳ قيد المراجعة'),
        ]

    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        if self.value() == 'active':
            return queryset.filter(status='active')
        if self.value() == 'expired':
            # Ads where start_date + duration_days < today
            return queryset.extra(
                where=["start_date + INTERVAL duration_days DAY < %s"],
                params=[timezone.now().date()]
            )
        if self.value() == 'pending':
            return queryset.filter(status='pending')
        return queryset


# ============ Inlines ============
class RequestStatusLogInline(admin.TabularInline):
    model = RequestStatusLog
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'message', 'created_at')
    can_delete = False
    classes = ['collapse']


class ApprovalDecisionInline(admin.TabularInline):
    model = ApprovalDecision
    extra = 0
    readonly_fields = ('decision', 'decided_by', 'reason', 'conditions', 'created_at')
    can_delete = False
    classes = ['collapse']


# ============ Admin Classes ============
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('user', 'request_type', 'status_badge', 'created_at', 'reviewed_by')

    list_filter = (PendingOnlyFilter, 'status', 'request_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 20
    autocomplete_fields = ['user', 'reviewed_by']
    actions = ['approve_requests', 'reject_requests', 'export_as_json_action']

    def export_as_json_action(self, request, queryset):
        from .admin_actions import export_as_json
        return export_as_json(self, request, queryset)
    export_as_json_action.short_description = "📄 تصدير المحدد إلى JSON"

    inlines = [RequestStatusLogInline, ApprovalDecisionInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('user', 'request_type', 'status', 'description'),
            'description': 'البيانات الأساسية للطلب'
        }),
        ('التعديلات المطلوبة', {
            'fields': ('changes', 'original_data'),
            'classes': ('collapse',)
        }),
        ('قرار الإدارة', {
            'fields': ('admin_response', 'admin_notes', 'reviewed_by', 'reviewed_at', 'conditions', 'deadline')
        }),
        ('المرفقات', {
            'fields': ('attachment', 'decision_doc'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'approved': '#28a745', 'rejected': '#dc3545', 'in_review': '#17a2b8'}
        labels = {'pending': 'معلق', 'approved': 'مقبول', 'rejected': 'مرفوض', 'in_review': 'قيد المراجعة'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:11px;">{}</span>',
            color, label
        )

    @admin.action(description='✅ قبول الطلبات المحددة')
    def approve_requests(self, request, queryset):
        count = queryset.update(status='approved', reviewed_by=request.user)
        self.message_user(request, f"تم قبول {count} طلب", messages.SUCCESS)

    @admin.action(description='❌ رفض الطلبات المحددة')
    def reject_requests(self, request, queryset):
        count = queryset.update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f"تم رفض {count} طلب", messages.WARNING)


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('banner_preview', 'title_or_place', 'placement', 'owner', 'start_date', 'duration_days', 'status_badge', 'created_at')

    list_filter = (ExpiredAdsFilter, 'status', 'placement', 'start_date')
    search_fields = ('place__name', 'owner__username', 'title')
    date_hierarchy = 'start_date'
    save_on_top = True
    list_per_page = 20
    autocomplete_fields = ['place', 'owner']
    actions = ['approve_ads', 'reject_ads', 'extend_ads']
    readonly_fields = ['banner_preview_large', 'views', 'clicks']

    fieldsets = (
        ('معلومات الإعلان', {
            'fields': ('title', 'placement', 'place', 'target_url', 'owner', 'description'),
        }),
        ('التواريخ والمدة', {
            'fields': (('start_date', 'duration_days'), 'status'),
        }),
        ('التسعير', {
            'fields': (('price', 'discount_price'),),
            'classes': ('collapse',),
        }),
        ('الوسائط', {
            'fields': ('banner_preview_large', 'banner_image',),
        }),
    )

    @admin.display(description='الصورة')
    def banner_preview(self, obj):
        if obj.banner_image:
            return format_html('<img src="{}" style="width: 80px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.banner_image.url)
        return "-"

    @admin.display(description='معاينة البانر')
    def banner_preview_large(self, obj):
        if obj.banner_image:
            return format_html('<img src="{}" style="width: 100%; max-width: 600px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />', obj.banner_image.url)
        return "لا توجد صورة"

    @admin.display(description='العنوان')
    def title_or_place(self, obj):
        return obj.title or (obj.place.name if obj.place else '—')

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'active': '#28a745', 'pending': '#ffc107', 'rejected': '#dc3545', 'expired': '#6c757d'}
        labels = {'active': 'نشط', 'pending': 'قيد المراجعة', 'rejected': 'مرفوض', 'expired': 'منتهي'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:11px;">{}</span>',
            color, label
        )

    @admin.action(description='✅ تفعيل الإعلانات')
    def approve_ads(self, request, queryset):
        from interactions.notifications.partner import PartnerNotifications
        count = 0
        for ad in queryset:
            if ad.status != 'active':
                ad.status = 'active'
                ad.save(update_fields=['status'])
                # Send notification to partner
                PartnerNotifications.notify_ad_approved(ad)
                count += 1
        self.message_user(request, f"تم تفعيل {count} إعلان وإرسال إشعارات لأصحابها", messages.SUCCESS)

    @admin.action(description='❌ رفض الإعلانات')
    def reject_ads(self, request, queryset):
        from interactions.notifications.partner import PartnerNotifications
        count = 0
        for ad in queryset:
            if ad.status != 'rejected':
                ad.status = 'rejected'
                ad.save(update_fields=['status'])
                # Send notification to partner
                PartnerNotifications.notify_ad_rejected(ad)
                count += 1
        self.message_user(request, f"تم رفض {count} إعلان وإرسال إشعارات لأصحابها", messages.WARNING)

    @admin.action(description='📅 تمديد 7 أيام')
    def extend_ads(self, request, queryset):
        from django.db.models import F
        queryset.update(duration_days=F('duration_days') + 7)
        self.message_user(request, f"تم تمديد {queryset.count()} إعلان بـ 7 أيام", messages.SUCCESS)


@admin.register(InvestmentOpportunity)
class InvestmentOpportunityAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('title', 'created_by', 'cost_display', 'location_short', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'location', 'description')
    autocomplete_fields = ['created_by']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['mark_open', 'mark_closed']

    fieldsets = (
        ('معلومات الفرصة', {
            'fields': ('title', 'description', 'pdf_file'),
        }),
        ('التفاصيل', {
            'fields': ('cost', 'location'),
        }),
        ('الحالة', {
            'fields': (('status', 'created_by'),),
        }),
    )

    @admin.display(description='التكلفة')
    def cost_display(self, obj):
        if obj.cost:
            formatted_cost = "{:,.0f}".format(float(obj.cost))
            return format_html('<span style="color:#28a745; font-weight:600;">{} ر.ي</span>', formatted_cost)
        return '-'

    @admin.display(description='الموقع')
    def location_short(self, obj):
        if obj.location:
            return obj.location[:20] + '...' if len(obj.location) > 20 else obj.location
        return '-'

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'open': '#28a745', 'closed': '#6c757d', 'pending': '#ffc107'}
        icons = {'open': '🟢', 'closed': '🔴', 'pending': '🟡'}
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '')
        label = obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{} {}</span>',
            color, icon, label
        )

    @admin.action(description='🟢 فتح الفرص')
    def mark_open(self, request, queryset):
        count = queryset.update(status='open')
        self.message_user(request, f"تم فتح {count} فرصة", messages.SUCCESS)

    @admin.action(description='🔴 إغلاق الفرص')
    def mark_closed(self, request, queryset):
        count = queryset.update(status='closed')
        self.message_user(request, f"تم إغلاق {count} فرصة", messages.WARNING)


@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity_badge', 'status_indicator', 'expires_at', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('title', 'description')
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['deactivate_alerts']

    fieldsets = (
        ('معلومات التنبيه', {
            'fields': ('title', 'description'),
        }),
        ('الإعدادات', {
            'fields': (('severity', 'expires_at'),),
        }),
    )

    @admin.display(description='الشدة')
    def severity_badge(self, obj):
        colors = {'low': '#28a745', 'medium': '#ffc107', 'high': '#fd7e14', 'critical': '#dc3545'}
        icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
        color = colors.get(obj.severity, '#6c757d')
        icon = icons.get(obj.severity, '⚠️')
        label = obj.get_severity_display() if hasattr(obj, 'get_severity_display') else obj.severity
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{} {}</span>',
            color, icon, label
        )

    @admin.display(description='الحالة')
    def status_indicator(self, obj):
        from django.utils import timezone
        if obj.expires_at and obj.expires_at < timezone.now():
            return format_html('<span style="color:#6c757d;">⏹️ منتهي</span>')
        return format_html('<span style="color:#dc3545; font-weight:600;">⚠️ نشط</span>')

    @admin.action(description='⏹️ إنهاء التنبيهات')
    def deactivate_alerts(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(expires_at=timezone.now())
        self.message_user(request, f"تم إنهاء {count} تنبيه", messages.WARNING)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_badge', 'table_name', 'user', 'timestamp')
    list_filter = ('action', 'table_name')
    search_fields = ('user__username', 'record_id')
    date_hierarchy = 'timestamp'
    save_on_top = True
    list_per_page = 50
    autocomplete_fields = ['user']

    readonly_fields = ('user', 'action', 'table_name', 'record_id', 'old_values', 'new_values', 'timestamp')

    @admin.display(description='الإجراء')
    def action_badge(self, obj):
        colors = {'CREATE': '#28a745', 'UPDATE': '#17a2b8', 'DELETE': '#dc3545'}
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:12px; font-size:11px;">{}</span>',
            color, obj.action
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(GeneralGuideline)
class GeneralGuidelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'category_badge', 'content_preview', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content')
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'

    fieldsets = (
        ('محتوى الإرشاد', {
            'fields': ('title', 'content'),
        }),
        ('التصنيف', {
            'fields': ('category',),
        }),
    )

    @admin.display(description='التصنيف')
    def category_badge(self, obj):
        colors = {'general': '#6c757d', 'safety': '#dc3545', 'transport': '#17a2b8', 'culture': '#6f42c1'}
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.category
        )

    @admin.display(description='المحتوى')
    def content_preview(self, obj):
        if obj.content:
            return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
        return '-'



from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'partner', 'amount', 'total_amount', 'paid_badge', 'issue_date')
    list_filter = ('is_paid', 'issue_date')
    search_fields = ('invoice_number', 'partner__username', 'advertisement__title')
    date_hierarchy = 'issue_date'
    save_on_top = True
    list_per_page = 20
    autocomplete_fields = ['partner', 'advertisement']
    actions = ['mark_paid', 'mark_unpaid']

    readonly_fields = ('invoice_number', 'issue_date')

    @admin.display(description='الدفع')
    def paid_badge(self, obj):
        if obj.is_paid:
            return format_html('<span style="color:#28a745;">✓ مدفوع</span>')
        return format_html('<span style="color:#dc3545;">✗ غير مدفوع</span>')

    @admin.action(description='✅ تحديد كمدفوع')
    def mark_paid(self, request, queryset):
        queryset.update(is_paid=True)
        self.message_user(request, f"تم تحديد {queryset.count()} فاتورة كمدفوعة", messages.SUCCESS)

    @admin.action(description='❌ تحديد كغير مدفوع')
    def mark_unpaid(self, request, queryset):
        queryset.update(is_paid=False)
        self.message_user(request, f"تم تحديد {queryset.count()} فاتورة كغير مدفوعة", messages.WARNING)


# Import moderation admin
from . import admin_moderation
from . import admin_content
from . import admin_ui  # UI/CMS models (SiteSetting, Menu, HomePageSection, etc.)


