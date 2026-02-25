"""
نموذج تسجيل الدخول الموحد مع دعم اللغة العربية
Unified Login Form with Arabic support
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class UnifiedLoginForm(AuthenticationForm):
    """
    نموذج تسجيل دخول موحد لجميع المستخدمين
    يدعم تسجيل الدخول بالبريد الإلكتروني أو اسم المستخدم
    """
    
    username = forms.CharField(
        label=_("اسم المستخدم أو البريد الإلكتروني"),
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل اسم المستخدم أو البريد الإلكتروني'),
            'autofocus': True,
            'autocomplete': 'username',
            'dir': 'auto',
        })
    )
    
    password = forms.CharField(
        label=_("كلمة المرور"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل كلمة المرور'),
            'autocomplete': 'current-password',
        })
    )

    error_messages = {
        'invalid_login': _(
            "بيانات تسجيل الدخول غير صحيحة. "
            "تأكد من اسم المستخدم/البريد الإلكتروني وكلمة المرور."
        ),
        'inactive': _("هذا الحساب غير مفعل."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة CSS classes للوضع الليلي
        for field in self.fields.values():
            if 'class' in field.widget.attrs:
                field.widget.attrs['class'] += ' rounded-3'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Check if input is email
            if '@' in username:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(email__iexact=username)
                    # Swap email for username to let ModelBackend handle auth
                    self.cleaned_data['username'] = user.username
                except User.DoesNotExist:
                    # Let default auth fail
                    pass
        
        return super().clean()
