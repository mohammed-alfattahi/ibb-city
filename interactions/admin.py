from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Review, PlaceComment, Favorite, Report, Notification, SystemAlert


class PlaceCommentInline(admin.StackedInline):
    model = PlaceComment
    extra = 0
    fk_name = 'parent'


@admin.register(PlaceComment)
class PlaceCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'place', 'visibility_badge', 'content_preview', 'created_at')
    list_filter = ('visibility_state', 'created_at')
    search_fields = ('content', 'user__username', 'place__name')
    autocomplete_fields = ['user', 'place']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'hide_comments', 'delete_comments']

    @admin.display(description='الحالة')
    def visibility_badge(self, obj):
        colors = {'visible': '#28a745', 'partner_hidden': '#6c757d', 'admin_hidden': '#343a40'}
        labels = {'visible': '👁 ظاهر', 'partner_hidden': '🙈 مخفي (شريك)', 'admin_hidden': '⛔ مخفي (مكتب)'}
        color = colors.get(obj.visibility_state, '#6c757d')
        label = labels.get(obj.visibility_state, obj.visibility_state)
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, label)

    @admin.display(description='المحتوى')
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    @admin.action(description='✅ إظهار التعليقات')
    def approve_comments(self, request, queryset):
        count = queryset.update(visibility_state='visible')
        self.message_user(request, f"تم إظهار {count} تعليق", messages.SUCCESS)

    @admin.action(description='🙈 إخفاء التعليقات')
    def hide_comments(self, request, queryset):
        count = queryset.update(visibility_state='admin_hidden')
        self.message_user(request, f"تم إخفاء {count} تعليق", messages.WARNING)

    @admin.action(description='🗑️ حذف التعليقات')
    def delete_comments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"تم حذف {count} تعليق", messages.WARNING)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Enhanced Review Admin with visibility management."""
    change_list_template = "admin/import_change_list.html"
    change_form_template = "admin/tabbed_change_form.html"
    list_display = ('place', 'user', 'visibility_badge', 'rating_stars', 'comment_preview', 'created_at')
    list_filter = ('visibility_state', 'rating', 'created_at')
    search_fields = ('place__name', 'user__username', 'comment')
    autocomplete_fields = ['user', 'place']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['show_reviews', 'admin_hide_reviews', 'delete_reviews']

    fieldsets = (
        ('📝 المراجعة', {
            'fields': ('place', 'user', ('rating', 'visibility_state')),
        }),
        ('💬 المحتوى', {
            'fields': ('comment',),
        }),
        ('🙈 إعدادات الإخفاء', {
            'fields': ('hidden_by', 'hidden_reason'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='الحالة')
    def visibility_badge(self, obj):
        colors = {'visible': '#28a745', 'partner_hidden': '#6c757d', 'admin_hidden': '#343a40'}
        labels = {'visible': '👁 ظاهر', 'partner_hidden': '🙈 مخفي (شريك)', 'admin_hidden': '⛔ مخفي (مكتب)'}
        color = colors.get(obj.visibility_state, '#6c757d')
        label = labels.get(obj.visibility_state, obj.visibility_state)
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, label)

    @admin.display(description='التقييم')
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        colors = {5: '#28a745', 4: '#20c997', 3: '#ffc107', 2: '#fd7e14', 1: '#dc3545'}
        color = colors.get(obj.rating, '#6c757d')
        return format_html('<span style="color:{}; font-size:14px;">{}</span>', color, stars)

    @admin.display(description='التعليق')
    def comment_preview(self, obj):
        if not obj.comment:
            return '-'
        return obj.comment[:40] + '...' if len(obj.comment) > 40 else obj.comment

    @admin.action(description='✅ إظهار المراجعات')
    def show_reviews(self, request, queryset):
        count = queryset.update(visibility_state='visible', hidden_by=None, hidden_reason='')
        self.message_user(request, f"تم إظهار {count} مراجعة", messages.SUCCESS)

    @admin.action(description='⛔ إخفاء المراجعات (مكتب السياحة)')
    def admin_hide_reviews(self, request, queryset):
        count = queryset.update(visibility_state='admin_hidden', hidden_by=request.user)
        self.message_user(request, f"تم إخفاء {count} مراجعة", messages.WARNING)

    @admin.action(description='🗑️ حذف المراجعات')
    def delete_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"تم حذف {count} مراجعة", messages.WARNING)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Enhanced Favorite Admin."""
    list_display = ('user_badge', 'place', 'place_category', 'created_at')
    search_fields = ('user__username', 'place__name')
    autocomplete_fields = ['user', 'place']
    list_filter = ('created_at',)
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'

    @admin.display(description='المستخدم')
    def user_badge(self, obj):
        return format_html(
            '<span style="font-size:14px;">❤️</span> {}',
            obj.user.username
        )

    @admin.display(description='التصنيف')
    def place_category(self, obj):
        if obj.place and obj.place.category:
            return format_html(
                '<span style="background:#e9ecef; padding:2px 8px; border-radius:8px; font-size:11px;">{}</span>',
                obj.place.category.name
            )
        return '-'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Enhanced Report Admin with workflow management."""
    change_list_template = "admin/import_change_list.html"
    list_display = ('id', 'user', 'report_type_badge', 'status_badge', 'description_preview', 'created_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('user__username', 'description')
    autocomplete_fields = ['user']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['mark_reviewed', 'mark_resolved', 'mark_dismissed']

    readonly_fields = ('created_at',)

    fieldsets = (
        ('📌 معلومات البلاغ', {
            'fields': ('user', 'report_type', 'status'),
        }),
        ('📝 التفاصيل', {
            'fields': ('description', 'content_type', 'object_id'),
        }),
    )

    @admin.display(description='النوع')
    def report_type_badge(self, obj):
        colors = {'spam': '#dc3545', 'inappropriate': '#fd7e14', 'incorrect': '#ffc107', 'other': '#6c757d'}
        labels = {'spam': '🚫 سبام', 'inappropriate': '⚠️ غير لائق', 'incorrect': '❌ خاطئ', 'other': '📝 آخر'}
        color = colors.get(obj.report_type, '#6c757d')
        label = labels.get(obj.report_type, obj.report_type)
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, label)

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'reviewed': '#17a2b8', 'resolved': '#28a745', 'dismissed': '#6c757d'}
        labels = {'pending': '⏳ معلق', 'reviewed': '👁 قيد المراجعة', 'resolved': '✅ تم الحل', 'dismissed': '❌ مرفوض'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{}</span>',
            color, label
        )

    @admin.display(description='الوصف')
    def description_preview(self, obj):
        return obj.description[:40] + '...' if len(obj.description) > 40 else obj.description

    @admin.action(description='👁 تحديد كقيد المراجعة')
    def mark_reviewed(self, request, queryset):
        count = queryset.update(status='reviewed')
        self.message_user(request, f"تم تحديث {count} بلاغ", messages.INFO)

    @admin.action(description='✅ تحديد كمحلول')
    def mark_resolved(self, request, queryset):
        count = queryset.update(status='resolved')
        self.message_user(request, f"تم حل {count} بلاغ", messages.SUCCESS)

    @admin.action(description='❌ رفض البلاغات')
    def mark_dismissed(self, request, queryset):
        count = queryset.update(status='dismissed')
        self.message_user(request, f"تم رفض {count} بلاغ", messages.WARNING)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type_badge', 'title', 'read_badge', 'created_at')
    list_filter = ('is_read', 'notification_type', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    autocomplete_fields = ['recipient']
    save_on_top = True
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'read_at')
    list_per_page = 50
    actions = ['mark_as_read', 'delete_notifications']

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'info': '#17a2b8', 'success': '#28a745', 'warning': '#ffc107', 
            'error': '#dc3545', 'system': '#6f42c1'
        }
        color = colors.get(obj.notification_type, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.notification_type
        )

    @admin.display(description='مقروء')
    def read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#28a745;">✓</span>')
        return format_html('<span style="color:#dc3545;">✗</span>')

    @admin.action(description='✓ تحديد كمقروء')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"تم تحديد {count} كمقروء", messages.SUCCESS)

    @admin.action(description='🗑️ حذف الإشعارات')
    def delete_notifications(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"تم حذف {count} إشعار", messages.WARNING)
    
    def has_add_permission(self, request):
        return False


# ==========================================
# Notification Outbox Admin (Async Delivery)
# ==========================================
from .notifications.outbox import NotificationOutbox

@admin.register(NotificationOutbox)
class NotificationOutboxAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'title', 'channel_badge', 'status_badge', 'attempts', 'created_at')
    list_filter = ('status', 'channel', 'provider', 'created_at')
    search_fields = ('recipient__username', 'title', 'body')
    autocomplete_fields = ['recipient']
    save_on_top = True
    readonly_fields = ('id', 'created_at', 'updated_at', 'sent_at')
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('المستلم', {
            'fields': ('recipient', 'channel', 'provider')
        }),
        ('المحتوى', {
            'fields': ('title', 'body', 'payload')
        }),
        ('حالة التسليم', {
            'fields': ('status', 'attempts', 'max_attempts', 'last_error')
        }),
        ('التواريخ', {
            'fields': ('scheduled_at', 'sent_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['retry_notifications', 'mark_as_dead']

    @admin.display(description='القناة')
    def channel_badge(self, obj):
        colors = {'push': '#28a745', 'email': '#17a2b8', 'sms': '#6f42c1'}
        color = colors.get(obj.channel, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, obj.channel
        )

    @admin.display(description='الحالة')
    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'sent': '#28a745', 'failed': '#dc3545', 'dead': '#343a40', 'retrying': '#17a2b8'}
        labels = {'pending': 'معلق', 'sent': 'مرسل', 'failed': 'فشل', 'dead': 'ميت', 'retrying': 'إعادة'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:8px; font-size:10px;">{}</span>',
            color, label
        )
    
    @admin.action(description="🔄 إعادة إرسال الإشعارات")
    def retry_notifications(self, request, queryset):
        from interactions.tasks.notifications import send_outbox_notification
        
        count = 0
        for outbox in queryset.filter(status__in=['failed', 'dead', 'retrying']):
            outbox.reset_for_retry()
            send_outbox_notification.delay(str(outbox.id))
            count += 1
        
        self.message_user(request, f"جاري إعادة إرسال {count} إشعار", messages.INFO)
    
    @admin.action(description="☠️ تحديد كميت (إيقاف المحاولات)")
    def mark_as_dead(self, request, queryset):
        updated = queryset.update(status='dead')
        self.message_user(request, f"تم تحديد {updated} إشعار كميت", messages.WARNING)
    
    
    def has_add_permission(self, request):
        return False


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    """Admin interface for sending broadcasts."""
    list_display = ('title', 'alert_type', 'target_audience', 'created_by', 'is_sent', 'created_at')
    list_filter = ('alert_type', 'target_audience', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('is_sent', 'sent_at', 'created_by')
    
    fieldsets = (
        ('📢 تفاصيل التنبيه', {
            'fields': ('title', 'message', 'alert_type', 'target_audience'),
            'description': 'بمجرد الحفظ، سيتم إرسال الإشعار فوراً إلى جميع المستخدمين المستهدفين.'
        }),
        ('معلومات الإرسال', {
            'fields': ('is_sent', 'sent_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
