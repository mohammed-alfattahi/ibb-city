from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Community, CommunityMembership, CommunityPost, PostComment


class CommunityMembershipInline(admin.TabularInline):
    model = CommunityMembership
    extra = 0
    autocomplete_fields = ['user']
    classes = ['collapse']


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ('name', 'official_badge', 'created_by', 'members_count', 'posts_count', 'created_at')
    list_filter = ('is_official', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['created_by']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['make_official', 'remove_official', 'duplicate_selected']
    inlines = [CommunityMembershipInline]

    fieldsets = (
        ('معلومات المجتمع', {
            'fields': ('name', 'slug', 'description', 'cover_image'),
        }),
        ('الإعدادات', {
            'fields': (('is_official', 'created_by'),),
        }),
    )

    @admin.display(description='رسمي')
    def official_badge(self, obj):
        if obj.is_official:
            return format_html('<span style="color:#28a745; font-weight:600;">✓ رسمي</span>')
        return format_html('<span style="color:#6c757d;">عادي</span>')

    @admin.display(description='الأعضاء')
    def members_count(self, obj):
        count = obj.members.count()
        return format_html(
            '<span style="background:#17a2b8; color:white; padding:2px 10px; border-radius:12px; font-size:11px;">{}</span>',
            count
        )

    @admin.display(description='المنشورات')
    def posts_count(self, obj):
        count = obj.posts.count()
        return format_html('<span style="font-weight:600; color:#6f42c1;">{}</span>', count)

    @admin.action(description='✓ تحديد كمجتمع رسمي')
    def make_official(self, request, queryset):
        count = queryset.update(is_official=True)
        self.message_user(request, f"تم تحديد {count} مجتمع كرسمي", messages.SUCCESS)

    @admin.action(description='✗ إزالة صفة الرسمية')
    def remove_official(self, request, queryset):
        count = queryset.update(is_official=False)
        self.message_user(request, f"تم إزالة صفة الرسمية من {count} مجتمع", messages.WARNING)

    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.slug = f"{obj.slug}-copy"
            obj.is_official = False
            obj.save()
        self.message_user(request, f"تم تكرار {queryset.count()} مجتمع بنجاح")
    duplicate_selected.short_description = "📋 تكرار المجتمعات المحددة"


@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'role_badge', 'joined_at')
    list_filter = ('role', 'joined_at', 'community')
    search_fields = ('user__username', 'community__name')
    autocomplete_fields = ['user', 'community']
    save_on_top = True
    list_per_page = 20
    date_hierarchy = 'joined_at'
    actions = ['make_admin', 'make_moderator', 'make_member']

    @admin.display(description='الدور')
    def role_badge(self, obj):
        colors = {'admin': '#dc3545', 'moderator': '#fd7e14', 'member': '#28a745'}
        icons = {'admin': '👑', 'moderator': '🛡️', 'member': '👤'}
        labels = {'admin': 'مسؤول', 'moderator': 'مشرف', 'member': 'عضو'}
        color = colors.get(obj.role, '#6c757d')
        icon = icons.get(obj.role, '👤')
        label = labels.get(obj.role, obj.role)
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:11px;">{} {}</span>',
            color, icon, label
        )

    @admin.action(description='👑 ترقية لمسؤول')
    def make_admin(self, request, queryset):
        count = queryset.update(role='admin')
        self.message_user(request, f"تم ترقية {count} عضو لمسؤول", messages.SUCCESS)

    @admin.action(description='🛡️ ترقية لمشرف')
    def make_moderator(self, request, queryset):
        count = queryset.update(role='moderator')
        self.message_user(request, f"تم ترقية {count} عضو لمشرف", messages.SUCCESS)

    @admin.action(description='👤 تخفيض لعضو')
    def make_member(self, request, queryset):
        count = queryset.update(role='member')
        self.message_user(request, f"تم تخفيض {count} إلى عضو", messages.WARNING)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'community', 'type_badge', 'content_preview', 'likes_display', 'created_at')
    list_filter = ('post_type', 'created_at', 'community')
    search_fields = ('content', 'author__username', 'community__name')
    autocomplete_fields = ['community', 'author', 'linked_place']
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 20
    actions = ['delete_posts']

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {'text': '#6c757d', 'image': '#17a2b8', 'link': '#28a745', 'poll': '#6f42c1'}
        icons = {'text': '📝', 'image': '🖼️', 'link': '🔗', 'poll': '📊'}
        color = colors.get(obj.post_type, '#6c757d')
        icon = icons.get(obj.post_type, '📝')
        return format_html('<span style="color:{}; font-size:16px;">{}</span>', color, icon)

    @admin.display(description='المحتوى')
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    @admin.display(description='الإعجابات')
    def likes_display(self, obj):
        return format_html('<span style="color:#dc3545;">❤️ {}</span>', obj.like_count)

    @admin.action(description='🗑️ حذف المنشورات')
    def delete_posts(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"تم حذف {count} منشور", messages.WARNING)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post_preview', 'content_preview', 'created_at')
    search_fields = ('content', 'author__username')
    autocomplete_fields = ['post', 'author', 'parent']
    save_on_top = True
    list_per_page = 30
    date_hierarchy = 'created_at'
    actions = ['delete_comments']

    @admin.display(description='المنشور')
    def post_preview(self, obj):
        return obj.post.content[:30] + '...' if len(obj.post.content) > 30 else obj.post.content

    @admin.display(description='التعليق')
    def content_preview(self, obj):
        return obj.content[:40] + '...' if len(obj.content) > 40 else obj.content

    @admin.action(description='🗑️ حذف التعليقات')
    def delete_comments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"تم حذف {count} تعليق", messages.WARNING)
