# 📖 شرح تفصيلي سطر بسطر لملفات Django

> **Line-by-Line Django Files Explanation**
>
> تطبيق المستخدمين (users) - دليل إب السياحي

---

## 📋 فهرس الملفات

1. [models.py - النماذج](#1-modelspy---النماذج)
2. [views.py - العروض](#2-viewspy---العروض)
3. [forms.py - نماذج الإدخال](#3-formspy---نماذج-الإدخال)
4. [admin.py - لوحة الإدارة](#4-adminpy---لوحة-الإدارة)
5. [urls.py - المسارات](#5-urlspy---المسارات)
6. [signals.py - الإشارات](#6-signalspy---الإشارات)
7. [email_service.py - خدمة البريد](#7-email_servicepy---خدمة-البريد)

---

# 1. models.py - النماذج

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات (Imports)
# ═══════════════════════════════════════════════════════════════════════

from django.db import models
# ↑ استيراد وحدة models من Django للتعامل مع قاعدة البيانات
# models تحتوي على كل الأدوات لإنشاء جداول قاعدة البيانات

from django.contrib.auth.models import AbstractUser
# ↑ استيراد AbstractUser: نموذج مستخدم جاهز من Django
# يحتوي على: username, password, email, is_active, is_staff, etc.
# نرث منه لإضافة حقول مخصصة

from django.utils.translation import gettext_lazy as _
# ↑ استيراد دالة الترجمة gettext_lazy
# _('نص') = يجعل النص قابل للترجمة لاحقاً
# lazy = الترجمة تحدث عند العرض وليس عند التحميل

from ibb_guide.base_models import TimeStampedModel
# ↑ استيراد نموذج أساسي مخصص يضيف:
# - created_at: تاريخ الإنشاء
# - updated_at: تاريخ آخر تحديث

# ═══════════════════════════════════════════════════════════════════════
# نموذج الدور (Role Model)
# ═══════════════════════════════════════════════════════════════════════

class Role(models.Model):
    # ↑ تعريف كلاس Role يرث من models.Model
    # models.Model = الكلاس الأساسي لكل النماذج في Django
    # Django سينشئ جدول اسمه: users_role

    name = models.CharField(max_length=50, unique=True)
    # ↑ حقل نصي للاسم
    # CharField = حقل نصي محدود الطول
    # max_length=50 = أقصى طول 50 حرف
    # unique=True = لا يمكن تكرار نفس الاسم

    description = models.TextField(blank=True)
    # ↑ حقل نصي طويل للوصف
    # TextField = حقل نصي غير محدود الطول
    # blank=True = يمكن تركه فارغاً في الفورم

    permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        verbose_name=_('الصلاحيات')
    )
    # ↑ علاقة متعدد-لمتعدد مع جدول الصلاحيات
    # ManyToManyField = علاقة M:N (دور واحد له صلاحيات متعددة)
    # 'auth.Permission' = جدول الصلاحيات الموجود في Django
    # verbose_name = الاسم الذي يظهر في الأدمن

    class Meta:
        # ↑ كلاس داخلي لإعدادات النموذج
        verbose_name = _('دور')
        verbose_name_plural = _('الأدوار')
        # ↑ الأسماء التي تظهر في لوحة الإدارة

    def __str__(self):
        return self.name
        # ↑ الدالة التي تحدد كيف يُعرض الكائن كنص
        # مثال: print(role) → "مدير"

# ═══════════════════════════════════════════════════════════════════════
# نموذج المستخدم (User Model)
# ═══════════════════════════════════════════════════════════════════════

class User(AbstractUser):
    # ↑ نموذج المستخدم يرث من AbstractUser
    # AbstractUser يعطينا: username, password, email, first_name, last_name
    # is_active, is_staff, is_superuser, date_joined, last_login

    # --- خيارات حالة الحساب ---
    ACCOUNT_STATUS_CHOICES = [
        ('active', _('نشط')),
        ('pending', _('قيد المراجعة')),
        ('rejected', _('مرفوض')),
        ('suspended', _('موقوف')),
    ]
    # ↑ قائمة الخيارات لحقل account_status
    # كل خيار = (القيمة_المحفوظة, النص_المعروض)
    # 'active' يُحفظ في قاعدة البيانات
    # _('نشط') يظهر للمستخدم

    # --- الحقول المخصصة ---

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الدور')
    )
    # ↑ مفتاح أجنبي يربط المستخدم بدور
    # ForeignKey = علاقة N:1 (مستخدمين كثر لدور واحد)
    # on_delete=SET_NULL = إذا حُذف الدور، اجعل القيمة NULL
    # null=True = يسمح بـ NULL في قاعدة البيانات
    # blank=True = يسمح بتركه فارغاً في الفورم

    full_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('الاسم الكامل')
    )
    # ↑ حقل الاسم الكامل

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('رقم الهاتف')
    )
    # ↑ حقل رقم الهاتف

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name=_('صورة الملف الشخصي')
    )
    # ↑ حقل صورة
    # ImageField = حقل خاص بالصور (يتطلب Pillow)
    # upload_to = المجلد الذي ستُرفع إليه الصور
    # الصور ستُحفظ في: media/profile_images/

    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_('نبذة تعريفية')
    )
    # ↑ حقل النبذة التعريفية

    interests = models.ManyToManyField(
        'Interest',
        blank=True,
        verbose_name=_('الاهتمامات')
    )
    # ↑ علاقة M:N مع الاهتمامات
    # يمكن للمستخدم أن يكون له اهتمامات متعددة

    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='pending',
        verbose_name=_('حالة الحساب')
    )
    # ↑ حقل حالة الحساب
    # choices = قائمة الخيارات المسموحة
    # default = القيمة الافتراضية عند الإنشاء

    # --- حقول التحقق من الإيميل ---

    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('رمز التحقق')
    )
    # ↑ رمز التحقق (64 حرف عشوائي)

    email_verification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('تاريخ إرسال التحقق')
    )
    # ↑ تاريخ ووقت إرسال رسالة التحقق
    # DateTimeField = حقل تاريخ + وقت

    # --- حقل الإشعارات ---

    fcm_token = models.TextField(blank=True, null=True)
    # ↑ رمز Firebase Cloud Messaging للإشعارات

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.username

    @property
    def is_partner(self):
        """هل المستخدم شريك؟"""
        return hasattr(self, 'partner_profile')
        # ↑ @property = تحويل الدالة لخاصية (تُستدعى بدون أقواس)
        # hasattr = يتحقق إذا كان للمستخدم partner_profile
        # user.is_partner → True أو False

    @property
    def is_approved_partner(self):
        """هل المستخدم شريك معتمد؟"""
        return (
            hasattr(self, 'partner_profile') and
            self.partner_profile.is_approved
        )
        # ↑ يتحقق من وجود ملف شريك + الموافقة عليه

