from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django import forms
from django.db import models
from .models import User, Role, JobPosition, PartnerProfile, UserRegistrationLog, UserLoginLog, Interest
from management.admin_actions import export_as_csv
from management.forms import CsvImportForm
from management.importers import CsvImporter


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'users_count')
    search_fields = ('name',)
    save_on_top = True
    list_per_page = 20

    @admin.display(description='عدد المستخدمين')
    def users_count(self, obj):
        count = obj.user_set.count()
        return format_html(
            '<span style="background:#17a2b8; color:white; padding:3px 10px; border-radius:12px;">{}</span>',
            count
        )


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'users_count')
    list_filter = ('department',)
    search_fields = ('title', 'department')
    save_on_top = True
    list_per_page = 20

    @admin.display(description='عدد الموظفين')
    def users_count(self, obj):
        count = obj.user_set.count()
        return format_html('<span style="color:#28a745; font-weight:600;">{}</span>', count)


class PartnerProfileInline(admin.StackedInline):
    model = PartnerProfile
    can_delete = False
    verbose_name_plural = 'ملف الشريك'
    fk_name = 'user'
    classes = ['collapse']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/import_change_list.html"
    change_form_template = "admin/tabbed_change_form.html"
    list_display = ('username', 'full_name', 'role_badge', 'is_active', 'last_login_fmt', 'quick_actions')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    list_editable = ('is_active',)
    formfield_overrides = {
        models.BooleanField: {'widget': forms.CheckboxInput(attrs={'class': 'toggle-active'})},
    }
    search_fields = ('username', 'email', 'full_name', 'phone_number')
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'date_joined'
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff', export_as_csv]

    fieldsets = (
        ('بيانات الدخول', {
            'fields': ('username', 'password'),
        }),
        ('المعلومات الشخصية', {
            'fields': ('full_name', 'email', 'phone_number', 'profile_image'),
        }),
        ('الصلاحيات', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('الدور والوظائف', {
            'fields': ('role', 'job_positions'),
        }),
        ('تواريخ مهمة', {
            'fields': ('last_login', 'date_joined'),
        }),
    )
    
    add_fieldsets = (
        ('بيانات الدخول', {
            'fields': ('username', 'password1', 'password2'),
        }),
        ('المعلومات الشخصية', {
            'fields': ('full_name', 'email', 'phone_number'),
        }),
        ('الدور', {
            'fields': ('role', 'is_staff'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    inlines = [PartnerProfileInline]

    @admin.display(description='الدور')
    def role_badge(self, obj):
        if not obj.role:
            return '-'
        colors = {'admin': '#dc3545', 'partner': '#6f42c1', 'user': '#28a745', 'visitor': '#6c757d'}
        color = colors.get(obj.role.name.lower(), '#17a2b8')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{}</span>',
            color, obj.role.name
        )

    @admin.display(description='آخر دخول', ordering='last_login')
    def last_login_fmt(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return '-'

    @admin.display(description='إجراءات سريعة')
    def quick_actions(self, obj):
        return format_html(
            '<div class="action-buttons">'
            '<a class="button" href="{}/change/#password" title="تغيير كلمة المرور" style="padding:4px 8px; margin:0 2px; background:#6c757d; color:white;"><i class="fas fa-key"></i></a>'
            '<a class="button" href="{}/change/#permissions" title="صلاحيات" style="padding:4px 8px; margin:0 2px; background:#17a2b8; color:white;"><i class="fas fa-lock"></i></a>'
            '<a class="button" href="{}/change/" title="تعديل" style="padding:4px 8px; margin:0 2px; background:#ffc107; color:black;"><i class="fas fa-edit"></i></a>'
            '</div>',
            obj.id, obj.id, obj.id
        )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_superuser:
            return format_html('<span style="color:#dc3545; font-weight:600;">👑 مدير</span>')
        if obj.is_staff:
            return format_html('<span style="color:#6f42c1;">🔧 موظف</span>')
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓ نشط</span>')
        return format_html('<span style="color:#dc3545;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل المستخدمين')
    def activate_users(self, request, queryset):
        # Update both is_active and account_status
        count = queryset.update(is_active=True, account_status='active')
        self.message_user(request, f"تم تفعيل {count} مستخدم", messages.SUCCESS)

    @admin.action(description='❌ تعطيل المستخدمين')
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم تعطيل {count} مستخدم", messages.WARNING)

    @admin.action(description='🔧 جعل موظفين')
    def make_staff(self, request, queryset):
        count = queryset.update(is_staff=True)
        self.message_user(request, f"تم ترقية {count} مستخدم لموظف", messages.SUCCESS)

    @admin.action(description='👤 إزالة صلاحية الموظف')
    def remove_staff(self, request, queryset):
        count = queryset.update(is_staff=False)
        self.message_user(request, f"تم إزالة صلاحية الموظف من {count} مستخدم", messages.WARNING)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data["csv_file"]
                result = CsvImporter.import_users(csv_file)
                
                if result['errors']:
                     messages.warning(request, f"تم استيراد {result['created']} مستخدم مع أخطاء: " + "; ".join(result['errors']))
                else:
                    messages.success(request, f"تم استيراد {result['created']} مستخدم بنجاح.")
                return redirect("admin:users_user_changelist")
        else:
            form = CsvImportForm()
        
        context = {
            "form": form,
            "title": "استيراد المستخدمين من CSV",
            "opts": self.model._meta,
        }
        return render(request, "admin/csv_form.html", context)


@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('user', 'commercial_reg_no', 'approval_badge', 'establishments_count', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__username', 'user__email', 'commercial_reg_no', 'organization_name')
    autocomplete_fields = ['user']
    actions = ['approve_partners', 'reject_partners', 'block_users', export_as_csv]
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'

    fieldsets = (
        ('معلومات الشريك', {
            'fields': ('user', 'organization_name', 'commercial_reg_no'),
        }),
        ('مستندات التحقق', {
            'fields': ('commercial_registry_file', 'id_card_image'),
            'classes': ('collapse',),
        }),
        ('الحالة', {
            'fields': ('is_approved',),
        }),
    )

    @admin.display(description='الحالة')
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="background:#28a745; color:white; padding:3px 10px; border-radius:12px;">✅ معتمد</span>')
        return format_html('<span style="background:#ffc107; color:#212529; padding:3px 10px; border-radius:12px;">⏳ قيد المراجعة</span>')

    @admin.display(description='المنشآت')
    def establishments_count(self, obj):
        count = obj.user.establishments.count()
        return format_html('<span style="font-weight:600; color:#17a2b8;">{}</span>', count)

    @admin.action(description='✅ اعتماد الشركاء')
    def approve_partners(self, request, queryset):
        from interactions.notifications.partner import PartnerNotifications
        count = 0
        for profile in queryset:
            if not profile.is_approved:
                profile.is_approved = True
                profile.save(update_fields=['is_approved'])
                
                # Also activate the user account status (it was 'pending' during registration)
                if profile.user.account_status != 'active':
                    profile.user.account_status = 'active'
                    profile.user.save(update_fields=['account_status'])
                
                # Send notification to partner (Skip if admin is approving themselves)
                if profile.user != request.user:
                    PartnerNotifications.notify_partner_approved(profile)
                count += 1
        self.message_user(request, f"تم اعتماد {count} شريك وإرسال إشعارات لهم", messages.SUCCESS)

    @admin.action(description='❌ رفض الشركاء')
    def reject_partners(self, request, queryset):
        from interactions.notifications.partner import PartnerNotifications
        count = 0
        for profile in queryset:
            if profile.is_approved:
                profile.is_approved = False
                profile.save(update_fields=['is_approved'])
                # Send notification to partner with reason
                PartnerNotifications.notify_partner_rejected(profile, reason='تم رفض طلبك من قبل الإدارة')
                count += 1
        self.message_user(request, f"تم رفض {count} شريك وإرسال إشعارات لهم", messages.WARNING)

    @admin.action(description='🚫 حظر المستخدمين')
    def block_users(self, request, queryset):
        for profile in queryset:
            profile.user.is_active = False
            profile.user.save()
        self.message_user(request, f"تم حظر {queryset.count()} مستخدم", messages.WARNING)


@admin.register(UserRegistrationLog)
class UserRegistrationLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'registration_type', 'status_badge', 'ip_address', 'created_at')
    list_filter = ('status', 'registration_type', 'created_at')
    search_fields = ('email', 'username', 'ip_address')
    readonly_fields = (
        'user', 'email', 'username', 'registration_type', 'status',
        'ip_address', 'user_agent', 'referer', 'failure_reason', 
        'metadata', 'created_at'
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    save_on_top = True
    list_per_page = 50

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'completed': '#28a745', 'pending': '#ffc107', 'failed': '#dc3545'}
        labels = {'completed': 'مكتمل', 'pending': 'معلق', 'failed': 'فشل'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:11px;">{}</span>',
            color, label
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserLoginLog)
class UserLoginLogAdmin(admin.ModelAdmin):
    list_display = ('username_or_email', 'user', 'status_badge', 'failure_reason', 'ip_address', 'created_at')
    list_filter = ('status', 'failure_reason', 'created_at')
    search_fields = ('username_or_email', 'ip_address', 'user__username', 'user__email')
    readonly_fields = (
        'user', 'username_or_email', 'status', 'failure_reason',
        'failure_details', 'ip_address', 'user_agent', 'metadata', 'created_at'
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    save_on_top = True
    list_per_page = 50

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'success': '#28a745', 'failed': '#dc3545'}
        labels = {'success': 'ناجح', 'failed': 'فشل'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:11px;">{}</span>',
            color, label
        )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
