from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from management.models import Request, ApprovalDecision, RequestStatusLog
from interactions.models import Notification
# Import necessary models for execution
from users.models import User, PartnerProfile, Role
from places.models import Establishment, Place
from interactions.services.review_service import ReviewService # If needed

class ApprovalService:
    """
    Domain Service for handling Administrative Approvals.
    Enforces governance by requiring specific decisions for state changes.
    """

    @staticmethod
    @transaction.atomic
    def assign_request(request_obj, assigned_to_user, assigned_by_user=None):
        """
        Assign a request to a specific user.
        """
        from management.models import ApprovalAssignment
        
        request_obj.assigned_to = assigned_to_user
        request_obj.save()
        
        ApprovalAssignment.objects.create(
            request=request_obj,
            assigned_to=assigned_to_user,
            assigned_by=assigned_by_user
        )
        
        # Notify Assignee
        Notification.objects.create(
            recipient=assigned_to_user,
            notification_type='system_alert',
            title='تم إسناد طلب جديد إليك',
            message=f"طلب {request_obj.get_request_type_display()} من {request_obj.user}",
            action_url=f"/admin/requests/{request_obj.pk}/" # Hypothetical link
        )
        return True

    @staticmethod
    @transaction.atomic
    def process_decision(request_obj, admin_user, decision, reason, conditions="", deadline=None, document=None):
        """
        Process an administrative decision on a Request.
        
        Args:
            request_obj: The Request instance.
            admin_user: The admin User making the decision.
            decision: One of ApprovalDecision.DECISION_TYPES (APPROVE, REJECT, etc.).
            reason: Justification for the decision.
        """
        
        # 1. Validation
        new_status = ApprovalService._map_decision_to_status(decision)
        if request_obj.status == new_status:
            # Idempotency check: If status is already same, log info and return existing decision if possible or none
            # We will just return None to indicate no-op, or fetch latest decision
            return request_obj.decisions.order_by('-created_at').first()

        if request_obj.status in ['APPROVED', 'REJECTED'] and decision in ['APPROVE', 'REJECT']:
            # Allow modifying decisions? For now, strict.
            raise ValidationError("This request has already been finalized.")

        # 2. Record Decision (Audit)
        decision_record = ApprovalDecision.record_decision(
            request=request_obj,
            user=admin_user,
            decision=decision,
            reason=reason,
            conditions=conditions,
            deadline=deadline,
            document=document
        )

        # 3. Update Request Status
        old_status = request_obj.status
        new_status = ApprovalService._map_decision_to_status(decision)
        request_obj.status = new_status
        request_obj.reviewed_by = admin_user
        request_obj.reviewed_at = timezone.now()
        
        if decision == 'REJECT':
            request_obj.admin_response = reason
        elif decision == 'CONDITIONAL':
            request_obj.conditions = conditions
            request_obj.deadline = deadline
            
        request_obj.save()

        # 4. Log Status Change
        RequestStatusLog.log_status_change(
            request=request_obj,
            new_status=new_status,
            changed_by=admin_user,
            message=f"Decision: {decision} - {reason}",
            internal_note=f"Formal decision ID: {decision_record.pk}"
        )

        # 5. Execute Business Logic (If Approved)
        if decision == 'APPROVE':
            ApprovalService._execute_approval_logic(request_obj)
        elif decision == 'REVOKE':
             ApprovalService._execute_revocation_logic(request_obj)

        # 6. Notify User
        ApprovalService._notify_user(request_obj, decision, reason)

        return decision_record

    @staticmethod
    def _map_decision_to_status(decision):
        mapping = {
            'APPROVE': 'APPROVED',
            'REJECT': 'REJECTED',
            'REQUEST_INFO': 'NEEDS_INFO',
            'CONDITIONAL': 'CONDITIONAL_APPROVAL',
            'REVOKE': 'REJECTED', # Or specialized status
        }
        return mapping.get(decision, 'PENDING')

    @staticmethod
    def _execute_approval_logic(request_obj):
        """Route to specific execution strategy based on request type."""
        handlers = {
            'UPGRADE_PARTNER': ApprovalService._handle_partner_upgrade,
            'ADD_PLACE': ApprovalService._handle_add_place,
            'UPDATE_INFO': ApprovalService._handle_update_info,
            'VERIFY_ESTABLISHMENT': ApprovalService._handle_verification,
            'CREATE_AD': ApprovalService._handle_ad_approval,
            # Add more handlers
        }
        
        handler = handlers.get(request_obj.request_type)
        if handler:
            handler(request_obj)
        else:
            # Generic handler or pass
            pass

    @staticmethod
    def _handle_partner_upgrade(request_obj):
        target_user = request_obj.user
        # Upgrade logic
        try:
            profile = target_user.partnerprofile
            profile.status = 'approved'
            profile.is_approved = True
            profile.reviewed_by = request_obj.reviewed_by
            profile.reviewed_at = timezone.now()
            profile.save()
            
            # Ensure Role is Partner
            partner_role, _ = Role.objects.get_or_create(name='Partner')
            target_user.role = partner_role
            target_user.save()
        except Exception as e:
            raise ValidationError(f"Failed to execute partner upgrade: {e}")

    @staticmethod
    def _handle_add_place(request_obj):
        target = request_obj.target_object
        if isinstance(target, (Place, Establishment)):
            target.is_active = True
            if hasattr(target, 'license_status'):
                target.license_status = 'Approved'
            target.save()

    @staticmethod
    def _handle_update_info(request_obj):
        """Apply pending changes to the object. Step 3.2.8 fix: Safe FK handling."""
        target = request_obj.target_object
        changes = request_obj.changes or {}
        
        for field, value in changes.items():
            if hasattr(target, field):
                try:
                    model_field = target._meta.get_field(field)
                    # Step 3.2.8 fix: Handle ForeignKey safely
                    if model_field.is_relation and model_field.many_to_one:
                        # Set via field_id to avoid lookup issues
                        setattr(target, f"{field}_id", int(value) if value else None)
                    else:
                        setattr(target, field, value)
                except Exception:
                    # Fallback to direct set
                    setattr(target, field, value)
        
        target.save()
        # Clear pending updates if it's an establishment
        if hasattr(target, 'pending_updates'):
            target.pending_updates = {}
            target.save()

    @staticmethod
    def _handle_verification(request_obj):
        target = request_obj.target_object
        if hasattr(target, 'is_verified'):
            target.is_verified = True
            target.save()

    @staticmethod
    def _handle_ad_approval(request_obj):
        target = request_obj.target_object
        # Assuming target is Advertisement model (needs import or generic access)
        if hasattr(target, 'status'):
            target.status = 'active'
            # Set end_date if needed
            target.save()

    @staticmethod
    def _execute_revocation_logic(request_obj):
        # Reverse logic if needed
        pass

    @staticmethod
    def _notify_user(request_obj, decision, reason):
        title_map = {
            'APPROVE': '✅ تمت الموافقة على طلبك',
            'REJECT': '❌ تم رفض طلبك',
            'REQUEST_INFO': '📝 مطلوب معلومات إضافية',
            'CONDITIONAL': '⚠️ موافقة مشروطة',
        }
        
        Notification.objects.create(
            recipient=request_obj.user,
            notification_type='request_update',
            title=title_map.get(decision, 'تحديث على طلبك'),
            message=f"تم تحديث حالة طلبك ({request_obj.get_request_type_display()}). ملاحظات: {reason}",
            action_url=f"/partners/requests/{request_obj.pk}/" # Partner portal link
        )