# ═══════════════════════════════════════════════════════════════════════
# نموذج ملف الشريك (PartnerProfile Model)
# ═══════════════════════════════════════════════════════════════════════

class PartnerProfile(TimeStampedModel):
    # ↑ يرث من TimeStampedModel
    # يعطينا تلقائياً: created_at, updated_at

    PARTNER_STATUS_CHOICES = [
        ('pending', _('قيد المراجعة')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
        ('info_requested', _('طلب معلومات')),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='partner_profile'
    )
    # ↑ علاقة واحد-لواحد مع المستخدم
    # OneToOneField = علاقة 1:1 (كل مستخدم له ملف شريك واحد فقط)
    # CASCADE = إذا حُذف المستخدم، يُحذف ملف الشريك
    # related_name = اسم العلاقة العكسية
    # user.partner_profile → الوصول لملف الشريك

    organization_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('اسم المنظمة/النشاط')
    )

    commercial_reg_no = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('رقم السجل التجاري')
    )

    id_card_image = models.ImageField(
        upload_to='partners/id_cards/',
        blank=True,
        null=True,
        verbose_name=_('صورة البطاقة الشخصية')
    )

    commercial_registry_file = models.FileField(
        upload_to='partners/registries/',
        blank=True,
        null=True,
        verbose_name=_('السجل التجاري')
    )
    # ↑ FileField = حقل رفع ملفات (PDF, Word, etc.)

    status = models.CharField(
        max_length=20,
        choices=PARTNER_STATUS_CHOICES,
        default='pending',
        verbose_name=_('حالة الطلب')
    )

    is_approved = models.BooleanField(default=False)
    # ↑ BooleanField = حقل نعم/لا (True/False)

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('سبب الرفض')
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_partner_profiles'
    )
    # ↑ المستخدم الذي راجع الطلب (أدمن)
    # related_name مختلف لأن User له علاقتين مع هذا النموذج

    reviewed_at = models.DateTimeField(null=True, blank=True)
    # ↑ تاريخ المراجعة

# ═══════════════════════════════════════════════════════════════════════
# نموذج الاهتمامات (Interest Model)
# ═══════════════════════════════════════════════════════════════════════

class Interest(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('FontAwesome class مثل: fa-hiking')
    )
    # ↑ help_text = نص مساعد يظهر تحت الحقل في الفورم

    def __str__(self):
        return self.name
