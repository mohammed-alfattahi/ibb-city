"""
Partner Upgrade Views
Views for Tourist → Partner upgrade workflow
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django import forms

from users.models import PartnerProfile, Role
from interactions.notifications.office import OfficeNotifications


class PartnerUpgradeForm(forms.ModelForm):
    """Form for tourist to request partner upgrade."""
    
    class Meta:
        model = PartnerProfile
        fields = ['organization_name', 'id_card_image', 'commercial_registry_file']
        widgets = {
            'organization_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المنشأة أو النشاط التجاري (اختياري)'
            }),
            'id_card_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'commercial_registry_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,image/*'
            }),
        }
        labels = {
            'organization_name': 'اسم المنظمة/النشاط',
            'id_card_image': 'صورة البطاقة الشخصية *',
            'commercial_registry_file': 'السجل التجاري (اختياري)',
        }
    
    def clean_id_card_image(self):
        image = self.cleaned_data.get('id_card_image')
        if not image:
            raise forms.ValidationError('صورة البطاقة الشخصية مطلوبة')
        return image


class PartnerUpgradeRequestView(LoginRequiredMixin, View):
    """
    Tourist requests upgrade to Partner status.
    Creates/updates PartnerProfile with status='pending'.
    """
    template_name = 'partners/upgrade_request.html'
    
    def get(self, request):
        # Check if user already has a partner profile
        existing_profile = getattr(request.user, 'partner_profile', None)
        
        if existing_profile:
            if existing_profile.status == 'approved':
                messages.info(request, 'أنت بالفعل شريك معتمد!')
                return redirect('partner_dashboard')
            elif existing_profile.status == 'pending':
                messages.info(request, 'طلبك قيد المراجعة بالفعل')
                return redirect('partner_pending')
        
        form = PartnerUpgradeForm(instance=existing_profile)
        return render(request, self.template_name, {
            'form': form,
            'existing_profile': existing_profile
        })
    
    def post(self, request):
        from ibb_guide.utils import get_client_ip
        
        existing_profile = getattr(request.user, 'partner_profile', None)
        
        form = PartnerUpgradeForm(request.POST, request.FILES, instance=existing_profile)
        
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.status = 'pending'
            profile.is_approved = False
            profile.submitted_at = timezone.now()
            profile.rejection_reason = ''  # Clear previous rejection
            profile.save()
            
            # Notify office users
            try:
                OfficeNotifications.notify_new_partner_request(profile)
            except Exception:
                pass  # Don't fail if notification fails
            
            messages.success(request, 'تم إرسال طلب الترقية بنجاح! سيتم مراجعته قريباً.')
            return redirect('partner_pending')
        
        return render(request, self.template_name, {
            'form': form,
            'existing_profile': existing_profile
        })


class PartnerPendingView(LoginRequiredMixin, View):
    """
    Shows partner request status (pending/rejected).
    Includes rejection reason if rejected.
    """
    template_name = 'partners/pending_status.html'
    
    def get(self, request):
        profile = getattr(request.user, 'partner_profile', None)
        
        if not profile:
            return redirect('partner_upgrade_request')
        
        if profile.status == 'approved':
            return redirect('partner_dashboard')
        
        return render(request, self.template_name, {
            'profile': profile
        })
