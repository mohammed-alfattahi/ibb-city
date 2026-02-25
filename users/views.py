from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, CreateView
from django.urls import reverse_lazy
from interactions.models import Favorite, Review
from .forms import UserUpdateForm, VisitorSignUpForm

User = get_user_model()

class VisitorSignUpView(CreateView):
    model = User
    form_class = VisitorSignUpForm
    template_name = 'registration/visitor_signup.html'
    success_url = reverse_lazy('verification_sent')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_email_verified = False
        user.save()
        
        # Check if email verification is skipped
        from django.conf import settings
        skip_verification = getattr(settings, 'SKIP_EMAIL_VERIFICATION', False)
        
        if skip_verification:
            # Auto-verify and auto-login
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            
            # Log registration as success
            from .models import UserRegistrationLog
            UserRegistrationLog.log_registration(
                request=self.request,
                user=user,
                email=user.email,
                username=user.username,
                registration_type='tourist',
                status='success'
            )
            
            # Auto-login the user
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            from django.contrib import messages
            messages.success(self.request, f'مرحباً {user.username}! تم إنشاء حسابك بنجاح.')
            
            from django.shortcuts import redirect
            return redirect('home')
        else:
            # Send verification email
            from .email_service import send_verification_email
            send_verification_email(user, self.request)
            
            # Log registration for audit
            from .models import UserRegistrationLog
            UserRegistrationLog.log_registration(
                request=self.request,
                user=user,
                email=user.email,
                username=user.username,
                registration_type='tourist',
                status='pending'  # Pending until email verified
            )
            
            # Store email in session for the verification_sent page
            self.request.session['pending_verification_email'] = user.email
            
            # Don't auto-login - user must verify email first
            return super().form_valid(form)
    
    def form_invalid(self, form):
        # Log failed registration attempt
        from .models import UserRegistrationLog
        UserRegistrationLog.log_registration(
            request=self.request,
            email=form.data.get('email', ''),
            username=form.data.get('username', ''),
            registration_type='tourist',
            status='failed',
            failure_reason=str(form.errors)
        )
        return super().form_invalid(form)

User = get_user_model()

class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['favorites'] = Favorite.objects.filter(user=self.request.user).select_related('place')
        context['my_reviews'] = Review.objects.filter(user=self.request.user).select_related('place').order_by('-created_at')
        return context

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "تم تحديث الملف الشخصي بنجاح")
        response = super().form_valid(form) # Saves the form
        
        if self.request.headers.get('HX-Request'):
            from django.http import HttpResponse
            from django.template.loader import render_to_string
            
            # Re-fetch user to ensure we have latest data (e.g. images)
            self.object.refresh_from_db()
            
            sidebar_html = render_to_string('users/partials/profile_sidebar.html', {'user': self.object}, request=self.request)
            hero_html = render_to_string('users/partials/profile_hero.html', {'user': self.object}, request=self.request)
            
            # OOB Swap for Hero
            # Sidebar is replacing itself because it has id="profile-sidebar" and partial also has it.
            # But wait, sidebar partial has id="profile-sidebar".
            # The form submission target is default (which is the form itself usually if not specified, but we put hx-swap="none").
            # So we rely on OOB for everything.
            
            response_content = f"""
            <div hx-swap-oob="outerHTML:#profile-sidebar">{sidebar_html}</div>
            <div hx-swap-oob="outerHTML:#profile-hero">{hero_html}</div>
            """
            
            # Also add a toast message if possible, but for now just the updates.
            # from django.contrib import messages
            # messages.success(self.request, "تم تحديث الملف الشخصي بنجاح")
            
            # If we had a toast container, we could swap it too.
            # For now, relying on visual updates.
            
            return HttpResponse(response_content)
            
        return response

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from interactions.models import NotificationPreference
        context['prefs'] = NotificationPreference.get_or_create_for_user(self.request.user)
        return context


# ============================================
# Unified Login View with Rate Limiting
# ============================================
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from .forms_login import UnifiedLoginForm
from axes.helpers import get_client_ip_address