```

---

# 2. views.py - العروض

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from django.shortcuts import render, redirect, get_object_or_404
# render = دالة لعرض قالب HTML
# redirect = دالة لإعادة التوجيه لصفحة أخرى
# get_object_or_404 = جلب كائن أو إظهار صفحة 404

from django.views.generic import CreateView, UpdateView, TemplateView
# CreateView = عرض لإنشاء كائن جديد
# UpdateView = عرض لتحديث كائن موجود
# TemplateView = عرض بسيط لعرض قالب

from django.contrib.auth import login, logout
# login = دالة لتسجيل دخول المستخدم
# logout = دالة لتسجيل خروج المستخدم

from django.contrib.auth.mixins import LoginRequiredMixin
# LoginRequiredMixin = خلطة تتطلب تسجيل الدخول

from django.contrib import messages
# messages = نظام الرسائل المؤقتة (success, error, warning)

from django.urls import reverse_lazy
# reverse_lazy = الحصول على URL من اسمه (للاستخدام في الكلاسات)

from .models import User
from .forms import VisitorSignUpForm

# ═══════════════════════════════════════════════════════════════════════
# عرض تسجيل الزائر
# ═══════════════════════════════════════════════════════════════════════

class VisitorSignUpView(CreateView):
    # ↑ عرض مبني على CreateView
    # CreateView يوفر: GET (عرض الفورم), POST (معالجة البيانات)

    model = User
    # ↑ النموذج الذي سيُنشأ منه كائن جديد

    form_class = VisitorSignUpForm
    # ↑ كلاس الفورم المستخدم

    template_name = 'users/signup.html'
    # ↑ مسار قالب HTML

    success_url = reverse_lazy('users:verification_sent')
    # ↑ الصفحة التي يُوجه إليها بعد النجاح
    # reverse_lazy = يحسب الـ URL لاحقاً (ليس فوراً)

    def form_valid(self, form):
        # ↑ تُستدعى عندما يكون الفورم صحيحاً
        # form = الفورم مع البيانات الصحيحة

        user = form.save(commit=False)
        # ↑ إنشاء كائن User بدون حفظه في قاعدة البيانات
        # commit=False = لا تحفظ الآن، سنضيف بيانات أولاً

        user.account_status = 'pending'
        # ↑ تعيين حالة الحساب كـ "قيد المراجعة"

        user.is_active = False
        # ↑ الحساب غير نشط حتى التحقق من الإيميل

        user.save()
        # ↑ الآن نحفظ في قاعدة البيانات

        # إرسال إيميل التحقق
        from .email_service import send_verification_email
        send_verification_email(user, self.request)
        # ↑ استدعاء دالة إرسال الإيميل

        messages.success(
            self.request,
            _('تم إنشاء حسابك! يرجى التحقق من بريدك الإلكتروني.')
        )
        # ↑ إضافة رسالة نجاح تظهر في الصفحة التالية

        return redirect(self.success_url)
        # ↑ إعادة التوجيه لصفحة النجاح

# ═══════════════════════════════════════════════════════════════════════
# عرض تسجيل الدخول الموحد
# ═══════════════════════════════════════════════════════════════════════

from django.views import View
from django.contrib.auth import authenticate
from .forms_login import UnifiedLoginForm

class UnifiedLoginView(View):
    # ↑ عرض مبني على View الأساسي
    # يجب تعريف get() و post() يدوياً

    template_name = 'users/login.html'

    def get(self, request):
        # ↑ عند طلب GET (فتح الصفحة)

        if request.user.is_authenticated:
            return redirect('home')
        # ↑ إذا المستخدم مسجل دخوله، وجهه للرئيسية

        form = UnifiedLoginForm()
        # ↑ إنشاء فورم فارغ

        return render(request, self.template_name, {'form': form})
        # ↑ عرض القالب مع الفورم

    def post(self, request):
        # ↑ عند طلب POST (إرسال الفورم)

        form = UnifiedLoginForm(request.POST)
        # ↑ إنشاء فورم مع البيانات المرسلة

        if form.is_valid():
            # ↑ التحقق من صحة البيانات

            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            # ↑ cleaned_data = البيانات النظيفة بعد التحقق

            user = authenticate(
                request,
                username=username_or_email,
                password=password
            )
            # ↑ محاولة المصادقة
            # authenticate = يتحقق من صحة البيانات
            # يرجع User إذا صحيحة، None إذا خاطئة

            if user is not None:
                if user.is_active:
                    login(request, user)
                    # ↑ تسجيل دخول المستخدم

                    messages.success(request, _('مرحباً بك!'))

                    next_url = request.GET.get('next', 'home')
                    # ↑ الصفحة التي كان يريد الوصول إليها
                    # أو 'home' إذا لم توجد

                    return redirect(next_url)
                else:
                    messages.error(
                        request,
                        _('حسابك غير مفعل. يرجى التحقق من إيميلك.')
                    )
            else:
                messages.error(
                    request,
                    _('بيانات الدخول غير صحيحة.')
                )

        return render(request, self.template_name, {'form': form})

# ═══════════════════════════════════════════════════════════════════════
# عرض الملف الشخصي
# ═══════════════════════════════════════════════════════════════════════

class UserProfileView(LoginRequiredMixin, UpdateView):
    # ↑ LoginRequiredMixin = يتطلب تسجيل الدخول
    # إذا لم يكن مسجلاً، يُوجه لصفحة الدخول

    model = User
    form_class = UserUpdateForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        # ↑ تحديد الكائن الذي سيُعدل
        return self.request.user
        # ↑ المستخدم الحالي

    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث ملفك الشخصي بنجاح!'))
        return super().form_valid(form)
        # ↑ super() = استدعاء الدالة الأصلية من الكلاس الأب

# ═══════════════════════════════════════════════════════════════════════
# عرض التحقق من الإيميل
# ═══════════════════════════════════════════════════════════════════════

class EmailVerificationView(View):

    def get(self, request, token):
        # ↑ token = الرمز من الـ URL
        # مثال: /verify/abc123def456/

        try:
            user = User.objects.get(email_verification_token=token)
            # ↑ البحث عن مستخدم برمز التحقق هذا
            # objects = مدير النموذج (Model Manager)
            # get() = جلب كائن واحد

            user.is_active = True
            user.account_status = 'active'
            user.email_verification_token = ''
            # ↑ مسح الرمز بعد الاستخدام

            user.save()
            # ↑ حفظ التغييرات

            messages.success(request, _('تم تفعيل حسابك بنجاح!'))
            return redirect('users:login')

        except User.DoesNotExist:
            # ↑ إذا لم يوجد مستخدم بهذا الرمز
            messages.error(request, _('رابط التحقق غير صالح.'))
            return redirect('home')
```

---

# 3. forms.py - نماذج الإدخال

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from django import forms
# ↑ استيراد وحدة الفورمات من Django

from django.contrib.auth.forms import UserCreationForm
# ↑ فورم جاهز لإنشاء مستخدمين (يتضمن التحقق من كلمة المرور)

from .models import User, PartnerProfile

# ═══════════════════════════════════════════════════════════════════════
# فورم تسجيل الزائر
# ═══════════════════════════════════════════════════════════════════════

class VisitorSignUpForm(UserCreationForm):
    # ↑ يرث من UserCreationForm
    # يعطينا: password1, password2 (مع التحقق من التطابق)

    email = forms.EmailField(
        required=True,
        label=_('البريد الإلكتروني'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    # ↑ تعريف حقل الإيميل
    # EmailField = حقل إيميل (يتحقق من الصيغة)
    # required=True = إلزامي
    # label = العنوان الذي يظهر
    # widget = تحديد نوع عنصر HTML
    # attrs = خصائص HTML إضافية

    full_name = forms.CharField(
        max_length=100,
        required=True,
        label=_('الاسم الكامل'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسمك الكامل'
        })
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label=_('رقم الهاتف'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '777123456'
        })
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label=_('أوافق على الشروط والأحكام')
    )
    # ↑ خانة اختيار (checkbox)
    # required=True = يجب الموافقة للمتابعة

    class Meta:
        # ↑ إعدادات الفورم
        model = User
        # ↑ النموذج المرتبط

        fields = ['username', 'email', 'full_name', 'phone_number',
                  'password1', 'password2', 'terms_accepted']
        # ↑ الحقول المضمنة في الفورم

    def clean_email(self):
        # ↑ دالة تحقق مخصصة لحقل email
        # clean_<field_name> = تُستدعى تلقائياً

        email = self.cleaned_data.get('email')
        # ↑ جلب قيمة الإيميل

        if User.objects.filter(email=email).exists():
            # ↑ التحقق إذا الإيميل موجود مسبقاً
            # filter() = بحث مع شروط
            # exists() = هل توجد نتائج؟

            raise forms.ValidationError(_('هذا البريد مسجل مسبقاً'))
            # ↑ رمي خطأ تحقق

        return email
        # ↑ إرجاع القيمة النظيفة

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # إزالة المسافات والأحرف غير الرقمية
            phone = ''.join(filter(str.isdigit, phone))
            # ↑ filter = إبقاء الأرقام فقط
        return phone

    def save(self, commit=True):
        # ↑ تخصيص عملية الحفظ

        user = super().save(commit=False)
        # ↑ إنشاء الكائن بدون حفظ

        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        # ↑ تعيين الحقول الإضافية

        if commit:
            user.save()

        return user

