from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from .models import Season, Event


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_range', 'status_badge', 'events_count', 'created_at')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    save_on_top = True
    list_per_page = 20
    actions = ['activate_seasons', 'deactivate_seasons', 'duplicate_selected']

    fieldsets = (
        ('معلومات الموسم', {
            'fields': ('name', 'description', 'cover_image'),
        }),
        ('الفترة الزمنية', {
            'fields': (('start_date', 'end_date'),),
        }),
        ('الحالة', {
            'fields': ('is_active',),
        }),
    )

    @admin.display(description='الفترة')
    def date_range(self, obj):
        start = obj.start_date.strftime('%Y/%m/%d') if obj.start_date else '-'
        end = obj.end_date.strftime('%Y/%m/%d') if obj.end_date else '-'
        return format_html('<span style="font-size:12px;">{} → {}</span>', start, end)

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        now = timezone.now().date()
        if not obj.is_active:
            return format_html('<span style="color:#6c757d;">⚪ غير نشط</span>')
        if obj.start_date and obj.end_date:
            if now < obj.start_date:
                return format_html('<span style="color:#17a2b8;">📅 قادم</span>')
            elif obj.start_date <= now <= obj.end_date:
                return format_html('<span style="color:#28a745;">🟢 جاري</span>')
            else:
                return format_html('<span style="color:#6c757d;">⏹️ انتهى</span>')
        return format_html('<span style="color:#ffc107;">⏳ معلق</span>')

    @admin.display(description='الفعاليات')
    def events_count(self, obj):
        count = obj.events.count()
        return format_html('<span style="font-weight:600; color:#6f42c1;">{}</span>', count)

    @admin.action(description='✅ تفعيل المواسم')
    def activate_seasons(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} موسم", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل المواسم')
    def deactivate_seasons(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} موسم", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_active = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} موسم بنجاح")
    duplicate_selected.short_description = "📋 تكرار المواسم المحددة"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('title', 'season', 'type_badge', 'date_time_display', 'featured_badge', 'location_short')
    list_filter = ('event_type', 'is_featured', 'start_datetime', 'season')
    search_fields = ('title', 'description', 'location')
    autocomplete_fields = ['season']
    date_hierarchy = 'start_datetime'
    save_on_top = True
    list_per_page = 20
    actions = ['feature_events', 'unfeature_events', 'duplicate_selected']

    fieldsets = (
        ('معلومات الفعالية', {
            'fields': ('title', 'description', 'cover_image'),
        }),
        ('التصنيف والموسم', {
            'fields': (('event_type', 'season'),),
        }),
        ('الموعد والمكان', {
            'fields': (('start_datetime', 'end_datetime'), 'location'),
        }),
        ('الأسعار والإعدادات', {
            'fields': (('price', 'is_featured'),),
        }),
    )

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'festival': '#dc3545', 'concert': '#6f42c1', 'exhibition': '#17a2b8',
            'workshop': '#28a745', 'sports': '#fd7e14', 'cultural': '#e83e8c'
        }
        icons = {
            'festival': '🎉', 'concert': '🎵', 'exhibition': '🖼️',
            'workshop': '🔧', 'sports': '⚽', 'cultural': '🎭'
        }
        color = colors.get(obj.event_type, '#6c757d')
        icon = icons.get(obj.event_type, '📌')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{} {}</span>',
            color, icon, obj.get_event_type_display() if hasattr(obj, 'get_event_type_display') else obj.event_type
        )

    @admin.display(description='الموعد')
    def date_time_display(self, obj):
        if obj.start_datetime:
            date_str = obj.start_datetime.strftime('%Y/%m/%d')
            time_str = obj.start_datetime.strftime('%H:%M')
            return format_html('<span style="font-size:12px;">📅 {} ⏰ {}</span>', date_str, time_str)
        return '-'

    @admin.display(description='مميز')
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="color:#ffc107; font-size:18px;">⭐</span>')
        return format_html('<span style="color:#dee2e6;">☆</span>')

    @admin.display(description='المكان')
    def location_short(self, obj):
        if obj.location:
            return obj.location[:25] + '...' if len(obj.location) > 25 else obj.location
        return '-'

    @admin.action(description='⭐ تمييز الفعاليات')
    def feature_events(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f"تم تمييز {count} فعالية", messages.SUCCESS)

    @admin.action(description='☆ إلغاء التمييز')
    def unfeature_events(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f"تم إلغاء تمييز {count} فعالية", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.is_featured = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} فعالية بنجاح")
    duplicate_selected.short_description = "📋 تكرار الفعاليات المحددة"