class UnifiedLoginView(LoginView):
    """
    نظام تسجيل دخول موحد لجميع المستخدمين
    يدعم تسجيل الدخول بالبريد الإلكتروني أو اسم المستخدم
    مع حماية ضد محاولات الاختراق والتحقق من حالة الحساب
    """
    template_name = 'registration/login.html'
    form_class = UnifiedLoginForm
    redirect_authenticated_user = True
    
    # Remember Me settings
    REMEMBER_ME_EXPIRY = 60 * 60 * 24 * 30  # 30 days in seconds
    
    def dispatch(self, request, *args, **kwargs):
        """التحقق من حظر Axes قبل عرض الصفحة"""
        from axes.helpers import is_client_ip_address_blacklisted
        from axes.handlers.proxy import AxesProxyHandler
        
        # Check if user is locked out by Axes
        if AxesProxyHandler.is_locked(request):
            messages.error(
                request,
                str(_('تم حظر حسابك مؤقتاً بسبب محاولات تسجيل دخول فاشلة متعددة. يرجى الانتظار والمحاولة لاحقاً.'))
            )
            return self.render_to_response(self.get_context_data(form=self.get_form(), locked_out=True))
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """التحقق من حالة الحساب قبل السماح بتسجيل الدخول"""
        user = form.get_user()
        username_or_email = form.cleaned_data.get('username', '')
        
        # Import login log model
        from .models import UserLoginLog
        
        # التحقق من تأكيد البريد الإلكتروني (فقط للمستخدمين العاديين، ليس المشرفين)
        if not user.is_superuser and not user.is_staff:
            from django.conf import settings
            skip_verification = getattr(settings, 'SKIP_EMAIL_VERIFICATION', False)
            
            if not skip_verification and hasattr(user, 'is_email_verified') and not user.is_email_verified:
                self.request.session['pending_verification_email'] = user.email
                messages.warning(
                    self.request,
                    str(_('يرجى تأكيد بريدك الإلكتروني أولاً. تحقق من صندوق الوارد.'))
                )
                # Log failed attempt - email not verified
                UserLoginLog.log_attempt(
                    request=self.request,
                    user=user,
                    username_or_email=username_or_email,
                    status='failed',
                    failure_reason='email_not_verified'
                )
                return redirect('verification_sent')
        
        # التحقق من حالة الحساب
        if hasattr(user, 'account_status'):
            if user.account_status == 'suspended':
                suspension_reason = user.suspension_reason or str(_('لم يتم تحديد السبب'))
                messages.error(
                    self.request,
                    str(_('تم إيقاف حسابك. السبب: {}').format(suspension_reason))
                )
                # Log failed attempt - account suspended
                UserLoginLog.log_attempt(
                    request=self.request,
                    user=user,
                    username_or_email=username_or_email,
                    status='failed',
                    failure_reason='account_suspended',
                    failure_details=user.suspension_reason or ''
                )
                return self.form_invalid(form)
            
            elif user.account_status == 'rejected':
                messages.error(
                    self.request,
                    str(_('تم رفض حسابك. يرجى التواصل مع الإدارة للمزيد من المعلومات.'))
                )
                # Log failed attempt - account rejected
                UserLoginLog.log_attempt(
                    request=self.request,
                    user=user,
                    username_or_email=username_or_email,
                    status='failed',
                    failure_reason='account_rejected'
                )
                return self.form_invalid(form)
            
            elif user.account_status == 'pending':
                messages.warning(
                    self.request,
                    _('حسابك قيد المراجعة. ستتمكن من الوصول الكامل بعد الموافقة.')
                )
        
        # Log successful login
        UserLoginLog.log_attempt(
            request=self.request,
            user=user,
            username_or_email=username_or_email,
            status='success'
        )
        
        # Handle Remember Me
        remember_me = self.request.POST.get('remember_me')
        if remember_me:
            # Set session to expire in 30 days
            self.request.session.set_expiry(self.REMEMBER_ME_EXPIRY)
        else:
            # Session expires when browser closes
            self.request.session.set_expiry(0)
        
        # Session Fixation Protection: regenerate session ID after successful login
        self.request.session.cycle_key()
        
        return super().form_valid(form)

    def get_success_url(self):
        """توجيه المستخدم حسب دوره ونوع حسابه"""
        user = self.request.user
        
        # التحقق من كون المستخدم مشرف (أعلى أولوية)
        if user.is_superuser:
            return reverse_lazy('admin:index')
        
        # التحقق من وجود ملف شريك تجاري (أولوية قبل الموظفين لأن الشركاء staff)
        if hasattr(user, 'partner_profile'):
            partner = user.partner_profile
            # Check status properly
            if partner.status == 'approved' or getattr(partner, 'is_approved', False):
                return reverse_lazy('partner_dashboard')
            elif partner.status in ('rejected', 'needs_info', 'pending'):
                return reverse_lazy('partner_pending')

        # التحقق من الدور (Role) لتوجيه الشركاء حتى بدون بروفايل مكتمل
        if user.role and user.role.name == 'partner':
             # If they have the role but no profile (edge case), send to wizard
             if not hasattr(user, 'partner_profile'):
                 return reverse_lazy('wizard_start')
             # Fallback to pending if status unknown
             return reverse_lazy('partner_pending')

        # التحقق من كون المستخدم موظف مكتب سياحة
        if user.is_staff:
            return reverse_lazy('custom_admin_dashboard')
        
        # المستخدم العادي (سائح)
        return reverse_lazy('home')

    def form_invalid(self, form):
        """عرض رسالة خطأ عند فشل تسجيل الدخول"""
        # Log failed login attempt - invalid credentials
        from .models import UserLoginLog
        username_or_email = form.data.get('username', '')
        UserLoginLog.log_attempt(
            request=self.request,
            username_or_email=username_or_email,
            status='failed',
            failure_reason='invalid_credentials'
        )
        
        # تجنب إضافة رسالة مكررة إذا كانت موجودة بالفعل
        storage = messages.get_messages(self.request)
        existing_messages = [m.message for m in storage]
        storage.used = False  # إعادة الرسائل للعرض
        
        error_msg = _('بيانات تسجيل الدخول غير صحيحة. تأكد من اسم المستخدم وكلمة المرور.')
        if str(error_msg) not in existing_messages:
            messages.error(self.request, error_msg)
        
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """إضافة معلومات إضافية للقالب"""
        context = super().get_context_data(**kwargs)
        
        # Check for lockout first
        from axes.handlers.proxy import AxesProxyHandler
        context['locked_out'] = AxesProxyHandler.is_locked(self.request)
        
        # محاولة الحصول على عدد المحاولات المتبقية
        try:
            from axes.models import AccessAttempt
            from django.conf import settings
            
            ip = get_client_ip_address(self.request)
            attempts = AccessAttempt.objects.filter(ip_address=ip).first()
            
            # Get max attempts from settings (default 5)
            max_attempts = getattr(settings, 'AXES_FAILURE_LIMIT', 5)
            
            if attempts:
                remaining = max_attempts - attempts.failures_since_start
                context['remaining_attempts'] = max(0, remaining)
                context['failed_attempts'] = attempts.failures_since_start
            else:
                context['remaining_attempts'] = max_attempts
                context['failed_attempts'] = 0
                
            context['max_attempts'] = max_attempts
        except Exception:
            pass
        
        return context


