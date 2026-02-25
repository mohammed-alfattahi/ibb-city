from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import CulturalLandmark, PublicEmergencyContact, SafetyGuideline


@admin.register(CulturalLandmark)
class CulturalLandmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')
    list_editable = ('order',)
    save_on_top = True
    list_per_page = 20
    actions = ['activate_selected', 'deactivate_selected', 'duplicate_selected']

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'description', 'icon', 'color'),
        }),
        ('الصور', {
            'fields': ('image1', 'image2'),
        }),
        ('الإعدادات', {
            'fields': (('is_active', 'order'),),
        }),
    )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓ نشط</span>')
        return format_html('<span style="color:#dc3545;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل المحدد')
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {queryset.count()} عنصر", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل المحدد')
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {queryset.count()} عنصر", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "تكرار العناصر المحددة"


@admin.register(PublicEmergencyContact)
class PublicEmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('icon_preview', 'title', 'number', 'color_badge', 'type_badges', 'status_badge', 'order')
    list_filter = ('color', 'is_hospital', 'is_primary_card', 'is_active')
    search_fields = ('title', 'number', 'description')
    ordering = ('order', 'title')
    list_editable = ('order',)
    save_on_top = True
    list_per_page = 20
    actions = ['activate_selected', 'deactivate_selected', 'mark_primary', 'duplicate_selected']

    fieldsets = (
        ('معلومات الجهة', {
            'fields': ('title', 'number', 'description'),
            'description': 'أدخل اسم الجهة ورقم الاتصال'
        }),
        ('المظهر', {
            'fields': (('icon', 'color'),),
            'description': 'اختر أيقونة من FontAwesome (مثل: fas fa-ambulance) ولون البطاقة'
        }),
        ('خيارات العرض', {
            'fields': (('is_primary_card', 'is_hospital'), ('is_active', 'order')),
        }),
    )

    @admin.display(description='أيقونة')
    def icon_preview(self, obj):
        colors = {
            'danger': '#dc3545', 'warning': '#ffc107', 'success': '#28a745',
            'primary': '#007bff', 'info': '#17a2b8', 'dark': '#343a40'
        }
        color = colors.get(obj.color, '#6c757d')
        return format_html(
            '<i class="{}" style="color:{}; font-size:18px;"></i>',
            obj.icon, color
        )

    @admin.display(description='اللون')
    def color_badge(self, obj):
        colors = {
            'danger': '#dc3545', 'warning': '#ffc107', 'success': '#28a745',
            'primary': '#007bff', 'info': '#17a2b8', 'dark': '#343a40'
        }
        labels = {
            'danger': 'أحمر', 'warning': 'أصفر', 'success': 'أخضر',
            'primary': 'أزرق', 'info': 'سماوي', 'dark': 'داكن'
        }
        color = colors.get(obj.color, '#6c757d')
        label = labels.get(obj.color, obj.color)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:10px; font-size:10px;">{}</span>',
            color, label
        )

    @admin.display(description='النوع')
    def type_badges(self, obj):
        badges = []
        if obj.is_primary_card:
            badges.append('<span style="background:#6f42c1; color:white; padding:2px 6px; border-radius:8px; font-size:9px; margin-left:4px;">بطاقة</span>')
        if obj.is_hospital:
            badges.append('<span style="background:#dc3545; color:white; padding:2px 6px; border-radius:8px; font-size:9px;">مستشفى</span>')
        return format_html(''.join(badges)) if badges else '-'

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓</span>')
        return format_html('<span style="color:#dc3545;">✗</span>')

    @admin.action(description='✅ تفعيل')
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {queryset.count()} رقم", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل')
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {queryset.count()} رقم", messages.WARNING)

    @admin.action(description='⭐ تحديد كبطاقة رئيسية')
    def mark_primary(self, request, queryset):
        queryset.update(is_primary_card=True)
        self.message_user(request, f"تم تحديد {queryset.count()} كبطاقة رئيسية", messages.SUCCESS)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "تكرار العناصر المحددة"


@admin.register(SafetyGuideline)
class SafetyGuidelineAdmin(admin.ModelAdmin):
    list_display = ('icon_preview', 'title', 'color_badge', 'status_badge', 'order')
    list_filter = ('is_active', 'color')
    search_fields = ('title', 'description')
    ordering = ('order',)
    list_editable = ('order',)
    save_on_top = True
    list_per_page = 20
    actions = ['activate_selected', 'deactivate_selected', 'duplicate_selected']

    fieldsets = (
        ('محتوى الإرشاد', {
            'fields': ('title', 'description'),
        }),
        ('المظهر', {
            'fields': (('icon', 'color'),),
        }),
        ('الإعدادات', {
            'fields': (('is_active', 'order'),),
        }),
    )

    @admin.display(description='أيقونة')
    def icon_preview(self, obj):
        colors = {
            'danger': '#dc3545', 'warning': '#ffc107', 'success': '#28a745', 'primary': '#007bff'
        }
        color = colors.get(obj.color, '#6c757d')
        return format_html('<i class="{}" style="color:{}; font-size:18px;"></i>', obj.icon, color)

    @admin.display(description='اللون')
    def color_badge(self, obj):
        colors = {'danger': '#dc3545', 'warning': '#ffc107', 'success': '#28a745', 'primary': '#007bff'}
        labels = {'danger': 'أحمر', 'warning': 'أصفر', 'success': 'أخضر', 'primary': 'أزرق'}
        color = colors.get(obj.color, '#6c757d')
        label = labels.get(obj.color, obj.color)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:10px; font-size:10px;">{}</span>',
            color, label
        )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓ نشط</span>')
        return format_html('<span style="color:#dc3545;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل')
    def activate_selected(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {queryset.count()} إرشاد", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل')
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {queryset.count()} إرشاد", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "تكرار العناصر المحددة"
