"""
Unified Approvals Dashboard Views
Single office page for processing all pending approvals.
"""
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.translation import gettext_lazy as _

from management.services.approval_engine import ApprovalEngine


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require staff access."""
    def test_func(self):
        return self.request.user.is_staff


class UnifiedApprovalsView(StaffRequiredMixin, TemplateView):
    """
    Unified dashboard for all pending approvals.
    Shows 3 tabs: Partners, Establishments, PendingChanges
    """
    template_name = 'management/unified_approvals.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current tab from query param
        tab = self.request.GET.get('tab', 'partners')
        
        context['current_tab'] = tab
        context['counts'] = ApprovalEngine.get_all_pending_counts()
        
        # Load data for current tab
        if tab == 'partners':
            context['pending_items'] = ApprovalEngine.get_pending_partners()
        elif tab == 'establishments':
            context['pending_items'] = ApprovalEngine.get_pending_establishments()
        elif tab == 'changes':
            context['pending_items'] = ApprovalEngine.get_pending_changes()
        
        return context


class ApprovePartnerView(StaffRequiredMixin, View):
    """Handle partner approval."""
    
    def post(self, request, pk):
        from users.models import PartnerProfile
        
        partner = get_object_or_404(PartnerProfile, pk=pk)
        notes = request.POST.get('notes', '')
        
        result = ApprovalEngine.approve_partner(
            office_user=request.user,
            partner_profile=partner,
            request=request,
            notes=notes
        )
        
        if result.success:
            messages.success(request, _("Partner approved successfully"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals')


class RejectPartnerView(StaffRequiredMixin, View):
    """Handle partner rejection."""
    
    def post(self, request, pk):
        from users.models import PartnerProfile
        
        partner = get_object_or_404(PartnerProfile, pk=pk)
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, _("Rejection reason is required"))
            return redirect('management:unified_approvals')
        
        result = ApprovalEngine.reject_partner(
            office_user=request.user,
            partner_profile=partner,
            reason=reason,
            request=request
        )
        
        if result.success:
            messages.success(request, _("Partner rejected"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals')


class RequestInfoPartnerView(StaffRequiredMixin, View):
    """Handle partner info request."""
    
    def post(self, request, pk):
        from users.models import PartnerProfile
        
        partner = get_object_or_404(PartnerProfile, pk=pk)
        info_message = request.POST.get('info_message', '')
        
        if not info_message:
            messages.error(request, _("Info request message is required"))
            return redirect('management:unified_approvals')
        
        result = ApprovalEngine.request_info_partner(
            office_user=request.user,
            partner_profile=partner,
            info_message=info_message,
            request=request
        )
        
        if result.success:
            messages.success(request, _("Info request sent to partner"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals')


class ApproveEstablishmentView(StaffRequiredMixin, View):
    """Handle establishment approval."""
    
    def post(self, request, pk):
        from places.models import Establishment
        
        establishment = get_object_or_404(Establishment, pk=pk)
        notes = request.POST.get('notes', '')
        
        result = ApprovalEngine.approve_establishment(
            office_user=request.user,
            establishment=establishment,
            request=request,
            notes=notes
        )
        
        if result.success:
            messages.success(request, _("Establishment approved"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals') + '?tab=establishments'


class RejectEstablishmentView(StaffRequiredMixin, View):
    """Handle establishment rejection."""
    
    def post(self, request, pk):
        from places.models import Establishment
        
        establishment = get_object_or_404(Establishment, pk=pk)
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, _("Rejection reason is required"))
            return redirect('management:unified_approvals') + '?tab=establishments'
        
        result = ApprovalEngine.reject_establishment(
            office_user=request.user,
            establishment=establishment,
            reason=reason,
            request=request
        )
        
        if result.success:
            messages.success(request, _("Establishment rejected"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals') + '?tab=establishments'


class ApprovePendingChangeView(StaffRequiredMixin, View):
    """Handle pending change approval."""
    
    def post(self, request, pk):
        from management.models import PendingChange
        
        change = get_object_or_404(PendingChange, pk=pk)
        notes = request.POST.get('notes', '')
        
        result = ApprovalEngine.approve_pending_change(
            office_user=request.user,
            pending_change=change,
            request=request,
            notes=notes
        )
        
        if result.success:
            messages.success(request, _("Change approved and applied"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals') + '?tab=changes'


class RejectPendingChangeView(StaffRequiredMixin, View):
    """Handle pending change rejection."""
    
    def post(self, request, pk):
        from management.models import PendingChange
        
        change = get_object_or_404(PendingChange, pk=pk)
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, _("Rejection reason is required"))
            return redirect('management:unified_approvals') + '?tab=changes'
        
        result = ApprovalEngine.reject_pending_change(
            office_user=request.user,
            pending_change=change,
            reason=reason,
            request=request
        )
        
        if result.success:
            messages.success(request, _("Change rejected"))
        else:
            messages.error(request, result.message)
        
        return redirect('management:unified_approvals') + '?tab=changes'


class ApprovalStatsAPIView(StaffRequiredMixin, View):
    """API endpoint for approval stats (for dashboard widgets)."""
    
    def get(self, request):
        counts = ApprovalEngine.get_all_pending_counts()
        return JsonResponse({
            'success': True,
            'counts': counts,
            'total': sum(counts.values())
        })