# ═══════════════════════════════════════════════════════════════════════
# فورم تحديث الملف الشخصي
# ═══════════════════════════════════════════════════════════════════════

class UserUpdateForm(forms.ModelForm):
    # ↑ ModelForm = فورم مبني على نموذج
    # يُنشئ الحقول تلقائياً من النموذج

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number',
                  'profile_image', 'bio', 'interests']
        # ↑ الحقول القابلة للتعديل

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'interests': forms.CheckboxSelectMultiple(),
            # ↑ عرض الاهتمامات كـ checkboxes متعددة
        }
        # ↑ تخصيص عناصر HTML
```

---

# 4. admin.py - لوحة الإدارة

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from django.contrib import admin
# ↑ وحدة الإدارة

from django.contrib.auth.admin import UserAdmin
# ↑ كلاس الإدارة الجاهز للمستخدمين

from django.utils.html import format_html
# ↑ لإنشاء HTML آمن

from .models import User, PartnerProfile, Role

# ═══════════════════════════════════════════════════════════════════════
# تسجيل نموذج المستخدم
# ═══════════════════════════════════════════════════════════════════════

@admin.register(User)
# ↑ ديكوريتر لتسجيل النموذج
# بديل عن: admin.site.register(User, CustomUserAdmin)

class CustomUserAdmin(UserAdmin):
    # ↑ يرث من UserAdmin الجاهز

    list_display = ['username', 'full_name', 'email', 'role_badge',
                    'status_badge', 'is_active', 'last_login']
    # ↑ الأعمدة التي تظهر في قائمة المستخدمين
    # يمكن أن تكون أسماء حقول أو دوال

    list_filter = ['is_active', 'is_staff', 'role', 'account_status']
    # ↑ الفلاتر في الشريط الجانبي

    search_fields = ['username', 'full_name', 'email', 'phone_number']
    # ↑ الحقول القابلة للبحث

    ordering = ['-date_joined']
    # ↑ الترتيب الافتراضي (- = تنازلي)

    readonly_fields = ['last_login', 'date_joined',
                       'email_verification_token']
    # ↑ حقول للقراءة فقط

    list_per_page = 20
    # ↑ عدد العناصر في كل صفحة

    actions = ['activate_users', 'deactivate_users']
    # ↑ الإجراءات الجماعية

    def role_badge(self, obj):
        # ↑ دالة لعرض شارة الدور
        # obj = كائن User

        if obj.role:
            return format_html(
                '<span class="badge bg-primary">{}</span>',
                obj.role.name
            )
            # ↑ format_html = إنشاء HTML آمن
        return '-'

    role_badge.short_description = _('الدور')
    # ↑ عنوان العمود

    def status_badge(self, obj):
        colors = {
            'active': 'success',
            'pending': 'warning',
            'rejected': 'danger',
            'suspended': 'secondary'
        }
        color = colors.get(obj.account_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_account_status_display()
            # ↑ get_<field>_display() = الحصول على النص المعروض
        )

    status_badge.short_description = _('الحالة')

    # --- الإجراءات الجماعية ---

    @admin.action(description=_('تفعيل المستخدمين المحددين'))
    # ↑ ديكوريتر لتعريف إجراء
    def activate_users(self, request, queryset):
        # request = الطلب الحالي
        # queryset = المستخدمين المحددين

        updated = queryset.update(is_active=True, account_status='active')
        # ↑ تحديث جماعي
        # update() = تحديث كل العناصر دفعة واحدة

        self.message_user(
            request,
            f'تم تفعيل {updated} مستخدم'
        )
        # ↑ إظهار رسالة للأدمن

# ═══════════════════════════════════════════════════════════════════════
# تسجيل نموذج ملف الشريك
# ═══════════════════════════════════════════════════════════════════════

@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):

    list_display = ['user', 'organization_name', 'status_badge',
                    'is_approved', 'created_at']

    list_filter = ['status', 'is_approved', 'created_at']

    search_fields = ['user__username', 'organization_name',
                     'commercial_reg_no']
    # ↑ user__username = البحث في حقل من علاقة
    # __ = للتنقل بين العلاقات

    actions = ['approve_partners', 'reject_partners']

    def status_badge(self, obj):
        # ... مشابه للسابق
        pass

    @admin.action(description=_('الموافقة على الشركاء المحددين'))
    def approve_partners(self, request, queryset):
        for partner in queryset:
            partner.status = 'approved'
            partner.is_approved = True
            partner.reviewed_by = request.user
            partner.save()

            # تغيير دور المستخدم
            partner_role, _ = Role.objects.get_or_create(name='partner')
            # ↑ get_or_create = جلب أو إنشاء
            # يرجع (object, created) - لذلك نستخدم _

            partner.user.role = partner_role
            partner.user.save()

            # إرسال إشعار
            from interactions.notifications import send_notification
            send_notification(
                partner.user,
                'partner_approved',
                'تمت الموافقة على طلبك!'
            )
```

---

# 5. urls.py - المسارات

