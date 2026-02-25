from django import forms
from django.core.exceptions import ValidationError
from .models import Advertisement
from places.models import Establishment
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML

class AdvertisementForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="تاريخ بدء الإعلان"
    )
    
    class Meta:
        model = Advertisement
        fields = ['title', 'description', 'place', 'target_url', 'placement', 'banner_image', 'price', 'discount_price', 'duration_days', 'start_date']
        labels = {
            'title': 'عنوان العرض / الخدمة',
            'description': 'التفاصيل والمميزات',
            'place': 'المنشأة المقدمة للعرض',
            'target_url': 'رابط التحويل (اختياري)',
            'placement': 'مكان ظهور الإعلان',
            'banner_image': 'صورة العرض (يفضل تصميم جذاب)',
            'price': 'السعر الأساسي (ر.ي)',
            'discount_price': 'سعر العرض (بعد الخصم) - اختياري',
            'duration_days': 'مدة العرض (أيام)',
        }
        help_texts = {
            'banner_image': 'يفضل مقاس 1200×600 بكسل.',
            'target_url': 'يمكنك إدخال رابط خارجي بدلًا من صفحة المنشأة.',
            'discount_price': 'اتركه فارغاً إذا لم يوجد خصم.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Allow advertising for all owner's establishments (approved, pending, or draft)
            self.fields['place'].queryset = Establishment.objects.filter(
                owner=user,
                approval_status__in=['approved', 'pending', 'draft'],
                is_active=True
            ).order_by('name')
        
        self.fields['place'].required = False
        self.fields['target_url'].required = False

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            'target_url',
            Row(
                Column('price', css_class='form-group col-md-6 mb-0'),
                Column('discount_price', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'placement',
            'place',
            'banner_image',
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('duration_days', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'تأكيد الدفع وإرسال للمراجعة', css_class='btn btn-success w-100 mt-3 rounded-pill fw-bold')
        )

    def clean(self):
        cleaned_data = super().clean()
        place = cleaned_data.get('place')
        target_url = cleaned_data.get('target_url')
        if not place and not target_url:
            raise ValidationError('Select a place or enter a target URL.')
        return cleaned_data


class PaymentProofForm(forms.ModelForm):
    receipt_image = forms.ImageField(required=True, label='صورة سند التحويل')
    transaction_reference = forms.CharField(required=True, label='رقم العملية المرجعي')

    class Meta:
        model = Advertisement
        fields = ['receipt_image', 'transaction_reference']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'receipt_image',
            'transaction_reference',
            Submit('submit', 'تأكيد الدفع وإرسال للمراجعة', css_class='btn btn-success w-100 mt-3 rounded-pill fw-bold')
        )

class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV File')
