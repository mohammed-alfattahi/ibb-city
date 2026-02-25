"""
Pending Change Service
خدمة التغييرات المعلقة

Handles field-level approval workflow for sensitive partner changes.
Sensitive fields (name, description) require tourism office approval.
"""
import logging
from typing import Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from management.models import PendingChange, AuditLog
from interactions.models import Notification
from users.models import User

logger = logging.getLogger(__name__)


class PendingChangeService:
    """
    Domain Service for handling sensitive field changes requiring approval.
    
    Sensitive fields that require approval:
    - name: Establishment name
    - description: Establishment description
    
    Workflow:
    1. Partner requests change → PendingChange created with status='pending'
    2. Office notified → Admin reviews in dashboard
    3. Admin approves → Field updated, partner notified
    4. Admin rejects → Partner notified with reason
    """
    
    SENSITIVE_FIELDS = ['name', 'description']
    
    @staticmethod
    def is_sensitive_field(field_name: str) -> bool:
        """Check if a field requires approval."""
        return field_name in PendingChangeService.SENSITIVE_FIELDS
    
    @staticmethod
    @transaction.atomic
    def request_sensitive_change(
        user: User,
        establishment,
        field_name: str,
        new_value: str,
        ip: Optional[str] = None
    ) -> Tuple[bool, str, Optional[PendingChange]]:
        """
        Create a pending change request for a sensitive field.
        
        Args:
            user: The partner user requesting the change
            establishment: The Establishment instance
            field_name: Field name ('name' or 'description')
            new_value: The new value being requested
            ip: Client IP address for audit
            
        Returns:
            Tuple of (success, message, pending_change or None)
        """
        if field_name not in PendingChangeService.SENSITIVE_FIELDS:
            return False, f"الحقل '{field_name}' لا يتطلب موافقة", None
        
        # Get current value
        old_value = getattr(establishment, field_name, '')
        
        # Check if value actually changed
        if old_value == new_value:
            return False, "لا يوجد تغيير في القيمة", None
        
        # Check for existing pending change for same field
        existing = PendingChange.objects.filter(
            establishment=establishment,
            field_name=field_name,
            status='pending'
        ).first()
        
        if existing:
            # Update existing pending change
            existing.new_value = new_value
            existing.client_ip = ip
            existing.save(update_fields=['new_value', 'client_ip', 'updated_at'])
            pending_change = existing
            logger.info(f"Updated existing PendingChange {existing.id} for {establishment}")
        else:
            # Create new pending change
            pending_change = PendingChange.objects.create(
                entity_type='establishment',
                establishment=establishment,
                field_name=field_name,
                old_value=old_value or '',
                new_value=new_value,
                requested_by=user,
                client_ip=ip
            )
            logger.info(f"Created PendingChange {pending_change.id} for {establishment}")
        
        # Write audit log
        AuditLog.objects.create(
            user=user,
            action='REQUEST_CHANGE',
            table_name='places_establishment',
            record_id=str(establishment.pk),
            old_values={field_name: old_value},
            new_values={field_name: new_value},
            ip_address=ip,
            reason=f"طلب تغيير {pending_change.get_field_name_display()}"
        )
        
        # Notify tourism office (all staff users)
        PendingChangeService._notify_office_of_request(pending_change)
        
        field_display = pending_change.get_field_name_display()
        return True, f"تم إرسال طلب تغيير {field_display} للمراجعة", pending_change
    
    @staticmethod
    @transaction.atomic
    def approve_change(
        admin_user: User,
        pending_change: PendingChange,
        ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Approve and apply a pending change.
        
        Args:
            admin_user: The admin user approving the change
            pending_change: The PendingChange instance to approve
            ip: Client IP address for audit
            
        Returns:
            Tuple of (success, message)
        """
        if not pending_change.is_pending:
            return False, f"التغيير بحالة '{pending_change.get_status_display()}' بالفعل"
        
        establishment = pending_change.establishment
        field_name = pending_change.field_name
        old_value = getattr(establishment, field_name, '')
        new_value = pending_change.new_value
        
        # Apply the change to the establishment
        setattr(establishment, field_name, new_value)
        establishment.save(update_fields=[field_name, 'updated_at'])
        
        # Update pending change status
        pending_change.status = 'approved'
        pending_change.reviewed_by = admin_user
        pending_change.reviewed_at = timezone.now()
        pending_change.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        
        # Write audit log
        AuditLog.objects.create(
            user=admin_user,
            action='APPROVE_CHANGE',
            table_name='places_establishment',
            record_id=str(establishment.pk),
            old_values={field_name: old_value},
            new_values={field_name: new_value},
            ip_address=ip,
            reason=f"الموافقة على تغيير {pending_change.get_field_name_display()}"
        )
        
        # Notify partner
        PendingChangeService._notify_partner_of_decision(pending_change, approved=True)
        
        logger.info(f"PendingChange {pending_change.id} approved by {admin_user}")
        return True, f"تمت الموافقة على تغيير {pending_change.get_field_name_display()}"
    
    @staticmethod
    @transaction.atomic
    def reject_change(
        admin_user: User,
        pending_change: PendingChange,
        note: str = '',
        ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Reject a pending change with optional note.
        
        Args:
            admin_user: The admin user rejecting the change
            pending_change: The PendingChange instance to reject
            note: Reason for rejection (visible to partner)
            ip: Client IP address for audit
            
        Returns:
            Tuple of (success, message)
        """
        if not pending_change.is_pending:
            return False, f"التغيير بحالة '{pending_change.get_status_display()}' بالفعل"
        
        # Update pending change status
        pending_change.status = 'rejected'
        pending_change.reviewed_by = admin_user
        pending_change.reviewed_at = timezone.now()
        pending_change.review_note = note
        pending_change.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at'])
        
        # Write audit log
        AuditLog.objects.create(
            user=admin_user,
            action='REJECT_CHANGE',
            table_name='management_pendingchange',
            record_id=str(pending_change.pk),
            old_values={'status': 'pending'},
            new_values={'status': 'rejected'},
            ip_address=ip,
            reason=note or f"رفض تغيير {pending_change.get_field_name_display()}"
        )
        
        # Notify partner with rejection reason
        PendingChangeService._notify_partner_of_decision(pending_change, approved=False, note=note)
        
        logger.info(f"PendingChange {pending_change.id} rejected by {admin_user}: {note}")
        return True, f"تم رفض تغيير {pending_change.get_field_name_display()}"
    
    @staticmethod
    def get_pending_changes_for_establishment(establishment) -> list:
        """Get all pending changes for an establishment."""
        return list(PendingChange.objects.filter(
            establishment=establishment,
            status='pending'
        ).order_by('-created_at'))
    
    @staticmethod
    def get_all_pending_changes():
        """Get all pending changes for admin review."""
        return PendingChange.objects.filter(status='pending').select_related(
            'establishment', 'requested_by'
        ).order_by('-created_at')
    
    @staticmethod
    def _notify_office_of_request(pending_change: PendingChange):
        """Send notification to tourism office about new pending change."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all staff users (tourism office)
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        
        establishment = pending_change.establishment
        partner = pending_change.requested_by
        field_display = pending_change.get_field_name_display()
        
        for staff_user in staff_users:
            Notification.objects.create(
                recipient=staff_user,
                notification_type='pending_change_requested',
                title='طلب تغيير معلق جديد',
                message=f"قدم الشريك {partner.username} طلب تغيير {field_display} للمنشأة '{establishment.name}'",
                # Note: content_type/object_id omitted because PendingChange uses UUID PK which overflows IntegerField
                action_url=f'/custom-admin/pending-changes/'
            )
    
    @staticmethod
    def _notify_partner_of_decision(pending_change: PendingChange, approved: bool, note: str = ''):
        """Send notification to partner about decision."""
        partner = pending_change.requested_by
        establishment = pending_change.establishment
        field_display = pending_change.get_field_name_display()
        
        if approved:
            notification_type = 'pending_change_approved'
            title = 'تمت الموافقة على طلب التغيير'
            message = f"تمت الموافقة على تغيير {field_display} للمنشأة '{establishment.name}'"
        else:
            notification_type = 'pending_change_rejected'
            title = 'تم رفض طلب التغيير'
            message = f"تم رفض تغيير {field_display} للمنشأة '{establishment.name}'"
            if note:
                message += f"\nالسبب: {note}"
        
        Notification.objects.create(
            recipient=partner,
            notification_type=notification_type,
            title=title,
            message=message,
            content_type=ContentType.objects.get_for_model(pending_change.establishment),
            object_id=establishment.pk,
            action_url=f'/partner/establishments/{establishment.pk}/'
        )