```python
from django.urls import path
# ↑ دالة path لتعريف المسارات

from . import views

app_name = 'users'
# ↑ اسم التطبيق (للتسمية المؤهلة)
# يُستخدم: reverse('users:login')

urlpatterns = [
    # --- مسارات المصادقة ---

    path('signup/', views.VisitorSignUpView.as_view(), name='signup'),
    # ↑ path(مسار_URL, العرض, اسم_المسار)
    # as_view() = تحويل الكلاس لدالة عرض
    # name = اسم للاستخدام في reverse()

    path('login/', views.UnifiedLoginView.as_view(), name='login'),

    path('logout/', views.LogoutView.as_view(), name='logout'),

    # --- مسارات التحقق ---

    path('verification-sent/',
         views.VerificationSentView.as_view(),
         name='verification_sent'),

    path('verify/<str:token>/',
         views.EmailVerificationView.as_view(),
         name='verify_email'),
    # ↑ <str:token> = معامل ديناميكي
    # str = نص
    # يُمرر للعرض كـ: token='...'

    path('resend-verification/',
         views.ResendVerificationView.as_view(),
         name='resend_verification'),

    # --- مسارات الملف الشخصي ---

    path('profile/',
         views.UserProfileView.as_view(),
         name='profile'),

    path('settings/',
         views.SettingsView.as_view(),
         name='settings'),

    # --- مسارات الشريك ---

    path('partners/signup/',
         views.PartnerSignUpView.as_view(),
         name='partner_signup'),

    path('partners/profile/edit/',
         views.PartnerProfileUpdateView.as_view(),
         name='partner_profile_edit'),
]
```

---

# 6. signals.py - الإشارات

```python
from django.db.models.signals import post_save
# ↑ إشارة تُطلق بعد حفظ كائن

from django.dispatch import receiver
# ↑ ديكوريتر لاستقبال الإشارات

from django.contrib.auth.models import Group
# ↑ نموذج المجموعات في Django

from .models import User

@receiver(post_save, sender=User)
# ↑ استقبال إشارة post_save من نموذج User
def sync_user_role_to_group(sender, instance, created, **kwargs):
    # sender = النموذج الذي أرسل الإشارة (User)
    # instance = الكائن الذي تم حفظه
    # created = هل هو كائن جديد؟
    # **kwargs = معاملات إضافية

    if instance.role:
        # إذا المستخدم له دور

        group, _ = Group.objects.get_or_create(name=instance.role.name)
        # ↑ إنشاء مجموعة بنفس اسم الدور إذا لم توجد

        instance.groups.clear()
        # ↑ مسح كل المجموعات الحالية

        instance.groups.add(group)
        # ↑ إضافة المستخدم للمجموعة الجديدة
```

---

# 7. email_service.py - خدمة البريد

```python
import secrets
# ↑ مكتبة لتوليد أرقام عشوائية آمنة

from django.core.mail import send_mail
# ↑ دالة إرسال البريد

from django.template.loader import render_to_string
# ↑ تحميل قالب وتحويله لنص

from django.utils import timezone
# ↑ أدوات الوقت

from django.conf import settings
# ↑ إعدادات المشروع

def generate_verification_token():
    """توليد رمز تحقق آمن"""
    return secrets.token_urlsafe(48)
    # ↑ توليد 48 بايت عشوائي بتنسيق URL-safe
    # الناتج حوالي 64 حرف

def send_verification_email(user, request):
    """إرسال إيميل التحقق"""

    # توليد رمز جديد
    token = generate_verification_token()

    # حفظ الرمز في المستخدم
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    # ↑ timezone.now() = الوقت الحالي مع المنطقة الزمنية
    user.save()

    # بناء رابط التحقق
    verification_url = request.build_absolute_uri(
        f'/users/verify/{token}/'
    )
    # ↑ build_absolute_uri = بناء رابط كامل
    # النتيجة: https://example.com/users/verify/token123/

    # تحميل قالب الإيميل
    html_message = render_to_string(
        'users/emails/verification.html',
        {
            'user': user,
            'verification_url': verification_url,
        }
    )
    # ↑ تحويل قالب HTML لنص مع البيانات

    # إرسال الإيميل
    send_mail(
        subject='تأكيد بريدك الإلكتروني - دليل إب',
        message='',  # نص عادي (فارغ لأننا نستخدم HTML)
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
        # ↑ fail_silently=False = أظهر الأخطاء
    )

    return True

def resend_verification_email(user, request):
    """إعادة إرسال إيميل التحقق مع Rate Limiting"""

    from datetime import timedelta

    # التحقق من Rate Limiting
    if user.email_verification_sent_at:
        time_since_last = timezone.now() - user.email_verification_sent_at
        # ↑ الفرق بين الآن وآخر إرسال

        if time_since_last < timedelta(minutes=5):
            # ↑ إذا مر أقل من 5 دقائق
            remaining = timedelta(minutes=5) - time_since_last
            raise Exception(
                f'يرجى الانتظار {remaining.seconds // 60} دقيقة'
            )

    # إرسال إيميل جديد
    return send_verification_email(user, request)
```

---

## 📝 ملاحظات ختامية

### رموز مهمة في Django

| الرمز      | المعنى                              |
| ---------- | ----------------------------------- |
| `__`       | التنقل بين العلاقات (user\_\_email) |
| `_`        | gettext_lazy للترجمة                |
| `@`        | ديكوريتر (decorator)                |
| `**kwargs` | معاملات اختيارية ككلمات مفتاحية     |

### دورة حياة الطلب

```
URL → urls.py → View → Model/Form → Template → Response
```

---

> **تاريخ التوثيق**: 2026-02-09

---

# 8. admin_actions.py - إجراءات التصدير

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

import csv
# ↑ مكتبة Python القياسية للتعامل مع ملفات CSV

import json
# ↑ مكتبة للتعامل مع JSON

from django.http import HttpResponse
# ↑ كلاس لإنشاء استجابة HTTP
# يُستخدم لإرسال ملفات للتحميل

from django.utils import timezone
# ↑ أدوات الوقت في Django

from django.core.serializers.json import DjangoJSONEncoder
# ↑ محول JSON خاص بـ Django
# يعرف كيف يحول: datetime, Decimal, UUID, etc.

# ═══════════════════════════════════════════════════════════════════════
# دالة تصدير CSV
# ═══════════════════════════════════════════════════════════════════════

