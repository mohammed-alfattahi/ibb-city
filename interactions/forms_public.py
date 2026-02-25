from django import forms
from .models import Review, Report

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': 'التقييم',
            'comment': 'تعليقك',
        }
        widgets = {
            # We'll use a custom star widget in HTML, but here we define the select/radio
            'rating': forms.RadioSelect(attrs={'class': 'star-rating-input'}), 
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'شاركنا تجربتك... ما الذي أعجبك؟'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'description', 'proof_image']
        labels = {
            'report_type': 'نوع البلاغ',
            'description': 'وصف المشكلة',
            'proof_image': 'صورة إثبات (اختياري)',
        }
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'يرجى تقديم تفاصيل إضافية لتساعدنا في التحقق...'}),
            'proof_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
