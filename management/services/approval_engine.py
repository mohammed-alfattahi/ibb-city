"""
Unified Approval Engine
Centralizes all approval workflows for Partners, Establishments, and PendingChanges.

This is the single source of truth for all approval logic.
All views should call these methods instead of directly modifying model status.
"""
import logging
from typing import Optional, Tuple
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from management.services.audit_service import AuditService
from interactions.notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ApprovalResult:
    """Result of an approval operation."""
    def __init__(self, success: bool, message: str = '', entity=None):
        self.success = success
        self.message = message
        self.entity = entity


class ApprovalEngine:
    """
    Unified Approval Engine for all approval workflows.
    
    Provides consistent API for:
    - Partner profile approvals (KYC)
    - Establishment approvals (publishing)
    - Sensitive field changes (PendingChange)
    
    All methods enforce permissions, create audit logs, and send notifications.
    """
    
    # ===========================================
    # Partner Approval Methods
    # ===========================================
    
    @staticmethod
    def approve_partner(
        office_user, 
        partner_profile, 
        request=None,
        notes: str = ''
    ) -> ApprovalResult:
        """
        Approve a partner profile (KYC approval).
        
        Args:
            office_user: Staff user performing the approval
            partner_profile: PartnerProfile instance
            request: Django request (for IP extraction)
            notes: Optional approval notes
            
        Returns:
            ApprovalResult with success status
        """
        from users.models import PartnerProfile
        
        # Permission check
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can approve partners")
        
        if partner_profile.status != 'pending':
            return ApprovalResult(
                success=False,
                message=f"Partner is not pending (status: {partner_profile.status})"
            )
        
        # Capture before state
        old_status = partner_profile.status
        
        # Update status + review metadata (model fields)
        partner_profile.status = 'approved'
        partner_profile.rejection_reason = ''
        partner_profile.reviewed_at = timezone.now()
        partner_profile.reviewed_by = office_user
        partner_profile.save(update_fields=['status', 'reviewed_at', 'reviewed_by', 'rejection_reason'])

        # Activate account so ApprovedPartnerRequiredMixin passes
        try:
            user = partner_profile.user
            user.account_status = 'active'
            user.is_active = True
            user.save(update_fields=['account_status', 'is_active'])
        except Exception:
            # Never block approval flow if account_status update fails
            pass
        
        # Audit log
        AuditService.log(
            actor=office_user,
            action='APPROVE',
            target_model=PartnerProfile,
            target_id=partner_profile.pk,
            old_data={'status': old_status},
            new_data={'status': 'approved'},
            reason=notes,
            request=request
        )
        
        # Notify partner
        NotificationService.emit_event(
            'PARTNER_APPROVED',
            {'partner_name': partner_profile.user.get_full_name()},
            {'user_id': partner_profile.user.pk}
        )
        
        logger.info(f"Partner {partner_profile.pk} approved by {office_user}")
        
        return ApprovalResult(
            success=True,
            message="Partner approved successfully",
            entity=partner_profile
        )
    
    @staticmethod
    def reject_partner(
        office_user, 
        partner_profile, 
        reason: str,
        request=None
    ) -> ApprovalResult:
        """
        Reject a partner profile.
        
        Args:
            office_user: Staff user performing the rejection
            partner_profile: PartnerProfile instance
            reason: Rejection reason (required)
            request: Django request
            
        Returns:
            ApprovalResult
        """
        from users.models import PartnerProfile
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can reject partners")
        
        if not reason:
            return ApprovalResult(success=False, message="Rejection reason is required")
        
        old_status = partner_profile.status
        
        partner_profile.status = 'rejected'
        partner_profile.rejection_reason = reason
        partner_profile.reviewed_at = timezone.now()
        partner_profile.reviewed_by = office_user
        partner_profile.save(update_fields=['status', 'rejection_reason', 'reviewed_at', 'reviewed_by'])

        # Mark user as rejected (prevents partner access)
        try:
            user = partner_profile.user
            user.account_status = 'rejected'
            user.save(update_fields=['account_status'])
        except Exception:
            pass
        
        AuditService.log(
            actor=office_user,
            action='REJECT',
            target_model=PartnerProfile,
            target_id=partner_profile.pk,
            old_data={'status': old_status},
            new_data={'status': 'rejected'},
            reason=reason,
            request=request
        )
        
        NotificationService.emit_event(
            'PARTNER_REJECTED',
            {'partner_name': partner_profile.user.get_full_name(), 'reason': reason},
            {'user_id': partner_profile.user.pk}
        )
        
        logger.info(f"Partner {partner_profile.pk} rejected by {office_user}: {reason}")
        
        return ApprovalResult(success=True, message="Partner rejected", entity=partner_profile)
    
    @staticmethod
    def request_info_partner(
        office_user,
        partner_profile,
        info_message: str,
        request=None
    ) -> ApprovalResult:
        """
        Request additional information from a partner.
        
        Args:
            office_user: Staff user requesting info
            partner_profile: PartnerProfile instance
            info_message: Message describing what info is needed
            request: Django request
            
        Returns:
            ApprovalResult
        """
        from users.models import PartnerProfile
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can request info from partners")
        
        if not info_message:
            return ApprovalResult(success=False, message="Info request message is required")
        
        old_status = partner_profile.status
        
        partner_profile.status = 'needs_info'
        partner_profile.info_request_message = info_message
        partner_profile.reviewed_at = timezone.now()
        partner_profile.reviewed_by = office_user
        partner_profile.save(update_fields=[
            'status', 'info_request_message', 'reviewed_at', 'reviewed_by'
        ])
        
        AuditService.log(
            actor=office_user,
            action='REQUEST_INFO',
            target_model=PartnerProfile,
            target_id=partner_profile.pk,
            old_data={'status': old_status},
            new_data={'status': 'needs_info'},
            reason=info_message,
            request=request
        )
        
        NotificationService.emit_event(
            'PARTNER_NEEDS_INFO',
            {
                'partner_name': partner_profile.user.get_full_name(),
                'info_message': info_message,
            },
            {'user_id': partner_profile.user.pk}
        )
        
        logger.info(f"Partner {partner_profile.pk} needs info, requested by {office_user}")
        
        return ApprovalResult(
            success=True,
            message="Info request sent to partner",
            entity=partner_profile
        )
    
    # ===========================================
    # Establishment Approval Methods
    # ===========================================
    
    @staticmethod
    def approve_establishment(
        office_user, 
        establishment, 
        request=None,
        notes: str = ''
    ) -> ApprovalResult:
        """
        Approve an establishment for public visibility.
        
        Args:
            office_user: Staff user
            establishment: Establishment instance
            request: Django request
            notes: Optional notes
            
        Returns:
            ApprovalResult
        """
        from places.models import Establishment
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can approve establishments")
        
        if establishment.approval_status not in ['pending', 'draft']:
            return ApprovalResult(
                success=False,
                message=f"Establishment is not pending (status: {establishment.approval_status})"
            )
        
        old_status = establishment.approval_status
        
        establishment.approval_status = 'approved'
        establishment.approved_at = timezone.now()
        establishment.approved_by = office_user
        establishment.save()
        
        AuditService.log(
            actor=office_user,
            action='APPROVE',
            target_model=Establishment,
            target_id=establishment.pk,
            old_data={'approval_status': old_status},
            new_data={'approval_status': 'approved'},
            reason=notes,
            request=request
        )
        
        # Notify owner
        if establishment.owner:
            NotificationService.emit_event(
                'ESTABLISHMENT_APPROVED',
                {'place_name': establishment.name},
                {'user_id': establishment.owner.pk}
            )
        
        logger.info(f"Establishment {establishment.pk} approved by {office_user}")
        
        return ApprovalResult(success=True, message="Establishment approved", entity=establishment)
    
    @staticmethod
    def reject_establishment(
        office_user, 
        establishment, 
        reason: str,
        request=None
    ) -> ApprovalResult:
        """
        Reject an establishment.
        """
        from places.models import Establishment
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can reject establishments")
        
        if not reason:
            return ApprovalResult(success=False, message="Rejection reason is required")
        
        old_status = establishment.approval_status
        
        establishment.approval_status = 'rejected'
        establishment.rejection_reason = reason
        establishment.save()
        
        AuditService.log(
            actor=office_user,
            action='REJECT',
            target_model=Establishment,
            target_id=establishment.pk,
            old_data={'approval_status': old_status},
            new_data={'approval_status': 'rejected'},
            reason=reason,
            request=request
        )
        
        if establishment.owner:
            NotificationService.emit_event(
                'ESTABLISHMENT_REJECTED',
                {'place_name': establishment.name, 'reason': reason},
                {'user_id': establishment.owner.pk}
            )
        
        logger.info(f"Establishment {establishment.pk} rejected by {office_user}: {reason}")
        
        return ApprovalResult(success=True, message="Establishment rejected", entity=establishment)
    
    # ===========================================
    # PendingChange Approval Methods
    # ===========================================
    
    @staticmethod
    def approve_pending_change(
        office_user, 
        pending_change, 
        request=None,
        notes: str = ''
    ) -> ApprovalResult:
        """
        Approve a pending sensitive field change and apply it.
        
        Args:
            office_user: Staff user
            pending_change: PendingChange instance
            request: Django request
            notes: Optional notes
            
        Returns:
            ApprovalResult
        """
        from management.models import PendingChange
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can approve changes")
        
        if pending_change.status != 'pending':
            return ApprovalResult(
                success=False,
                message=f"Change is not pending (status: {pending_change.status})"
            )
        
        # Store old value
        old_value = pending_change.old_value
        new_value = pending_change.new_value
        
        # Apply the change to the establishment
        establishment = pending_change.establishment
        field_name = pending_change.field_name
        
        if hasattr(establishment, field_name):
            setattr(establishment, field_name, new_value)
            establishment.save(update_fields=[field_name])
        
        # Update pending change status
        pending_change.status = 'approved'
        pending_change.reviewed_by = office_user
        pending_change.reviewed_at = timezone.now()
        pending_change.save()
        
        AuditService.log(
            actor=office_user,
            action='APPROVE_CHANGE',
            target_model=PendingChange,
            target_id=pending_change.pk,
            old_data={'status': 'pending', field_name: old_value},
            new_data={'status': 'approved', field_name: new_value},
            reason=notes,
            request=request
        )
        
        # Notify owner
        if establishment.owner:
            NotificationService.emit_event(
                'CHANGE_APPROVED',
                {'place_name': establishment.name, 'field': field_name},
                {'user_id': establishment.owner.pk}
            )
        
        logger.info(f"PendingChange {pending_change.pk} approved by {office_user}")
        
        return ApprovalResult(success=True, message="Change approved and applied", entity=pending_change)
    
    @staticmethod
    def reject_pending_change(
        office_user, 
        pending_change, 
        reason: str,
        request=None
    ) -> ApprovalResult:
        """
        Reject a pending change.
        """
        from management.models import PendingChange
        
        if not office_user.is_staff:
            raise PermissionDenied("Only staff can reject changes")
        
        if not reason:
            return ApprovalResult(success=False, message="Rejection reason is required")
        
        pending_change.status = 'rejected'
        pending_change.reviewed_by = office_user
        pending_change.reviewed_at = timezone.now()
        pending_change.review_note = reason  # Field is 'review_note' not 'rejection_reason'
        pending_change.save()
        
        AuditService.log(
            actor=office_user,
            action='REJECT_CHANGE',
            target_model=type(pending_change),
            target_id=pending_change.pk,
            old_data={'status': 'pending'},
            new_data={'status': 'rejected'},
            reason=reason,
            request=request
        )
        
        establishment = pending_change.establishment
        if establishment and establishment.owner:
            NotificationService.emit_event(
                'CHANGE_REJECTED',
                {
                    'place_name': establishment.name, 
                    'field': pending_change.field_name,
                    'reason': reason
                },
                {'user_id': establishment.owner.pk}
            )
        
        logger.info(f"PendingChange {pending_change.pk} rejected by {office_user}: {reason}")
        
        return ApprovalResult(success=True, message="Change rejected", entity=pending_change)
    
    # ===========================================
    # Query Methods
    # ===========================================
    
    @staticmethod
    def get_pending_partners():
        """Get all pending partner profiles."""
        from users.models import PartnerProfile
        return PartnerProfile.objects.filter(status='pending').select_related('user')
    
    @staticmethod
    def get_pending_establishments():
        """Get all pending establishments."""
        from places.models import Establishment
        return Establishment.objects.filter(
            approval_status='pending'
        ).select_related('owner', 'category')
    
    @staticmethod
    def get_pending_changes():
        """Get all pending sensitive field changes."""
        from management.models import PendingChange
        return PendingChange.objects.filter(
            status='pending'
        ).select_related('establishment', 'requested_by')
    
    @staticmethod
    def get_all_pending_counts() -> dict:
        """Get counts of all pending items."""
        return {
            'partners': ApprovalEngine.get_pending_partners().count(),
            'establishments': ApprovalEngine.get_pending_establishments().count(),
            'changes': ApprovalEngine.get_pending_changes().count(),
        }