def export_as_csv(modeladmin, request, queryset):
    """
    Generic CSV export action for Django Admin with Arabic support
    إجراء عام لتصدير البيانات إلى CSV في لوحة الإدارة
    """
    # ↑ هذه الدالة تُستخدم كـ action في Django Admin
    # modeladmin = كائن الأدمن الذي استدعى الإجراء
    # request = طلب HTTP الحالي
    # queryset = العناصر المحددة

    meta = modeladmin.model._meta
    # ↑ _meta = معلومات وصفية عن النموذج
    # تحتوي على: اسم النموذج، الحقول، العلاقات

    field_names = [field.name for field in meta.fields]
    # ↑ قائمة بأسماء جميع حقول النموذج
    # List Comprehension: إنشاء قائمة من حلقة
    # meta.fields = كل حقول النموذج

    response = HttpResponse(content_type='text/csv')
    # ↑ إنشاء استجابة من نوع CSV
    # content_type = نوع المحتوى (MIME type)

    response['Content-Disposition'] = f'attachment; filename={meta.object_name}_export_{timezone.now().strftime("%Y%m%d")}.csv'
    # ↑ تعيين header لتحميل الملف
    # attachment = تحميل كملف (وليس عرض في المتصفح)
    # filename = اسم الملف المحمل
    # strftime = تنسيق التاريخ (مثال: 20260209)

    # Add BOM for Excel compatibility with Arabic
    response.write(u'\ufeff'.encode('utf8'))
    # ↑ كتابة BOM (Byte Order Mark) في بداية الملف
    # \ufeff = علامة خاصة تخبر Excel أن الملف UTF-8
    # بدونها قد يظهر العربي كرموز غريبة في Excel

    writer = csv.writer(response)
    # ↑ إنشاء كاتب CSV
    # سيكتب مباشرة في response

    writer.writerow(field_names)
    # ↑ كتابة صف العناوين (أسماء الأعمدة)

    for obj in queryset:
        # ↑ المرور على كل عنصر محدد

        row = []
        # ↑ قائمة لتخزين قيم الصف

        for field in field_names:
            value = getattr(obj, field)
            # ↑ getattr = جلب قيمة خاصية باسمها
            # مثال: getattr(user, 'email') = user.email

            if hasattr(value, 'strftime'):
                # ↑ إذا كانت القيمة تاريخ/وقت
                value = value.strftime('%Y-%m-%d %H:%M')
                # ↑ تحويلها لنص بتنسيق معين

            elif value is None:
                value = ''
                # ↑ تحويل None لنص فارغ

            # Handle list/dict for CSV
            if isinstance(value, (list, dict)):
                # ↑ إذا كانت القيمة قائمة أو قاموس
                value = json.dumps(value, ensure_ascii=False)
                # ↑ تحويلها لـ JSON
                # ensure_ascii=False = للحفاظ على العربي

            row.append(str(value))
            # ↑ إضافة القيمة كنص للصف

        writer.writerow(row)
        # ↑ كتابة الصف في CSV

    return response
    # ↑ إرجاع الاستجابة (سيبدأ التحميل)

export_as_csv.short_description = "📂 تصدير المحدد إلى CSV"
# ↑ النص الذي يظهر في قائمة الإجراءات
# يمكن استخدام إيموجي!

# ═══════════════════════════════════════════════════════════════════════
# دالة تصدير JSON
# ═══════════════════════════════════════════════════════════════════════

def export_as_json(modeladmin, request, queryset):
    """
    Generic JSON export action
    إجراء عام لتصدير البيانات إلى JSON
    """
    meta = modeladmin.model._meta
    data = []
    # ↑ قائمة لتخزين البيانات

    for obj in queryset:
        item = {}
        # ↑ قاموس لتخزين بيانات عنصر واحد

        for field in meta.fields:
            value = getattr(obj, field.name)

            if hasattr(value, 'file'):
                # ↑ إذا كانت القيمة ملف (ImageField, FileField)
                value = value.url if value else None
                # ↑ جلب الـ URL إذا وجد

            item[field.name] = value
            # ↑ إضافة للقاموس

        data.append(item)
        # ↑ إضافة العنصر للقائمة

    response = HttpResponse(content_type='application/json')
    # ↑ استجابة من نوع JSON

    response['Content-Disposition'] = f'attachment; filename={meta.object_name}_export_{timezone.now().strftime("%Y%m%d")}.json'

    json.dump(data, response, cls=DjangoJSONEncoder, indent=4, ensure_ascii=False)
    # ↑ json.dump = كتابة JSON مباشرة في ملف/استجابة
    # cls=DjangoJSONEncoder = استخدام محول Django
    # indent=4 = تنسيق جميل (4 مسافات)
    # ensure_ascii=False = دعم العربي

    return response

