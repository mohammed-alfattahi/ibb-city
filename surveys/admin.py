from django.contrib import admin
from django.contrib import messages
from django import forms
from django.utils.html import format_html
from django.utils import timezone
from .models import Survey, SurveyQuestion, SurveyResponse


class SurveyQuestionForm(forms.ModelForm):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'
        widgets = {
            'choices': forms.Textarea(attrs={'rows': 3, 'placeholder': 'خيار واحد في كل سطر...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Handle showing empty string instead of [] for new or empty choices
        choices = self.initial.get('choices')
        
        if choices is None:
            if self.instance and self.instance.pk:
                choices = self.instance.choices
            else:
                choices = []
            
        if choices == [] or choices == '[]':
            self.initial['choices'] = ""
        elif isinstance(choices, list):
            self.initial['choices'] = "\n".join(choices)
        elif isinstance(choices, str) and choices == '[]':
             self.initial['choices'] = ""

    def clean_choices(self):
        data = self.cleaned_data.get('choices')
        if isinstance(data, str):
            # Clean up the string and filter out any leftover '[]' text
            cleaned = [c.strip() for c in data.split('\n') if c.strip() and c.strip() != '[]']
            return cleaned
        return data if data is not None else []


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    form = SurveyQuestionForm
    extra = 1
    fields = ['question_text', 'question_type', 'choices', 'is_required', 'order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    change_list_template = "admin/import_change_list.html"
    list_display = ['title', 'detailed_status', 'responses_display', 'date_range', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [SurveyQuestionInline]
    readonly_fields = ['created_by', 'response_count']
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 20
    actions = ['activate_surveys', 'deactivate_surveys', 'send_notification', 'duplicate_selected']

    fieldsets = (
        ('معلومات الاستبيان', {
            'fields': ('title', 'description'),
        }),
        ('الفترة الزمنية', {
            'fields': (('start_date', 'end_date'),),
        }),
        ('الإعدادات', {
            'fields': (('is_active', 'created_by'), 'max_responses', 'response_count'),
        }),
    )

    @admin.display(description='حالة الاستبيان')
    def detailed_status(self, obj):
        info = obj.status_info
        
        # Toggle component (AJAX)
        toggle_attrs = f'data-id="{obj.id}" data-app="surveys" data-model="survey" data-field="is_active"'
        active_class = "btn-success" if obj.is_active else "btn-light"
        active_icon = "fa-toggle-on" if obj.is_active else "fa-toggle-off"
        
        return format_html(
            '<div class="d-flex align-items-center gap-2">'
            '<button class="btn btn-sm {} active-toggle" {} title="تبديل الحالة">'
            '<i class="fas {}"></i>'
            '</button>'
            '<span class="badge bg-{} p-2" style="min-width: 80px;">'
            '<i class="fas fa-{} me-1"></i> {}'
            '</span>'
            '</div>',
            active_class, toggle_attrs, active_icon,
            info['class'], info['icon'], info['label']
        )

    @admin.display(description='الردود')
    def responses_display(self, obj):
        count = obj.response_count
        color = '#28a745' if count > 10 else '#ffc107' if count > 0 else '#6c757d'
        return format_html(
            '<span style="background:{}; color:white; padding:3px 12px; border-radius:12px; font-size:12px; font-weight:600;">{}</span>',
            color, count
        )

    @admin.display(description='الفترة')
    def date_range(self, obj):
        start = obj.start_date.strftime('%m/%d') if obj.start_date else '∞'
        end = obj.end_date.strftime('%m/%d') if obj.end_date else '∞'
        return format_html('<span style="font-size:12px;">📅 {} → {}</span>', start, end)

    @admin.action(description='✅ تفعيل الاستبيانات')
    def activate_surveys(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"تم تفعيل {count} استبيان", messages.SUCCESS)

    @admin.action(description='❌ إلغاء تفعيل الاستبيانات')
    def deactivate_surveys(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"تم إلغاء تفعيل {count} استبيان", messages.WARNING)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    @admin.action(description='📨 إرسال إشعار للسياح')
    def send_notification(self, request, queryset):
        from interactions.notifications import NotificationService
        
        count = 0
        for survey in queryset:
            if not survey.is_active:
                continue
                
            NotificationService.notify_group(
                target_group='tourists',
                title=f'استبيان جديد: {survey.title}',
                message='نود سماع رأيك! شارك في الاستبيان الجديد لتحسين خدماتنا.',
                url=f'/surveys/{survey.id}/'
            )
            count += 1
            
        self.message_user(request, f"تم إرسال إشعارات لـ {count} استبيان.", messages.SUCCESS)

    @admin.action(description="📋 تكرار الاستبيانات المحددة")
    def duplicate_selected(self, request, queryset):
        for obj in queryset:
            # Create a list of questions to duplicate later
            questions = list(obj.questions.all())
            
            # Step 1: Duplicate the Survey
            obj.pk = None
            obj.is_active = False
            obj.title = f"{obj.title} (نسخة)"
            obj.save()
            
            # Step 2: Duplicate all associated questions
            for q in questions:
                q.pk = None
                q.survey = obj
                q.save()
                
        self.message_user(request, f"تم تكرار {queryset.count()} استبيان مع كافة الأسئلة بنجاح.", messages.SUCCESS)



@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    form = SurveyQuestionForm
    list_display = ['question_preview', 'survey', 'type_badge', 'required_badge', 'order']
    list_filter = ['survey', 'question_type', 'is_required']
    search_fields = ['question_text']
    ordering = ['survey', 'order']
    save_on_top = True
    list_per_page = 30

    @admin.display(description='السؤال')
    def question_preview(self, obj):
        return obj.question_text[:40] + '...' if len(obj.question_text) > 40 else obj.question_text

    @admin.display(description='النوع')
    def type_badge(self, obj):
        colors = {
            'text': '#6c757d', 'textarea': '#17a2b8', 'number': '#28a745',
            'select': '#6f42c1', 'radio': '#fd7e14', 'checkbox': '#dc3545',
            'rating': '#ffc107'
        }
        icons = {
            'text': '📝', 'textarea': '📄', 'number': '🔢',
            'select': '📋', 'radio': '🔘', 'checkbox': '☑️',
            'rating': '⭐',
            'choice': '📻', 'date': '📅'
        }
        color = colors.get(obj.question_type, '#6c757d')
        icon = icons.get(obj.question_type, '❓')
        return format_html('<span style="color:{}; font-size:14px;">{}</span>', color, icon)

    @admin.display(description='مطلوب')
    def required_badge(self, obj):
        if obj.is_required:
            return format_html('<span style="color:#dc3545; font-weight:600;">*</span>')
        return '-'


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'user', 'answers_preview', 'created_at']
    list_filter = ['survey', 'created_at']
    readonly_fields = ['survey', 'user', 'answers', 'created_at']
    date_hierarchy = 'created_at'
    save_on_top = True
    list_per_page = 50

    @admin.display(description='الإجابات')
    def answers_preview(self, obj):
        if obj.answers:
            count = len(obj.answers) if isinstance(obj.answers, dict) else 0
            return format_html(
                '<span style="background:#17a2b8; color:white; padding:2px 10px; border-radius:8px; font-size:11px;">{} إجابة</span>',
                count
            )
        return '-'
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
