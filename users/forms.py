from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Field
from .models import PartnerProfile, User, Role, Interest
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


class VisitorSignUpForm(UserCreationForm):
    """نموذج تسجيل حساب سائح جديد"""
    
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': _('example@email.com'),
            'class': 'form-control',
            'dir': 'ltr',
        })
    )


    
    # الموافقة على الشروط
    terms_accepted = forms.BooleanField(
        label=_('أوافق على شروط الاستخدام وسياسة الخصوصية'),
        required=True,
        error_messages={
            'required': _('يجب الموافقة على شروط الاستخدام للمتابعة')
        }
    )


    class Meta(UserCreationForm.Meta):
        
        model = User
        fields = ('username', 'email')
        labels = {
            'username': _('اسم المستخدم'),
        }
        help_texts = {
            'username': _('أحرف إنجليزية وأرقام و _ فقط'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Arabic labels for password fields
        self.fields['password1'].label = _('كلمة المرور')
        self.fields['password1'].help_text = _('6 أحرف على الأقل')
        self.fields['password2'].label = _('تأكيد كلمة المرور')
        self.fields['password2'].help_text = _('أدخل نفس كلمة المرور مرة أخرى')
        
        # Apply username validator
        self.fields['username'].validators.append(username_regex)
        
        # Form helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'email',

            'password1',
            'password2',
            'terms_accepted',
            Submit('submit', _('إنشاء حساب سائح'), css_class='btn btn-primary w-100 mt-3 rounded-pill fw-bold')
        )

    def clean_email(self):
        """التحقق من عدم تكرار البريد الإلكتروني"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('هذا البريد الإلكتروني مستخدم بالفعل.'))
        return email.lower()



    def save(self, commit=True):
        user = super().save(commit=False)
        # Set full_name to username if empty, or blank
        user.full_name = self.cleaned_data.get('username', '')
        user.email = self.cleaned_data['email']

        user.account_status = 'active'  # تفعيل فوري للسائح
        
        # تعيين دور السائح
        tourist_role, _ = Role.objects.get_or_create(name='tourist')
        user.role = tourist_role
        
        if commit:
            user.save()
        return user

class PartnerProfileForm(forms.ModelForm):
    # Add User fields we want to edit together
    full_name = forms.CharField(label="Full Name", required=False)
    phone_number = forms.CharField(label="Phone Number", required=False)
    bio = forms.CharField(label="Bio", widget=forms.Textarea(attrs={'rows': 3}), required=False)
    profile_image = forms.ImageField(label="Profile Picture", required=False)
    cover_image = forms.ImageField(label="Cover Image", required=False)

    class Meta:
        model = PartnerProfile
        fields = ['organization_name', 'commercial_reg_no', 'id_card_image']
        help_texts = {
            'commercial_reg_no': 'Your official business registration number.',
            'id_card_image': 'Upload a copy of your ID for verification.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['full_name'].initial = user.full_name
            self.fields['phone_number'].initial = user.phone_number
            self.fields['bio'].initial = user.bio
            self.fields['profile_image'].initial = user.profile_image
            self.fields['cover_image'].initial = user.cover_image

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<h4>Personal Information</h4>"),
            Row(
                Column('full_name', css_class='form-group col-md-6 mb-0'),
                Column('phone_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'bio',
            Row(
                Column('profile_image', css_class='form-group col-md-6 mb-0'),
                Column('cover_image', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            HTML("<hr><h4>Business Details</h4>"),
            'organization_name',
            Row(
                Column('commercial_reg_no', css_class='form-group col-md-6 mb-0'),
                Column('id_card_image', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Update Profile', css_class='btn btn-primary mt-3')
        )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        from management.services.moderation_service import analyze_text
        result = analyze_text(full_name)
        if result.action == 'block':
            raise forms.ValidationError(_("يحتوي الاسم الكامل على كلمات محظورة."))
        return full_name

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio:
            from management.services.moderation_service import analyze_text
            result = analyze_text(bio)
            if result.action == 'block':
                raise forms.ValidationError(_("تحتوي النبذة التعريفية على كلمات محظورة."))
        return bio

    def save(self, commit=True):
        partner_profile = super().save(commit=False)
        if commit:
            partner_profile.save()
            # Save User fields
            user = partner_profile.user
            user.full_name = self.cleaned_data['full_name']
            user.phone_number = self.cleaned_data['phone_number']
            user.bio = self.cleaned_data['bio']
            if self.cleaned_data['profile_image']:
                user.profile_image = self.cleaned_data['profile_image']
            if self.cleaned_data['cover_image']:
                user.cover_image = self.cleaned_data['cover_image']
            user.save()
        return partner_profile

class UserUpdateForm(forms.ModelForm):
    full_name = forms.CharField(label=_("الاسم الكامل"), required=True)
    phone_number = forms.CharField(label="رقم الهاتف", required=False)
    bio = forms.CharField(label="نبذة تعريفية", widget=forms.Textarea(attrs={'rows': 3}), required=False)
    profile_image = forms.ImageField(label="الصورة الشخصية", required=False)
    cover_image = forms.ImageField(label="صورة الغلاف", required=False)

    interests = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("الاهتمامات")
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'bio', 'profile_image', 'cover_image', 'interests']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'full_name',
            'phone_number',
            'bio',
            HTML('<h5 class="mt-3 mb-2">الاهتمامات</h5>'),
            'interests',
            Row(
                Column('profile_image', css_class='form-group col-md-6 mb-0'),
                Column('cover_image', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'حفظ التغييرات', css_class='btn btn-primary w-100 mt-3 rounded-pill fw-bold')
        )

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        from management.services.moderation_service import analyze_text
        result = analyze_text(full_name)
        if result.action == 'block':
            raise forms.ValidationError(_("يحتوي الاسم الكامل على كلمات محظورة."))
        return full_name

    def clean_bio(self):
        bio = self.cleaned_data.get('bio')
        if bio:
            from management.services.moderation_service import analyze_text
            result = analyze_text(bio)
            if result.action == 'block':
                raise forms.ValidationError(_("تحتوي النبذة التعريفية على كلمات محظورة."))
        return bio

