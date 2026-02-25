from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from .models import User, Role, PartnerProfile
import re

# Phone number validator
phone_regex = RegexValidator(
    regex=r'^(\+967|00967|0)?[7][0-9]{8}$',
    message=_('أدخل رقم هاتف يمني صحيح (مثال: 771234567)')
)

# Username validator - English letters, numbers, underscore only
username_regex = RegexValidator(
    regex=r'^[a-zA-Z0-9_]+$',
    message=_('اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط')
)


class PartnerSignUpForm(UserCreationForm):
    """نموذج تسجيل حساب شريك تجاري جديد"""
    
    # بيانات المستخدم
    full_name = forms.CharField(
        label=_("الاسم الكامل"),
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': _('أدخل اسمك الكامل'),
            'class': 'form-control',
        })
    )
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': _('example@email.com'),
            'class': 'form-control',
            'dir': 'ltr',
        })
    )
    phone_number = forms.CharField(
        label=_("رقم الهاتف"),
        required=True,
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'placeholder': _('771234567'),
            'class': 'form-control',
            'dir': 'ltr',
        })
    )
    
    # بيانات الشريك التجاري
    commercial_reg_no = forms.CharField(
        label=_("رقم السجل التجاري"),
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': _('أدخل رقم السجل التجاري'),
            'class': 'form-control',
            'dir': 'ltr',
        })
    )
    id_card_image = forms.ImageField(
        label=_("صورة الهوية الشخصية"),
        required=True,
        help_text=_('ارفع صورة واضحة للهوية للتحقق من هويتك')
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'full_name', 'phone_number')
        labels = {
            'username': _('اسم المستخدم'),
        }
        help_texts = {
            'username': _('أحرف إنجليزية وأرقام و _ فقط'),
        }
    
    terms_accepted = forms.BooleanField(
        label=_('أوافق على شروط الاستخدام وسياسة الخصوصية'),
        required=True,
        error_messages={
            'required': _('يجب الموافقة على شروط الاستخدام للمتابعة')
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Arabic labels for password fields
        self.fields['password1'].label = _('كلمة المرور')
        self.fields['password1'].help_text = _('8 أحرف على الأقل')
        self.fields['password2'].label = _('تأكيد كلمة المرور')
        
        # Apply username validator
        self.fields['username'].validators.append(username_regex)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3"><i class="fas fa-user me-2"></i>' + str(_('البيانات الشخصية')) + '</h5>'),
            'username',
            Row(
                Column('full_name', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'email',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<hr><h5 class="mb-3"><i class="fas fa-briefcase me-2"></i>' + str(_('بيانات النشاط التجاري')) + '</h5>'),
            Row(
                Column('commercial_reg_no', css_class='form-group col-md-6 mb-3'),
                Column('id_card_image', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<div class="form-check my-3">'),
            'terms_accepted',
            HTML('</div>'),
            Submit('submit', _('تقديم طلب الشراكة'), css_class='btn btn-success w-100 mt-3 rounded-pill fw-bold')
        )

    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل.'))
        return email.lower()

    def clean_phone_number(self):
        """التحقق من عدم تكرار رقم الهاتف"""
        phone = self.cleaned_data.get('phone_number')
        phone = re.sub(r'^(\+967|00967|0)', '', phone)
        
        if User.objects.filter(phone_number__icontains=phone).exists():
            raise forms.ValidationError(_('رقم الهاتف هذا مستخدم بالفعل.'))
        return phone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        from management.services.moderation_service import analyze_text
        result = analyze_text(username)
        if result.action == 'block':
            raise forms.ValidationError(_("يحتوي اسم المستخدم على كلمات محظورة."))
        return username

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        from management.services.moderation_service import analyze_text
        result = analyze_text(full_name)
        if result.action == 'block':
            raise forms.ValidationError(_("يحتوي الاسم الكامل على كلمات محظورة."))
        return full_name

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.account_status = 'pending'  # حالة قيد المراجعة
        
        if commit:
            user.save()
            
            # تعيين دور الشريك
            partner_role, _ = Role.objects.get_or_create(name='Partner')
            user.role = partner_role
            user.save()
            
            # إنشاء ملف الشريك
            from django.utils import timezone
            PartnerProfile.objects.create(
                user=user,
                commercial_reg_no=self.cleaned_data.get('commercial_reg_no', ''),
                id_card_image=self.cleaned_data.get('id_card_image'),
                status='pending',  # قيد المراجعة
                is_approved=False,
                submitted_at=timezone.now()  # Fix Gap 1: Set submission time
            )
            
        return user


class TouristUpgradeForm(forms.ModelForm):
    # PartnerProfile fields
    organization_name = forms.CharField(
        label=_("اسم المنظمة/النشاط"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    commercial_reg_no = forms.CharField(
        label=_("رقم السجل التجاري"), 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    commercial_registry_file = forms.FileField(
        label=_("ملف السجل التجاري"),
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'})
    )
    id_card_image = forms.ImageField(
        label=_("صورة الهوية الشخصية"), 
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['full_name', 'phone_number']
        labels = {
            'full_name': _('الاسم الكامل'),
            'phone_number': _('رقم الهاتف'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h5 class="mb-3 text-muted">بيانات مقدم الطلب</h5>'),
            Row(
                Column('full_name', css_class='form-group col-md-6 mb-3'),
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<hr><h5 class="mb-3 text-muted">وثائق الشراكة</h5>'),
            Row(
                Column('organization_name', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('commercial_reg_no', css_class='form-group col-md-6 mb-3'),
                Column('commercial_registry_file', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('id_card_image', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
            Submit('submit', 'إرسال طلب الترقية', css_class='btn btn-success w-100 mt-3 rounded-pill fw-bold')
        )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        from management.services.moderation_service import analyze_text
        result = analyze_text(full_name)
        if result.action == 'block':
            raise forms.ValidationError(_("يحتوي الاسم الكامل على كلمات محظورة."))
        return full_name

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            
            # Update Role to Partner if not already
            partner_role, _ = Role.objects.get_or_create(name='Partner')
            if user.role != partner_role:
                user.role = partner_role
                user.save()
            
            # Create OR UPDATE PartnerProfile
            # We must update fields in case this is a re-submission after rejection
            defaults = {
                'organization_name': self.cleaned_data.get('organization_name'),
                'commercial_reg_no': self.cleaned_data.get('commercial_reg_no'),
                'status': 'pending', # Reset to pending
                'is_approved': False,
                'rejection_reason': '' # Clear rejection reason
            }
            
            profile, created = PartnerProfile.objects.update_or_create(
                user=user,
                defaults=defaults
            )
            
            # Handle Image/File Uploads
            if self.cleaned_data.get('id_card_image'):
                profile.id_card_image = self.cleaned_data['id_card_image']
            
            if self.cleaned_data.get('commercial_registry_file'):
                profile.commercial_registry_file = self.cleaned_data['commercial_registry_file']
            
            profile.save()

        return user

