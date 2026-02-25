from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from users.services.rbac_service import RBACService

class RbacPermissionRequiredMixin(AccessMixin):
    """
    Mixin to check user permissions via RBACService.
    Usage:
        class MyView(RbacPermissionRequiredMixin, View):
            permission_required = 'places.add_place'
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.permission_required:
            has_perm = RBACService.user_has_permission(request.user, self.permission_required)
            if not has_perm:
                return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()
        return super().handle_no_permission()

class ApprovedPartnerRequiredMixin(AccessMixin):
    """
    Ensure user is a Partner and their Profile is APPROVED.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Allow superusers and staff
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)
            
        # Check Role (case-insensitive)
        role_name = (getattr(getattr(request.user, 'role', None), 'name', '') or '').strip().lower()
        if role_name != 'partner':
            raise PermissionDenied("User is not a Partner")
             
        # Check Profile Status
        if not hasattr(request.user, 'partner_profile'):
            # Auto-fix: Create profile if user has Partner role but no profile (e.g. manual admin assign)
            from .models import PartnerProfile
            PartnerProfile.objects.create(user=request.user, status='pending')
            # Check again (or redirect to pending)
            from django.shortcuts import redirect
            return redirect('partner_pending')
        
        # Use is_approved boolean matching the Policy
        # Also check account_status to be consistent with UserPolicy
        if not request.user.partner_profile.is_approved or request.user.account_status != 'active':
            from django.shortcuts import redirect
            return redirect('partner_pending')

        return super().dispatch(request, *args, **kwargs)

class StaffAdminRequiredMixin(AccessMixin):
    """
    Ensure user is Staff/Admin but NOT a Partner.
    Prevents Partners (who have is_staff=True) from accessing Admin Dashboard.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Must be staff or superuser
        if not request.user.is_staff:
            return self.handle_no_permission()

        # Block Partners (unless they are also superusers)
        if not request.user.is_superuser:
            role_name = (getattr(getattr(request.user, 'role', None), 'name', '') or '').strip().lower()
            if role_name == 'partner':
                from django.shortcuts import redirect
                return redirect('partner_dashboard')

        return super().dispatch(request, *args, **kwargs)
