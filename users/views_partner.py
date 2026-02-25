from django.views.generic import UpdateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from .models import PartnerProfile
from .forms import PartnerProfileForm
from .forms_auth import PartnerSignUpForm
from django.contrib.auth import get_user_model, login

User = get_user_model()

class PartnerSignUpView(CreateView):
    form_class = PartnerSignUpForm
    template_name = 'partners/signup.html'
    success_url = reverse_lazy('verification_sent')

    def get_context_data(self, **kwargs):
        """Pass multipart flag for file upload if needed (though CreateView handles it if form has FileField)"""
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        # Save the user (form.save() creates User + PartnerProfile)
        response = super().form_valid(form)
        user = self.object  # Get the created user
        
        from users.services.partner_service import PartnerService
        PartnerService.handle_registration(self.request, user)
        
        # Store email in session for verification_sent page
        self.request.session['pending_verification_email'] = user.email
        
        messages.success(self.request, "تم إنشاء حسابك بنجاح!")
        
        if user.is_email_verified:
             # Verification skipped
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('partner_dashboard')
            
        messages.info(self.request, "يرجى تأكيد بريدك الإلكتروني.")
        return redirect('verification_sent')



class PartnerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = PartnerProfile
    form_class = PartnerProfileForm
    template_name = 'partners/profile_form.html'
    success_url = reverse_lazy('partner_profile')

    def get_object(self, queryset=None):
        # Get or create the partner profile for the logged-in user
        profile, created = PartnerProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

from django.views.generic import TemplateView
from management.requests_views import PartnerRequestListView, PartnerRequestDetailView
from management.audit_views import PartnerAuditLogListView

class PartnerPendingView(LoginRequiredMixin, TemplateView):
    """Shows partner request status (pending/rejected). Redirects approved partners."""
    template_name = 'partners/pending_status.html'
    
    def get(self, request, *args, **kwargs):
        profile = getattr(request.user, 'partner_profile', None)
        
        # No profile? Redirect to upgrade request
        if not profile:
            return redirect('partner_upgrade')
        
        # Approved? Redirect to dashboard
        if profile.status == 'approved':
            return redirect('partner_dashboard')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = getattr(self.request.user, 'partner_profile', None)
        return context

from .forms_auth import TouristUpgradeForm
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

@method_decorator(ratelimit(key='user', rate='10/d', method='POST', block=True), name='dispatch')
class TouristToPartnerUpgradeView(LoginRequiredMixin, UpdateView):
    """Tourist requests upgrade to Partner. Creates/updates PartnerProfile with status='pending'."""
    model = User
    form_class = TouristUpgradeForm
    template_name = 'partners/upgrade_request.html'
    success_url = reverse_lazy('partner_pending')

    def get(self, request, *args, **kwargs):
        profile = getattr(request.user, 'partner_profile', None)
        
        if profile:
            if profile.status == 'approved':
                messages.info(request, 'أنت بالفعل شريك معتمد!')
                return redirect('partner_dashboard')
            elif profile.status == 'pending':
                messages.info(request, 'طلبك قيد المراجعة بالفعل')
                return redirect('partner_pending')
        
        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['existing_profile'] = getattr(self.request.user, 'partner_profile', None)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        from users.services.partner_service import PartnerService
        success, message = PartnerService.request_upgrade(self.request.user)
        
        if success:
            messages.success(self.request, message)
        else:
            messages.error(self.request, message)
            
        return response