# ============================================
# Email Verification Views
# ============================================
from django.views import View
from django.shortcuts import render
from django.http import HttpResponseRedirect

class VerificationSentView(TemplateView):
    """Page shown after registration asking user to check email."""
    template_name = 'registration/verification_sent.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.session.get('pending_verification_email', '')
        return context


class EmailVerificationView(View):
    """Handle email verification token."""
    
    TOKEN_EXPIRY_HOURS = 24  # Token expires after 24 hours
    
    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            
            # Check token expiry (24 hours)
            if user.email_verification_sent_at:
                from datetime import timedelta
                from django.utils import timezone
                expiry_time = user.email_verification_sent_at + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
                if timezone.now() > expiry_time:
                    return render(request, 'registration/verification_failed.html', {
                        'error_message': _('رابط التحقق منتهي الصلاحية. يرجى طلب رابط جديد.'),
                        'expired': True,
                        'email': user.email
                    })
            
            # Mark email as verified
            user.is_email_verified = True
            user.email_verification_token = ''  # Clear the token
            user.save(update_fields=['is_email_verified', 'email_verification_token'])
            
            # Update registration log status to success
            from .models import UserRegistrationLog
            UserRegistrationLog.objects.filter(
                user=user, 
                status='pending'
            ).update(status='success')
            
            messages.success(request, _('تم تأكيد بريدك الإلكتروني بنجاح!'))
            return render(request, 'registration/verification_success.html')
            
        except User.DoesNotExist:
            return render(request, 'registration/verification_failed.html', {
                'error_message': _('رابط التحقق غير صالح أو منتهي الصلاحية.')
            })


class ResendVerificationView(View):
    """Resend verification email."""
    
    def post(self, request):
        email = request.POST.get('email') or request.session.get('pending_verification_email')
        
        if not email:
            messages.error(request, _('لم يتم تحديد البريد الإلكتروني.'))
            return redirect('login')
        
        try:
            # Bug fix: Handle duplicate emails gracefully
            user_qs = User.objects.filter(email=email, is_email_verified=False)
            if not user_qs.exists():
                raise User.DoesNotExist
            user = user_qs.first()
            
            from .email_service import resend_verification_email
            success, message = resend_verification_email(user, request)
            
            if success:
                messages.success(request, message)
            else:
                messages.warning(request, message)
            
            return render(request, 'registration/verification_sent.html', {'email': email})
            
        except User.DoesNotExist:
            messages.error(request, _('لم يتم العثور على حساب بهذا البريد الإلكتروني.'))
            return redirect('login')
