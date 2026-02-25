from django.contrib import admin
from django.contrib import messages
from django.http import HttpRequest
from django.utils.html import format_html

from .models import UIZone, UIComponent, ZoneComponent, UIRevision
from cms.services.ui_builder import copy_zone_components, publish_zone


class ZoneComponentInline(admin.TabularInline):
    model = ZoneComponent
    extra = 1
    min_num = 0
    ordering = ('stage', 'order',)
    fields = ('stage', 'component', 'order', 'is_visible', 'data_override')
    readonly_fields = ()
    classes = ['collapse']


@admin.register(UIZone)
class UIZoneAdmin(admin.ModelAdmin):
    """Enhanced UIZone Admin with visual management."""
    inlines = [ZoneComponentInline]
    list_display = ('name', 'slug', 'component_count_badge', 'stage_info', 'preview_links')
    list_filter = ('slug',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    save_on_top = True
    list_per_page = 20
    actions = ('copy_published_to_draft', 'publish_draft')

    fieldsets = (
        ('📍 معلومات المنطقة', {
            'fields': ('name', 'slug'),
        }),
        ('📄 الوصف', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='المكونات')
    def component_count_badge(self, obj):
        count = obj.components.count()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background:{}; color:white; padding:3px 12px; border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, count
        )

    @admin.display(description='المراحل')
    def stage_info(self, obj):
        draft_count = obj.zone_components.filter(stage='draft').count()
        published_count = obj.zone_components.filter(stage='published').count()
        return format_html(
            '<span style="font-size:11px;">📝 {} | 🌐 {}</span>',
            draft_count, published_count
        )

    def preview_links(self, obj):
        return format_html(
            '<a href="/?preview=1" target="_blank" style="background:#17a2b8; color:white; padding:3px 8px; border-radius:6px; font-size:10px; margin-left:4px;">معاينة</a>'
            '<a href="/" target="_blank" style="background:#28a745; color:white; padding:3px 8px; border-radius:6px; font-size:10px;">مباشر</a>'
        )
    preview_links.short_description = 'روابط'

    @admin.action(description="📝 نسخ (published) إلى (draft)")
    def copy_published_to_draft(self, request: HttpRequest, queryset):
        count = 0
        for zone in queryset:
            copy_zone_components(zone, 'published', 'draft', user=request.user, action='copy_published_to_draft')
            count += 1
        self.message_user(request, f"تم نسخ {count} منطقة إلى المسودة", messages.SUCCESS)

    @admin.action(description="🌐 نشر (draft) إلى (published)")
    def publish_draft(self, request: HttpRequest, queryset):
        count = 0
        for zone in queryset:
            publish_zone(zone, user=request.user)
            count += 1
        self.message_user(request, f"تم نشر {count} منطقة", messages.SUCCESS)


@admin.register(UIComponent)
class UIComponentAdmin(admin.ModelAdmin):
    """Enhanced UIComponent Admin."""
    list_display = ('icon_display', 'name', 'slug', 'template_badge', 'usage_count')
    list_display_links = ('icon_display', 'name')
    search_fields = ('name', 'slug', 'template_path')
    prepopulated_fields = {'slug': ('name',)}
    save_on_top = True
    list_per_page = 20

    fieldsets = (
        ('🧩 معلومات المكون', {
            'fields': ('name', 'slug'),
        }),
        ('📄 القالب', {
            'fields': ('template_path',),
        }),
        ('⚙️ الإعدادات الافتراضية', {
            'fields': ('default_data',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='')
    def icon_display(self, obj):
        return format_html('<span style="font-size:20px;">🧩</span>')

    @admin.display(description='القالب')
    def template_badge(self, obj):
        if obj.template_path:
            short_path = obj.template_path.split('/')[-1] if '/' in obj.template_path else obj.template_path
            return format_html(
                '<code style="background:#f8f9fa; padding:2px 6px; border-radius:4px; font-size:11px;">{}</code>',
                short_path
            )
        return '-'

    @admin.display(description='الاستخدام')
    def usage_count(self, obj):
        count = obj.zone_usages.count() if hasattr(obj, 'zone_usages') else 0
        return format_html(
            '<span style="background:#6f42c1; color:white; padding:2px 10px; border-radius:10px; font-size:10px;">{}</span>',
            count
        )


@admin.register(UIRevision)
class UIRevisionAdmin(admin.ModelAdmin):
    """Enhanced UIRevision Admin for tracking changes."""
    list_display = ('zone', 'action_badge', 'stage_transition', 'created_by', 'created_at')
    list_filter = ('action', 'from_stage', 'to_stage', 'created_at')
    search_fields = ('zone__slug', 'zone__name')
    readonly_fields = ('zone', 'action', 'from_stage', 'to_stage', 'snapshot', 'created_by', 'created_at')
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 30

    @admin.display(description='الإجراء')
    def action_badge(self, obj):
        colors = {
            'publish': '#28a745', 'copy_published_to_draft': '#17a2b8',
            'update': '#ffc107', 'create': '#6f42c1', 'delete': '#dc3545'
        }
        icons = {
            'publish': '🌐', 'copy_published_to_draft': '📋',
            'update': '✏️', 'create': '➕', 'delete': '🗑️'
        }
        color = colors.get(obj.action, '#6c757d')
        icon = icons.get(obj.action, '📝')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:10px;">{} {}</span>',
            color, icon, obj.action
        )

    @admin.display(description='الانتقال')
    def stage_transition(self, obj):
        return format_html(
            '<span style="font-size:11px;">{} → {}</span>',
            obj.from_stage or '-', obj.to_stage or '-'
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