export_as_json.short_description = "📄 تصدير المحدد إلى JSON"
```

---

# 9. mixins.py - خلطات الصلاحيات

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from django.contrib.auth.mixins import AccessMixin
# ↑ كلاس أساسي للتحكم في الوصول
# يوفر: handle_no_permission(), get_login_url()

from django.core.exceptions import PermissionDenied
# ↑ استثناء يُظهر صفحة 403 Forbidden

from users.services.rbac_service import RBACService
# ↑ خدمة التحقق من الصلاحيات (Role-Based Access Control)

# ═══════════════════════════════════════════════════════════════════════
# خلطة التحقق من الصلاحيات (RBAC)
# ═══════════════════════════════════════════════════════════════════════

class RbacPermissionRequiredMixin(AccessMixin):
    """
    Mixin to check user permissions via RBACService.
    خلطة للتحقق من صلاحيات المستخدم عبر خدمة RBAC

    الاستخدام:
        class MyView(RbacPermissionRequiredMixin, View):
            permission_required = 'places.add_place'
    """
    # ↑ Mixin = كلاس يُضاف للوراثة المتعددة
    # لا يُستخدم وحده، بل مع كلاسات أخرى

    permission_required = None
    # ↑ الصلاحية المطلوبة (يُحددها المستخدم)
    # صيغة: 'app_label.permission_codename'
    # مثال: 'places.add_place', 'users.change_user'

    def dispatch(self, request, *args, **kwargs):
        # ↑ dispatch = أول دالة تُستدعى عند وصول طلب
        # تحدد أي دالة (get, post, etc.) ستُستدعى
        # نعترضها هنا للتحقق من الصلاحيات

        if not request.user.is_authenticated:
            # ↑ إذا المستخدم غير مسجل دخوله
            return self.handle_no_permission()
            # ↑ توجيهه لصفحة الدخول أو 403

        if self.permission_required:
            # ↑ إذا حددنا صلاحية مطلوبة

            has_perm = RBACService.user_has_permission(
                request.user,
                self.permission_required
            )
            # ↑ التحقق من الصلاحية عبر الخدمة

            if not has_perm:
                return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
        # ↑ استدعاء dispatch الأصلية لمتابعة الطلب

    def handle_no_permission(self):
        # ↑ تُستدعى عند رفض الوصول

        if self.raise_exception or self.request.user.is_authenticated:
            # ↑ إذا المستخدم مسجل → 403
            # إذا غير مسجل → توجيه للدخول
            raise PermissionDenied(self.get_permission_denied_message())

        return super().handle_no_permission()
        # ↑ التصرف الافتراضي (توجيه للدخول)

# ═══════════════════════════════════════════════════════════════════════
# خلطة التحقق من الشريك المعتمد
# ═══════════════════════════════════════════════════════════════════════

class ApprovedPartnerRequiredMixin(AccessMixin):
    """
    Ensure user is a Partner and their Profile is APPROVED.
    التأكد من أن المستخدم شريك ومعتمد
    """

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Allow superusers and staff
        if request.user.is_superuser or request.user.is_staff:
            # ↑ السماح للمدراء بالوصول دائماً
            return super().dispatch(request, *args, **kwargs)

        # Check Role (case-insensitive)
        role_name = (
            getattr(getattr(request.user, 'role', None), 'name', '') or ''
        ).strip().lower()
        # ↑ سلسلة getattr للوصول الآمن:
        # request.user.role.name
        # لكن بدون أخطاء إذا كان role = None
        # .strip() = إزالة المسافات
        # .lower() = تحويل لأحرف صغيرة

        if role_name != 'partner':
            raise PermissionDenied("User is not a Partner")
            # ↑ المستخدم ليس شريكاً

        # Check Profile Status
        if not hasattr(request.user, 'partner_profile'):
            # ↑ إذا ليس لديه ملف شريك

            # Auto-fix: Create profile
            from .models import PartnerProfile
            PartnerProfile.objects.create(user=request.user, status='pending')
            # ↑ إنشاء ملف شريك تلقائياً

            from django.shortcuts import redirect
            return redirect('partner_pending')
            # ↑ توجيه لصفحة الانتظار

        # Check if approved
        if not request.user.partner_profile.is_approved:
            # ↑ إذا الملف غير معتمد
            from django.shortcuts import redirect
            return redirect('partner_pending')

        # Also check account_status
        if request.user.account_status != 'active':
            # ↑ إذا حالة الحساب ليست نشطة
            from django.shortcuts import redirect
            return redirect('partner_pending')

        return super().dispatch(request, *args, **kwargs)
        # ↑ كل شيء صحيح، متابعة الطلب
```

---

# 10. backends.py - نظام المصادقة المخصص

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from django.contrib.auth import get_user_model
# ↑ دالة للحصول على نموذج المستخدم الحالي
# أفضل من استيراد User مباشرة (للمرونة)

from django.contrib.auth.backends import ModelBackend
# ↑ نظام المصادقة الافتراضي في Django
# نرث منه لتخصيص سلوك المصادقة

from django.db.models import Q
# ↑ Q = كائن للاستعلامات المعقدة
# يسمح بـ OR, AND, NOT في الشروط

User = get_user_model()
# ↑ الحصول على نموذج المستخدم
# يرجع الكلاس المحدد في AUTH_USER_MODEL

# ═══════════════════════════════════════════════════════════════════════
# نظام المصادقة بالإيميل أو اسم المستخدم
# ═══════════════════════════════════════════════════════════════════════

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend which allows users to authenticate
    using either their username or email address.

    نظام مصادقة يسمح بتسجيل الدخول بالإيميل أو اسم المستخدم
    """
    # ↑ يجب تسجيل هذا الـ backend في settings.py:
    # AUTHENTICATION_BACKENDS = [
    #     'users.backends.EmailOrUsernameModelBackend',
    # ]

    def authenticate(self, request, username=None, password=None, **kwargs):
        # ↑ الدالة الرئيسية للمصادقة
        # username = ما أدخله المستخدم (قد يكون إيميل!)
        # password = كلمة المرور
        # **kwargs = معاملات إضافية

        # Determine if 'username' is an email or a username
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
            # ↑ USERNAME_FIELD = الحقل الرئيسي للتعريف
            # عادة 'username' أو 'email'

        try:
            # Try to fetch the user by searching username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            # ↑ Q(...) | Q(...) = OR بين الشرطين
            # __iexact = مطابقة بدون حساسية للحروف
            # (case-insensitive exact match)
            #
            # الاستعلام يبحث عن مستخدم:
            # username = 'ahmed' أو email = 'ahmed'

        except User.DoesNotExist:
            # ↑ لم يوجد مستخدم مطابق
            return None
            # ↑ None = فشل المصادقة

        except User.MultipleObjectsReturned:
            # ↑ وُجد أكثر من مستخدم (نادر)
            # يحدث إذا كان email غير unique

            return User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by('id').first()
            # ↑ اختيار الأول مرتب بالـ id

        if user.check_password(password) and self.user_can_authenticate(user):
            # ↑ check_password = التحقق من كلمة المرور
            # تقارن مع الـ hash المحفوظ
            #
            # user_can_authenticate = التحقق من is_active
            # (وأي شروط إضافية)

            return user
            # ↑ نجاح! إرجاع المستخدم

        return None
        # ↑ كلمة المرور خاطئة أو الحساب غير نشط
```

---

# 11. serializers.py - محولات API

```python
# ═══════════════════════════════════════════════════════════════════════
# الاستيرادات
# ═══════════════════════════════════════════════════════════════════════

from rest_framework import serializers
# ↑ Django REST Framework
# serializers = محولات بين Python و JSON

from .models import User

# ═══════════════════════════════════════════════════════════════════════
# محول التسجيل
# ═══════════════════════════════════════════════════════════════════════

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration API
    محول لتسجيل المستخدمين عبر API
    """
    # ↑ ModelSerializer = محول مبني على نموذج
    # ينشئ الحقول تلقائياً

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    # ↑ حقل كلمة المرور
    # write_only = لا يُرجع في الاستجابة (للأمان)
    # min_length = الحد الأدنى للطول
    # style = إعدادات العرض (للواجهة التفاعلية)

    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    # ↑ حقل تأكيد كلمة المرور

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone_number',
                  'password', 'password_confirm']
        # ↑ الحقول المضمنة في الـ API

    def validate(self, data):
        # ↑ تحقق على مستوى الكائن كاملاً
        # تُستدعى بعد validate_<field> لكل حقل

        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'كلمتا المرور غير متطابقتين'
            })
            # ↑ رمي خطأ تحقق

        return data

    def validate_email(self, value):
        # ↑ تحقق مخصص لحقل email

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('هذا البريد مسجل مسبقاً')

        return value

    def create(self, validated_data):
        # ↑ إنشاء الكائن من البيانات الصحيحة

        validated_data.pop('password_confirm')
        # ↑ إزالة حقل التأكيد (ليس في النموذج)

        password = validated_data.pop('password')
        # ↑ إخراج كلمة المرور

        user = User(**validated_data)
        # ↑ إنشاء كائن User بالبيانات المتبقية
        # ** = فك القاموس كـ keyword arguments

        user.set_password(password)
        # ↑ تشفير كلمة المرور (hashing)
        # لا نحفظ كلمة المرور كنص عادي أبداً!

        user.is_active = False
        user.account_status = 'pending'

        user.save()
        return user

