"""
Role-Based Access Boundaries - Clear Separation of Tourist, Partner, and Admin

This module defines the boundaries and permissions for each user role,
making access control explicit and maintainable.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Set, Optional


class UserRole(Enum):
    """User role types."""
    ANONYMOUS = "anonymous"
    TOURIST = "tourist"
    PARTNER = "partner"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class Permission(Enum):
    """Available permissions in the system."""
    # Public/Tourist permissions
    VIEW_PLACES = "view_places"
    VIEW_REVIEWS = "view_reviews"
    CREATE_REVIEW = "create_review"
    EDIT_OWN_REVIEW = "edit_own_review"
    DELETE_OWN_REVIEW = "delete_own_review"
    REPORT_CONTENT = "report_content"
    TOGGLE_FAVORITE = "toggle_favorite"
    VIEW_PROFILE = "view_profile"
    EDIT_OWN_PROFILE = "edit_own_profile"
    
    # Partner permissions
    MANAGE_ESTABLISHMENT = "manage_establishment"
    CREATE_ESTABLISHMENT = "create_establishment"
    CREATE_AD = "create_ad"
    REPLY_TO_REVIEW = "reply_to_review"
    HIDE_REVIEW = "hide_review"
    PIN_REVIEW = "pin_review"
    VIEW_PARTNER_DASHBOARD = "view_partner_dashboard"
    VIEW_ANALYTICS = "view_analytics"
    SUBMIT_UPDATE_REQUEST = "submit_update_request"
    
    # Admin permissions
    APPROVE_PARTNER = "approve_partner"
    REJECT_PARTNER = "reject_partner"
    APPROVE_REQUEST = "approve_request"
    REJECT_REQUEST = "reject_request"
    APPROVE_AD = "approve_ad"
    REJECT_AD = "reject_ad"
    SUSPEND_ESTABLISHMENT = "suspend_establishment"
    VIEW_ADMIN_DASHBOARD = "view_admin_dashboard"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_USERS = "manage_users"
    HANDLE_REPORTS = "handle_reports"
    SEND_SYSTEM_NOTIFICATIONS = "send_system_notifications"
    VIEW_SYSTEM_HEALTH = "view_system_health"


@dataclass
class RoleBoundary:
    """
    Defines the boundary for a user role.
    
    Includes:
    - Permissions: What the role can do
    - Accessible URLs: URL patterns the role can access
    - Restricted Models: Models the role can interact with
    """
    role: UserRole
    permissions: Set[Permission] = field(default_factory=set)
    allowed_url_patterns: List[str] = field(default_factory=list)
    description: str = ""
    

class AccessBoundaryPolicy:
    """
    Policy for managing role-based access boundaries.
    
    Usage:
        policy = AccessBoundaryPolicy()
        can_access = policy.has_permission(user_role, Permission.APPROVE_PARTNER)
        allowed_urls = policy.get_allowed_urls(user_role)
    """
    
    # Role definitions
    ROLE_PERMISSIONS = {
        UserRole.ANONYMOUS: {
            Permission.VIEW_PLACES,
            Permission.VIEW_REVIEWS,
        },
        
        UserRole.TOURIST: {
            Permission.VIEW_PLACES,
            Permission.VIEW_REVIEWS,
            Permission.CREATE_REVIEW,
            Permission.EDIT_OWN_REVIEW,
            Permission.DELETE_OWN_REVIEW,
            Permission.REPORT_CONTENT,
            Permission.TOGGLE_FAVORITE,
            Permission.VIEW_PROFILE,
            Permission.EDIT_OWN_PROFILE,
        },
        
        UserRole.PARTNER: {
            # Inherits tourist permissions
            Permission.VIEW_PLACES,
            Permission.VIEW_REVIEWS,
            Permission.CREATE_REVIEW,
            Permission.EDIT_OWN_REVIEW,
            Permission.DELETE_OWN_REVIEW,
            Permission.REPORT_CONTENT,
            Permission.TOGGLE_FAVORITE,
            Permission.VIEW_PROFILE,
            Permission.EDIT_OWN_PROFILE,
            # Partner-specific
            Permission.MANAGE_ESTABLISHMENT,
            Permission.CREATE_ESTABLISHMENT,
            Permission.CREATE_AD,
            Permission.REPLY_TO_REVIEW,
            Permission.HIDE_REVIEW,
            Permission.PIN_REVIEW,
            Permission.VIEW_PARTNER_DASHBOARD,
            Permission.VIEW_ANALYTICS,
            Permission.SUBMIT_UPDATE_REQUEST,
        },
        
        UserRole.ADMIN: {
            # All permissions except superuser-specific
            Permission.VIEW_PLACES,
            Permission.VIEW_REVIEWS,
            Permission.APPROVE_PARTNER,
            Permission.REJECT_PARTNER,
            Permission.APPROVE_REQUEST,
            Permission.REJECT_REQUEST,
            Permission.APPROVE_AD,
            Permission.REJECT_AD,
            Permission.SUSPEND_ESTABLISHMENT,
            Permission.VIEW_ADMIN_DASHBOARD,
            Permission.VIEW_AUDIT_LOG,
            Permission.MANAGE_USERS,
            Permission.HANDLE_REPORTS,
            Permission.SEND_SYSTEM_NOTIFICATIONS,
            Permission.VIEW_SYSTEM_HEALTH,
        },
        
        UserRole.SUPERUSER: {
            # All permissions
            *Permission,
        },
    }
    
    # URL patterns each role can access
    ROLE_URL_PATTERNS = {
        UserRole.ANONYMOUS: [
            r'^/$',
            r'^/place/',
            r'^/places/',
            r'^/login/',
            r'^/join/',
            r'^/offers/',
        ],
        
        UserRole.TOURIST: [
            r'^/$',
            r'^/place/',
            r'^/places/',
            r'^/profile/',
            r'^/notifications/',
            r'^/favorites/',
            r'^/offers/',
        ],
        
        UserRole.PARTNER: [
            r'^/$',
            r'^/place/',
            r'^/places/',
            r'^/profile/',
            r'^/notifications/',
            r'^/partner/',
            r'^/offers/',
        ],
        
        UserRole.ADMIN: [
            r'^/custom-admin/',
            r'^/admin/',
        ],
        
        UserRole.SUPERUSER: [
            r'^/',  # Access to everything
        ],
    }
    
    def get_role_from_user(self, user) -> UserRole:
        """
        Determine the role of a user.
        
        Args:
            user: Django user object or None
            
        Returns:
            UserRole enum value
        """
        if user is None or not user.is_authenticated:
            return UserRole.ANONYMOUS
        
        if user.is_superuser:
            return UserRole.SUPERUSER
        
        if user.is_staff:
            return UserRole.ADMIN
        
        # Check for partner profile
        if hasattr(user, 'partnerprofile') and user.partnerprofile.is_approved:
            return UserRole.PARTNER
        
        return UserRole.TOURIST
    
    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: UserRole to check
            permission: Permission to verify
            
        Returns:
            True if role has permission
        """
        permissions = self.ROLE_PERMISSIONS.get(role, set())
        return permission in permissions
    
    def get_permissions(self, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role."""
        return self.ROLE_PERMISSIONS.get(role, set())
    
    def get_allowed_urls(self, role: UserRole) -> List[str]:
        """Get URL patterns allowed for a role."""
        return self.ROLE_URL_PATTERNS.get(role, [])
    
    def can_access_resource(self, user, resource_type: str, resource_owner_id: int = None) -> bool:
        """
        Check if a user can access a specific resource.
        
        Args:
            user: Django user object
            resource_type: Type of resource (e.g., 'establishment', 'review')
            resource_owner_id: Optional owner ID for ownership check
            
        Returns:
            True if access is allowed
        """
        role = self.get_role_from_user(user)
        
        # Superusers can access everything
        if role == UserRole.SUPERUSER:
            return True
        
        # Admins can access most things
        if role == UserRole.ADMIN:
            return True
        
        # For owned resources, check ownership
        if resource_owner_id and user.is_authenticated:
            if user.id == resource_owner_id:
                return True
        
        # Default checks based on resource type
        resource_permissions = {
            'establishment': Permission.MANAGE_ESTABLISHMENT,
            'ad': Permission.CREATE_AD,
            'review': Permission.CREATE_REVIEW,
        }
        
        required_permission = resource_permissions.get(resource_type)
        if required_permission:
            return self.has_permission(role, required_permission)
        
        return False
    
    def get_boundary(self, role: UserRole) -> RoleBoundary:
        """
        Get the complete boundary definition for a role.
        
        Args:
            role: UserRole to get boundary for
            
        Returns:
            RoleBoundary dataclass
        """
        descriptions = {
            UserRole.ANONYMOUS: "Unauthenticated visitors - view-only access",
            UserRole.TOURIST: "Registered tourists - can review and favorite",
            UserRole.PARTNER: "Approved partners - can manage establishments",
            UserRole.ADMIN: "Admin staff - can moderate and approve",
            UserRole.SUPERUSER: "Super admin - full system access",
        }
        
        return RoleBoundary(
            role=role,
            permissions=self.get_permissions(role),
            allowed_url_patterns=self.get_allowed_urls(role),
            description=descriptions.get(role, "")
        )


# Convenience functions for Django views
def require_permission(permission: Permission):
    """
    Decorator factory for permission-based access control.
    
    Usage:
        @require_permission(Permission.MANAGE_ESTABLISHMENT)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        from functools import wraps
        from django.core.exceptions import PermissionDenied
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            policy = AccessBoundaryPolicy()
            role = policy.get_role_from_user(request.user)
            
            if not policy.has_permission(role, permission):
                raise PermissionDenied("ليس لديك صلاحية الوصول لهذه الصفحة.")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
