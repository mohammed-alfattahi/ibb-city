from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel


class Survey(TimeStampedModel):
    """نموذج الاستبيان"""
    title = models.CharField(max_length=200, verbose_name='عنوان الاستبيان')
    description = models.TextField(blank=True, verbose_name='وصف الاستبيان')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_surveys'
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='تاريخ البدء')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الانتهاء')
    max_responses = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='الحد الأقصى للردود',
        help_text='سيتم إغلاق الاستبيان تلقائياً عند الوصول لهذا العدد (اتركه فارغاً للاستمرار بلا حدود)'
    )

    class Meta:
        verbose_name = 'استبيان'
        verbose_name_plural = 'الاستبيانات'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def response_count(self):
        return self.responses.count()

    @property
    def is_open(self):
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        if self.max_responses and self.response_count >= self.max_responses:
            return False
        return True

    @property
    def status_info(self):
        """إرجاع معلومات الحالة للعرض المتطور"""
        from django.utils import timezone
        today = timezone.now().date()
        
        if not self.is_active:
            return {'label': 'معطّل (يدوي)', 'class': 'secondary', 'icon': 'pause-circle'}
        
        if self.max_responses and self.response_count >= self.max_responses:
            return {'label': 'مكتمل (الحد الأقصى)', 'class': 'danger', 'icon': 'check-double'}
            
        if self.start_date and today < self.start_date:
            return {'label': 'مجدول وقيد الانتظار', 'class': 'info', 'icon': 'clock'}
            
        if self.end_date and today > self.end_date:
            return {'label': 'منتهي (انتهى التاريخ)', 'class': 'warning', 'icon': 'calendar-times'}
            
        return {'label': 'نشط ومتاح حالياً', 'class': 'success', 'icon': 'check-circle'}


class SurveyQuestion(models.Model):
    """أسئلة الاستبيان"""
    QUESTION_TYPES = [
        ('rating', 'تقييم (1-5)'),
        ('text', 'نص حر'),
        ('choice', 'اختيار من متعدد (راديو)'),
        ('checkbox', 'اختيارات متعددة (صندوق اختيار)'),
        ('select', 'قائمة منسدلة'),
        ('number', 'رقم'),
        ('date', 'تاريخ'),
        ('yesno', 'نعم/لا'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500, verbose_name='نص السؤال')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name='نوع السؤال')
    choices = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='الخيارات',
        help_text='ادخل الخيارات (خيار واحد في كل سطر). سيتم استخدامها في أسئلة الاختيار من متعدد.'
    )
    is_required = models.BooleanField(default=True, verbose_name='مطلوب')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'سؤال استبيان'
        verbose_name_plural = 'أسئلة الاستبيان'
        ordering = ['order']

    def __str__(self):
        return f"{self.survey.title}: {self.question_text[:50]}"


class SurveyResponse(TimeStampedModel):
    """ردود الاستبيان"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='survey_responses'
    )
    answers = models.JSONField(default=dict, verbose_name='الإجابات')
    # مثال: {"1": "5", "2": "نص الإجابة", "3": "الخيار الثاني"}

    class Meta:
        verbose_name = 'رد استبيان'
        verbose_name_plural = 'ردود الاستبيانات'
        unique_together = ('survey', 'user')  # رد واحد لكل مستخدم

    def __str__(self):
        return f"Response to {self.survey.title} by {self.user}"
