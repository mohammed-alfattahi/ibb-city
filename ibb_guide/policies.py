from typing import Optional, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

User = get_user_model()

class BasePolicy:
    """
    Base class for all policies.
    Policies define strict rules for WHO can do WHAT on WHICH object.
    """
    def __init__(self, user: User):
        self.user = user

    def check(self, rule: str, target: Optional[Any] = None) -> bool:
        """
        Generic check method. Should be overridden or used with dynamic dispatch.
        """
        method_name = f"can_{rule}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(target)
        return False

    def authorize(self, rule: str, target: Optional[Any] = None):
        """
        Raises PermissionDenied if the check fails.
        """
        if not self.check(rule, target):
            raise PermissionDenied(f"Authorization failed for rule: {rule}")


class UserPolicy(BasePolicy):
    def can_access_dashboard(self, target=None) -> bool:
        """
        Policy: Only Staff (Admin), Partners, and specific roles can access the dashboard.
        Suspended users are explicitly blocked.
        """
        if not self.user.is_authenticated:
            return False
            
        if self.user.account_status == 'suspended':
            return False

        # Staff always access
        if self.user.is_staff or self.user.is_superuser:
            return True

        # Partners can access if active AND have an approved profile
        if self.user.role and self.user.role.name.lower() == 'partner':
            if self.user.account_status == 'active':
                try:
                    return self.user.partner_profile.is_approved
                except Exception:
                    return False
            return False

        # Fallback: Check for Partner Profile existence
        try:
            if self.user.partner_profile.is_approved:
                return self.user.account_status == 'active'
        except Exception:
            pass

        return False

    def can_manage_users(self, target=None) -> bool:
        """Admin only."""
        return self.user.is_staff or self.user.is_superuser


class PlacePolicy(BasePolicy):
    def can_create_place(self, target=None) -> bool:
        # Only Active Partners can create places
        is_partner = self.user.role and self.user.role.name == 'partner'
        return is_partner and self.user.account_status == 'active'

    def can_edit_place(self, place) -> bool:
        """
        Policy: 
        1. Admins can edit anything.
        2. Owners can edit their own place IF it's not in a 'locked' state (e.g., suspended).
        """
        if self.user.is_superuser or self.user.is_staff:
            return True
            
        if place.owner == self.user:
            # Cannot edit if user is suspended
            if self.user.account_status == 'suspended':
                return False
            # Cannot edit if place is strictly suspended (depending on business rule)
            # For now, we allow editing to fix issues, but maybe not if 'locked'.
            return True
            
        return False
        
    def can_delete_place(self, place) -> bool:
        # Only Admins can delete places? Or Owners too?
        # Usually deletion is sensitive. Let's say Admin only or Owner with restrictions.
        return self.user.is_staff or (place.owner == self.user)


class RequestPolicy(BasePolicy):
    def can_view_requests(self, target=None) -> bool:
        return self.user.is_staff or self.user.is_superuser

    def can_view_own_request(self, request) -> bool:
        """
        Policy: Users can view their own requests.
        Admins can view any request.
        """
        if self.user.is_staff or self.user.is_superuser:
            return True
        return request.user == self.user

    def can_approve_request(self, request) -> bool:
        """
        Policy: Only Admins can approve.
        Approvals MUST be formal (handled via UseCase/Service).
        """
        if not (self.user.is_staff or self.user.is_superuser):
            return False
            
        # Cannot approve a request that is already finalized
        if request.status in ['APPROVED', 'REJECTED', 'CANCELLED']:
            return False
            
        return True

    def can_create_approval_decision(self, request) -> bool:
        """Alias for strict institutional approval."""
        return self.can_approve_request(request)
