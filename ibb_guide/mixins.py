"""
Object-Level Permission Mixins - Ensure users can only access their own objects.

These mixins provide fine-grained access control beyond simple login requirements.

Usage:
    from ibb_guide.mixins import OwnerRequiredMixin, EstablishmentOwnerMixin
    
    class MyView(EstablishmentOwnerMixin, UpdateView):
        model = Establishment
        ...
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Generic mixin to verify object ownership.
    
    Override `owner_field` to specify the field name that contains the owner.
    Default is 'owner'.
    """
    owner_field = 'owner'
    
    def test_func(self):
        obj = self.get_object()
        owner = getattr(obj, self.owner_field, None)
        
        # Allow superusers and staff
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True
        
        # Check ownership
        return owner == self.request.user
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المحتوى.")
        return super().handle_no_permission()


class EstablishmentOwnerMixin(OwnerRequiredMixin):
    """
    Mixin for views that operate on Establishment objects.
    Ensures only the establishment owner can access.
    """
    owner_field = 'owner'
    
    def get_queryset(self):
        """Filter queryset to only show user's establishments (for list views)."""
        from places.models import Establishment
        qs = super().get_queryset() if hasattr(super(), 'get_queryset') else Establishment.objects.all()
        
        if self.request.user.is_superuser:
            return qs
        
        return qs.filter(owner=self.request.user)


class AdvertisementOwnerMixin(OwnerRequiredMixin):
    """
    Mixin for views that operate on Advertisement objects.
    Ensures only the ad owner can access.
    """
    owner_field = 'owner'
    
    def get_queryset(self):
        """Filter queryset to only show user's ads (for list views)."""
        from management.models import Advertisement
        qs = super().get_queryset() if hasattr(super(), 'get_queryset') else Advertisement.objects.all()
        
        if self.request.user.is_superuser:
            return qs
        
        return qs.filter(owner=self.request.user)


class PlaceOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin for views that operate on Place objects that have an owner through Establishment.
    """
    
    def test_func(self):
        obj = self.get_object()
        
        # Allow superusers
        if self.request.user.is_superuser:
            return True
        
        # Check if it's an establishment owned by user
        if hasattr(obj, 'owner'):
            return obj.owner == self.request.user
        
        # Check if it's a place created by user (for landmarks etc)
        if hasattr(obj, 'establishment'):
            return obj.establishment.owner == self.request.user
        
        return False


class RequestOwnerMixin(OwnerRequiredMixin):
    """
    Mixin for views that operate on Request objects.
    Ensures only the request creator can access.
    """
    owner_field = 'user'


class PartnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to ensure user is an approved partner.
    """
    
    def test_func(self):
        user = self.request.user
        
        # Superusers can access
        if user.is_superuser:
            return True
        
        # Check for approved partner profile
        if hasattr(user, 'partner_profile') and user.partner_profile:
            return user.partner_profile.is_approved
        
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            
            # Check if user has a partner profile
            if hasattr(self.request.user, 'partner_profile'):
                status = self.request.user.partner_profile.status
                if status == 'pending':
                    return redirect('partner_pending')
                elif status == 'rejected':
                    # For now, redirect to pending page which usually shows status
                    # Or we should have a specific rejection page. 
                    # Let's use partner_pending as it likely shows the status message.
                    return redirect('partner_pending')
                elif status == 'needs_info':
                     return redirect('partner_pending')
            
            # If no profile or other issue
            messages.warning(self.request, "يجب أن تكون شريكاً معتمداً للوصول لهذه الصفحة.")
            return redirect('partner_signup')
            
        return super().handle_no_permission()


# ============================================
# DRF Permission Classes
# ============================================
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission for DRF.
    Only allows owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsOwnerOnly(permissions.BasePermission):
    """
    Strict object-level permission - only owner can access (even for read).
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsApprovedPartner(permissions.BasePermission):
    """
    DRF permission to check if user is an approved partner.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'partner_profile') and request.user.partner_profile:
            return request.user.partner_profile.is_approved
        
        return False
