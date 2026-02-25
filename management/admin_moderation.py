from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from management.models.moderation import BannedWord, ModerationEvent


@admin.register(BannedWord)
class BannedWordAdmin(admin.ModelAdmin):
    list_display = ('term_masked', 'severity_badge', 'language_badge', 'status_badge', 'updated_at')
    list_filter = ('severity', 'language', 'is_active')
    search_fields = ('term',)
    save_on_top = True
    list_per_page = 30
    actions = ['activate_words', 'deactivate_words']

    fieldsets = (
        ('الكلمة المحظورة', {
            'fields': ('term', 'severity'),
        }),
        ('الإعدادات', {
            'fields': (('language', 'is_active'),),
        }),
    )

    @admin.display(description='الكلمة')
    def term_masked(self, obj):
        # Mask the word for privacy/display
        if len(obj.term) > 2:
            masked = obj.term[0] + '*' * (len(obj.term) - 2) + obj.term[-1]
        else:
            masked = '*' * len(obj.term)
        return format_html('<code style="background:#f8f9fa; padding:2px 6px; border-radius:4px;">{}</code>', masked)

    @admin.display(description='الشدة')
    def severity_badge(self, obj):
        colors = {'low': '#28a745', 'medium': '#ffc107', 'high': '#fd7e14', 'critical': '#dc3545'}
        icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
        color = colors.get(obj.severity, '#6c757d')
        icon = icons.get(obj.severity, '⚠️')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:10px; font-size:11px;">{} {}</span>',
            color, icon, obj.get_severity_display() if hasattr(obj, 'get_severity_display') else obj.severity
        )

    @admin.display(description='اللغة')
    def language_badge(self, obj):
        icons = {'ar': '🇸🇦', 'en': '🇬🇧', 'all': '🌍'}
        icon = icons.get(obj.language, '🈯')
        return format_html('<span style="font-size:16px;">{}</span>', icon)

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#28a745;">✓ نشط</span>')
        return format_html('<span style="color:#dc3545;">✗ معطل</span>')

    @admin.action(description='✅ تفعيل الكلمات')
    def activate_words(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} كلمة", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل الكلمات')
    def deactivate_words(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} كلمة", messages.WARNING)


@admin.register(ModerationEvent)
class ModerationEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'action_badge', 'severity_badge', 'user_display', 'content_preview', 'ip_address', 'created_at')
    list_filter = ('action_taken', 'severity', 'created_at')
    search_fields = ('content_snapshot', 'user__username', 'ip_address')
    readonly_fields = ('content_snapshot', 'matched_terms', 'created_at', 'ip_address', 'user')
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 50
    actions = ['block_users', 'warn_users']

    fieldsets = (
        ('تفاصيل الحدث', {
            'fields': ('user', 'action_taken', 'severity'),
        }),
        ('المحتوى', {
            'fields': ('content_snapshot', 'matched_terms'),
        }),
        ('معلومات إضافية', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='الإجراء')
    def action_badge(self, obj):
        colors = {'blocked': '#dc3545', 'warned': '#ffc107', 'flagged': '#17a2b8', 'allowed': '#28a745'}
        icons = {'blocked': '🚫', 'warned': '⚠️', 'flagged': '🚩', 'allowed': '✓'}
        color = colors.get(obj.action_taken, '#6c757d')
        icon = icons.get(obj.action_taken, '📌')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:10px; font-size:11px;">{} {}</span>',
            color, icon, obj.get_action_taken_display() if hasattr(obj, 'get_action_taken_display') else obj.action_taken
        )

    @admin.display(description='الشدة')
    def severity_badge(self, obj):
        colors = {'low': '#28a745', 'medium': '#ffc107', 'high': '#fd7e14', 'critical': '#dc3545'}
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.severity
        )

    @admin.display(description='المستخدم')
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/users/user/{}/change/" style="color:#17a2b8;">{}</a>',
                obj.user.id, obj.user.username
            )
        return '-'

    @admin.display(description='المحتوى')
    def content_preview(self, obj):
        if obj.content_snapshot:
            return obj.content_snapshot[:40] + '...' if len(obj.content_snapshot) > 40 else obj.content_snapshot
        return '-'

    @admin.action(description='🚫 حظر المستخدمين')
    def block_users(self, request, queryset):
        count = 0
        for event in queryset:
            if event.user:
                event.user.is_active = False
                event.user.save()
                count += 1
        self.message_user(request, f"تم حظر {count} مستخدم", messages.WARNING)

    @admin.action(description='⚠️ تحذير المستخدمين')
    def warn_users(self, request, queryset):
        from interactions.notifications import NotificationService
        count = 0
        for event in queryset:
            if event.user:
                NotificationService.send(
                    user=event.user,
                    title='تحذير من الإدارة',
                    message='تم رصد محتوى مخالف. يرجى الالتزام بسياسات الموقع.',
                    notification_type='warning'
                )
                count += 1
        self.message_user(request, f"تم تحذير {count} مستخدم", messages.WARNING)
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
