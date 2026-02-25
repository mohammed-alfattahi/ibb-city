# management/admin_ui.py
# Admin registration for UI/CMS models - Enhanced Version

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import (
    SiteSetting, Menu, SocialLink,
    SidebarWidget, SidebarLink,
    HomePageSection, HeroSlide,
    FeatureToggle, NotificationSetting,
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Site settings - singleton pattern enforced"""
    list_display = ("site_name", "contact_email", "contact_phone", "maintenance_badge")
    save_on_top = True
    list_per_page = 20

    fieldsets = (
        ('معلومات الموقع', {
            'fields': ('site_name', 'site_description', 'logo', 'favicon'),
        }),
        ('معلومات الاتصال', {
            'fields': (('contact_email', 'contact_phone'), 'address'),
        }),
        ('الصيانة', {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='الصيانة')
    def maintenance_badge(self, obj):
        if getattr(obj, 'maintenance_mode', False):
            return format_html('<span style="background:#dc3545; color:white; padding:3px 10px; border-radius:12px;">🔧 وضع الصيانة</span>')
        return format_html('<span style="color:#28a745;">✓ يعمل</span>')
    
    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    """Dynamic menu management"""
    list_display = ("title", "location_badge", "status_badge", "order", "parent", "visibility_icons")
    list_filter = ("location", "is_active", "visible_for_guests", "visible_for_users")
    search_fields = ("title", "url")
    list_editable = ("order",)
    ordering = ("location", "order")
    save_on_top = True
    list_per_page = 20
    actions = ['activate_menus', 'deactivate_menus', 'duplicate_selected']

    fieldsets = (
        ('معلومات القائمة', {
            'fields': ('title', 'url', 'parent'),
        }),
        ('الموقع والترتيب', {
            'fields': (('location', 'order'),),
        }),
        ('الظهور', {
            'fields': ('is_active', ('visible_for_guests', 'visible_for_users', 'visible_for_admins')),
        }),
    )

    @admin.display(description='الموقع')
    def location_badge(self, obj):
        colors = {'header': '#17a2b8', 'footer': '#6c757d', 'sidebar': '#6f42c1'}
        color = colors.get(obj.location, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.get_location_display() if hasattr(obj, 'get_location_display') else obj.location
        )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓</span>')
        return format_html('<span style="color:#dc3545;">✗</span>')

    @admin.display(description='الظهور')
    def visibility_icons(self, obj):
        icons = []
        if obj.visible_for_guests:
            icons.append('👥')
        if obj.visible_for_users:
            icons.append('👤')
        if obj.visible_for_admins:
            icons.append('👑')
        return ' '.join(icons) if icons else '-'

    @admin.action(description='✅ تفعيل')
    def activate_menus(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} قائمة", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل')
    def deactivate_menus(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} قائمة", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_active = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "📋 تكرار العناصر المحددة"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    """Social media links management"""
    list_display = ("icon_preview", "label", "url_short", "status_badge", "order")
    list_filter = ("is_active",)
    search_fields = ("label", "url")
    list_editable = ("order",)
    save_on_top = True
    list_per_page = 20
    actions = ['activate_links', 'deactivate_links', 'duplicate_selected']

    @admin.display(description='أيقونة')
    def icon_preview(self, obj):
        if hasattr(obj, 'icon') and obj.icon:
            return format_html('<i class="{}" style="font-size:18px; color:#17a2b8;"></i>', obj.icon)
        return '🔗'

    @admin.display(description='الرابط')
    def url_short(self, obj):
        return obj.url[:30] + '...' if len(obj.url) > 30 else obj.url

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓ نشط</span>')
        return format_html('<span style="color:#dc3545;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل')
    def activate_links(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} رابط", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل')
    def deactivate_links(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} رابط", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "📋 تكرار العناصر المحددة"


class SidebarLinkInline(admin.TabularInline):
    """Inline editor for SidebarWidget links"""
    model = SidebarLink
    extra = 1
    fields = ("title", "url", "is_active", "order")


@admin.register(SidebarWidget)
class SidebarWidgetAdmin(admin.ModelAdmin):
    """Sidebar widget management with inline links"""
    list_display = ("title", "type_badge", "visibility_badge", "order", "links_count")
    list_filter = ("widget_type", "is_visible")
    search_fields = ("title", "content")
    list_editable = ("order",)
    inlines = [SidebarLinkInline]
    save_on_top = True
    list_per_page = 20
    actions = ['show_widgets', 'hide_widgets', 'duplicate_selected']

    fieldsets = (
        ('معلومات الودجت', {
            'fields': ('title', 'widget_type', 'content'),
        }),
        ('الظهور', {
            'fields': ('is_visible', 'order', 'pages', 'roles'),
        }),
    )

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {'links': '#17a2b8', 'html': '#6f42c1', 'categories': '#28a745', 'popular': '#fd7e14'}
        color = colors.get(obj.widget_type, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.get_widget_type_display() if hasattr(obj, 'get_widget_type_display') else obj.widget_type
        )

    @admin.display(description='ظاهر')
    def visibility_badge(self, obj):
        if obj.is_visible:
            return format_html('<span style="color:#28a745;">👁</span>')
        return format_html('<span style="color:#dc3545;">🙈</span>')

    @admin.display(description='الروابط')
    def links_count(self, obj):
        count = obj.links.count()
        return format_html('<span style="color:#17a2b8; font-weight:600;">{}</span>', count)

    @admin.action(description='👁 إظهار')
    def show_widgets(self, request, queryset):
        count = queryset.update(is_visible=True)
        self.message_user(request, f"تم إظهار {count} ودجت", messages.SUCCESS)

    @admin.action(description='🙈 إخفاء')
    def hide_widgets(self, request, queryset):
        count = queryset.update(is_visible=False)
        self.message_user(request, f"تم إخفاء {count} ودجت", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_visible = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "📋 تكرار العناصر المحددة"


@admin.register(HomePageSection)
class HomePageSectionAdmin(admin.ModelAdmin):
    """Home page section builder"""
    list_display = ("title", "type_badge", "visibility_badge", "order")
    list_filter = ("section_type", "is_visible")
    search_fields = ("title", "content")
    list_editable = ("order",)
    save_on_top = True
    list_per_page = 20
    actions = ['show_sections', 'hide_sections', 'duplicate_selected']

    fieldsets = (
        ('معلومات القسم', {
            'fields': ('title', 'section_type'),
        }),
        ('المحتوى', {
            'fields': ('content',),
            'description': '⚠️ يستخدم فقط لنوع "HTML مخصص". سيتم تنظيف HTML للأمان.'
        }),
        ('الظهور', {
            'fields': ('is_visible', 'order'),
        }),
    )

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'hero': '#dc3545', 'featured_places': '#28a745', 'categories': '#17a2b8',
            'events': '#6f42c1', 'custom_html': '#fd7e14', 'partners': '#e83e8c'
        }
        icons = {
            'hero': '🖼️', 'featured_places': '📍', 'categories': '📂',
            'events': '🎉', 'custom_html': '💻', 'partners': '🤝'
        }
        color = colors.get(obj.section_type, '#6c757d')
        icon = icons.get(obj.section_type, '📦')
        label = obj.get_section_type_display() if hasattr(obj, 'get_section_type_display') else obj.section_type
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:10px; font-size:11px;">{} {}</span>',
            color, icon, label
        )

    @admin.display(description='ظاهر')
    def visibility_badge(self, obj):
        if obj.is_visible:
            return format_html('<span style="color:#28a745;">👁 ظاهر</span>')
        return format_html('<span style="color:#dc3545;">🙈 مخفي</span>')

    @admin.action(description='👁 إظهار')
    def show_sections(self, request, queryset):
        count = queryset.update(is_visible=True)
        self.message_user(request, f"تم إظهار {count} قسم", messages.SUCCESS)

    @admin.action(description='🙈 إخفاء')
    def hide_sections(self, request, queryset):
        count = queryset.update(is_visible=False)
        self.message_user(request, f"تم إخفاء {count} قسم", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_visible = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "📋 تكرار العناصر المحددة"


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    """Hero carousel slides management"""
    list_display = ("image_preview", "title", "subtitle_short", "status_badge", "order", "button_text")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    list_editable = ("order",)
    save_on_top = True
    list_per_page = 20
    actions = ['activate_slides', 'deactivate_slides', 'duplicate_selected']

    fieldsets = (
        ('محتوى الشريحة', {
            'fields': ('title', 'subtitle', 'image'),
        }),
        ('الزر', {
            'fields': (('button_text', 'button_link'),),
        }),
        ('الظهور', {
            'fields': (('is_active', 'order'),),
        }),
    )

    @admin.display(description='صورة')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px; height:35px; object-fit:cover; border-radius:6px; box-shadow:0 2px 4px rgba(0,0,0,0.1);"/>',
                obj.image.url
            )
        return '-'

    @admin.display(description='الوصف')
    def subtitle_short(self, obj):
        if obj.subtitle:
            return obj.subtitle[:30] + '...' if len(obj.subtitle) > 30 else obj.subtitle
        return '-'

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background:#28a745; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">✓ نشط</span>')
        return format_html('<span style="background:#6c757d; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل الشرائح')
    def activate_slides(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} شريحة", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل الشرائح')
    def deactivate_slides(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} شريحة", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_active = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} عنصر بنجاح")
    duplicate_selected.short_description = "📋 تكرار العناصر المحددة"


@admin.register(FeatureToggle)
class FeatureToggleAdmin(admin.ModelAdmin):
    """System Feature Flags Management"""
    list_display = ("key", "description", "status_badge")
    list_filter = ("is_enabled",)
    search_fields = ("key", "description")
    save_on_top = True
    list_per_page = 20
    actions = ['enable_features', 'disable_features']

    fieldsets = (
        ('معلومات الميزة', {
            'fields': ('key', 'description'),
        }),
        ('الحالة', {
            'fields': ('is_enabled',),
        }),
    )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_enabled:
            return format_html('<span style="color:#28a745; font-weight:bold;">✓ مفعل</span>')
        return format_html('<span style="color:#dc3545; font-weight:bold;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل الميزات المحددة')
    def enable_features(self, request, queryset):
        count = queryset.update(is_enabled=True)
        self.message_user(request, f"تم تفعيل {count} ميزة", messages.SUCCESS)

    @admin.action(description='❌ تعطيل الميزات المحددة')
    def disable_features(self, request, queryset):
        count = queryset.update(is_enabled=False)
        self.message_user(request, f"تم تعطيل {count} ميزة", messages.WARNING)


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    """System-wide Notification Settings"""
    list_display = ("__str__", "retention_days", "allow_delete", "allow_mark_all")
    save_on_top = True
    
    fieldsets = (
        ('إعدادات عامة', {
            'fields': ('retention_days',),
            'description': 'عدد الأيام للاحتفاظ بالإشعارات قبل الحذف التلقائي'
        }),
        ('صلاحيات المستخدم', {
            'fields': ('allow_delete', 'allow_mark_all'),
        }),
    )

    def has_add_permission(self, request):
        # Singleton: Only allow add if none exists
        return not NotificationSetting.objects.exists()