# ═══════════════════════════════════════════════════════════════════════
# محول عرض المستخدم
# ═══════════════════════════════════════════════════════════════════════

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user data
    محول لعرض بيانات المستخدم
    """

    role_name = serializers.SerializerMethodField()
    # ↑ حقل محسوب (ليس في النموذج)
    # يستدعي دالة get_role_name()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name',
                  'phone_number', 'profile_image', 'bio',
                  'role_name', 'account_status', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'account_status']
        # ↑ حقول للقراءة فقط (لا يمكن تعديلها عبر API)

    def get_role_name(self, obj):
        # ↑ دالة لحساب role_name
        # obj = كائن User

        return obj.role.name if obj.role else None
        # ↑ إرجاع اسم الدور أو None
```

---

# 12. context_processors.py - معالجات السياق

```python
# ═══════════════════════════════════════════════════════════════════════
# معالجات السياق
# ═══════════════════════════════════════════════════════════════════════

# معالج السياق = دالة تُضيف متغيرات لكل القوالب
# يُسجل في settings.py → TEMPLATES → OPTIONS → context_processors

def user_notifications(request):
    """
    إضافة عدد الإشعارات غير المقروءة لكل صفحة
    """
    if request.user.is_authenticated:
        from interactions.models import Notification

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        # ↑ عدد الإشعارات غير المقروءة

        return {
            'unread_notifications_count': unread_count
        }
        # ↑ قاموس يُدمج مع context القالب

    return {}
    # ↑ قاموس فارغ للمستخدمين غير المسجلين


def site_settings(request):
    """
    إضافة إعدادات الموقع لكل صفحة
    """
    from management.models import SiteSetting

    settings_dict = {}

    for setting in SiteSetting.objects.all():
        settings_dict[setting.key] = setting.value

    return {
        'site_settings': settings_dict
    }
    # ↑ الآن يمكن في أي قالب:
    # {{ site_settings.site_name }}
    # {{ site_settings.contact_email }}


# ═══════════════════════════════════════════════════════════════════════
# التسجيل في settings.py
# ═══════════════════════════════════════════════════════════════════════

# TEMPLATES = [
#     {
#         ...
#         'OPTIONS': {
#             'context_processors': [
#                 ...
#                 'users.context_processors.user_notifications',
#                 'management.context_processors.site_settings',
#             ],
#         },
#     },
# ]
```

---

## 📊 ملخص الملفات

| الملف                   | الوظيفة الرئيسية          | يُستخدم في      |
| ----------------------- | ------------------------- | --------------- |
| `models.py`             | تعريف هيكل قاعدة البيانات | كل شيء          |
| `views.py`              | معالجة الطلبات            | urls.py         |
| `forms.py`              | التحقق من إدخال المستخدم  | views.py        |
| `admin.py`              | لوحة الإدارة              | Django Admin    |
| `urls.py`               | توجيه الطلبات             | المشروع الرئيسي |
| `signals.py`            | إجراءات تلقائية           | يعمل تلقائياً   |
| `email_service.py`      | إرسال الإيميلات           | views.py        |
| `mixins.py`             | فحص الصلاحيات             | views.py        |
| `backends.py`           | نظام المصادقة             | settings.py     |
| `serializers.py`        | تحويل JSON ↔ Python       | API views       |
| `admin_actions.py`      | إجراءات التصدير           | admin.py        |
| `context_processors.py` | متغيرات للقوالب           | templates       |

---

## 🔄 دورة حياة طلب Django

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────┐
│  urls.py    │ → تحديد الـ View المطلوب
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Middleware │ → معالجة الطلب (Auth, Session, CSRF)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Mixins    │ → فحص الصلاحيات
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   View      │ → منطق الأعمال
├─────────────┤
│  ├─ Form    │ → التحقق من البيانات
│  ├─ Model   │ → التعامل مع قاعدة البيانات
│  └─ Service │ → منطق إضافي
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Template   │ → إنشاء HTML
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Response   │ → إرسال الاستجابة
└─────────────┘
```

---

> **تاريخ التوثيق**: 2026-02-09
> **الإصدار**: 2.0 (مُحدّث)
