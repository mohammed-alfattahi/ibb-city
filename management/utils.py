import json
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Request, AuditLog

class RequestManager:
    """
    Utility class to manage Partner Requests (Submission, Approval, Rejection)
    """

    @staticmethod
    def submit_update_request(user, target_object, changes, description=""):
        """
        Submit a request to update an object.
        capture original data for comparison.
        """
        # 1. Capture Original Data
        original_data = {}
        for field in changes.keys():
            if hasattr(target_object, field):
                val = getattr(target_object, field)
                # Handle complex types (ForeignKeys, Files) if needed, simplified for now:
                original_data[field] = str(val) if val is not None else ""
        
        # 2. Create Request
        req = Request.objects.create(
            user=user,
            request_type='UPDATE_INFO',
            target_object=target_object,
            changes=changes,
            original_data=original_data,
            description=description,
            status='PENDING'
        )
        return req

    @staticmethod
    def approve_request(request_id, reviewer, reason="", decision_doc=None):
        """
        Approve a request and apply changes to the target object.
        """
        req = Request.objects.get(pk=request_id)
        if req.status != 'PENDING':
            return False, "Request is not pending."

        target = req.target_object
        if not target:
            return False, "Target object not found."

        # Create snapshot BEFORE applying changes (for rollback capability)
        from .models import EntityVersion
        EntityVersion.create_snapshot(
            target,
            user=reviewer,
            reason="Before applying approved changes",
            related_request=req
        )

        # Apply Changed
        try:
            old_values_log = {}
            new_values_log = {}

            for field, value in req.changes.items():
                if hasattr(target, field):
                    # Handle specific field types if needed (e.g. ForeignKey IDs)
                    # For now assume value is compatible or handled by serializer/form
                    
                    # Store for audit
                    old_val = getattr(target, field)
                    old_values_log[field] = str(old_val)
                    new_values_log[field] = str(value)
                    
                    # Update
                    # Note: For ForeignKeys, we might receive ID.
                    if isinstance(value, int) and field != 'id': 
                        # Try to handle FK assignment by ID if field allows
                        # Check if field is a relation
                        model_field = target._meta.get_field(field)
                        if model_field.is_relation and model_field.many_to_one:
                             setattr(target, f"{field}_id", value)
                        else:
                             setattr(target, field, value)
                    else:
                        setattr(target, field, value)

            target.save()
            
            # Update Request Status
            req.status = 'APPROVED'
            req.reviewed_by = reviewer
            req.reviewed_at = timezone.now()
            req.admin_response = reason # Save reason in Request too
            if decision_doc:
                req.decision_doc = decision_doc
            req.save()
            
            # Log Status Change
            from .models import RequestStatusLog
            RequestStatusLog.log_status_change(
                request=req,
                new_status='APPROVED',
                changed_by=reviewer,
                message="تمت الموافقة على طلبك بنجاح.",
                internal_note=reason
            )
            
            # Audit Log (Decision Log)
            AuditLog.objects.create(
                user=reviewer,
                action='APPROVE_REQUEST',
                table_name=target._meta.model_name,
                record_id=str(target.pk),
                old_values=old_values_log,
                new_values=new_values_log,
                reason=reason,
                attachment=decision_doc
            )

            return True, "Request approved and changes applied."

        except Exception as e:
            return False, f"Error applying changes: {str(e)}"

    @staticmethod
    def reject_request(request_id, reviewer, reason="", decision_doc=None):
        req = Request.objects.get(pk=request_id)
        req.status = 'REJECTED'
        req.reviewed_by = reviewer
        req.reviewed_at = timezone.now()
        req.admin_response = reason
        if decision_doc:
            req.decision_doc = decision_doc
        req.save()
        
        # Log Status Change
        from .models import RequestStatusLog
        RequestStatusLog.log_status_change(
            request=req,
            new_status='REJECTED',
            changed_by=reviewer,
            message=f"تم رفض الطلب. السبب: {reason}",
            internal_note=reason
        )
        
        # Audit Log (Decision Log)
        AuditLog.objects.create(
            user=reviewer,
            action='REJECT_REQUEST',
            table_name=req.target_content_type.model,
            record_id=str(req.target_object_id),
            reason=reason,
            attachment=decision_doc,
            new_values={'status': 'REJECTED'}
        )
        
        return True, "Request rejected."

    @staticmethod
    def request_info(request_id, reviewer, message="", decision_doc=None):
        req = Request.objects.get(pk=request_id)
        req.status = 'NEEDS_INFO'
        req.reviewed_by = reviewer
        req.reviewed_at = timezone.now()
        req.admin_response = message
        if decision_doc:
            req.decision_doc = decision_doc
        req.save()
        
        # Log Status Change
        from .models import RequestStatusLog
        RequestStatusLog.log_status_change(
            request=req,
            new_status='NEEDS_INFO',
            changed_by=reviewer,
            message=f"مطلوب معلومات إضافية: {message}",
            internal_note=message
        )
        
        # Audit Log
        AuditLog.objects.create(
            user=reviewer,
            action='REQUEST_INFO',
            table_name=req.target_content_type.model,
            record_id=str(req.target_object_id),
            reason=message,
            attachment=decision_doc,
            new_values={'status': 'NEEDS_INFO'}
        )
        
        return True, "Info requested."

    @staticmethod
    def conditional_approve(request_id, reviewer, conditions="", deadline=None, reason="", decision_doc=None):
        req = Request.objects.get(pk=request_id)
        req.status = 'CONDITIONAL_APPROVAL'
        req.reviewed_by = reviewer
        req.reviewed_at = timezone.now()
        req.conditions = conditions
        req.deadline = deadline
        req.admin_response = reason
        if decision_doc:
            req.decision_doc = decision_doc
        req.save()

        # Log Status Change
        from .models import RequestStatusLog
        RequestStatusLog.log_status_change(
            request=req,
            new_status='CONDITIONAL_APPROVAL',
            changed_by=reviewer,
            message=f"موافقة مشروطة. الشروط: {conditions}",
            internal_note=reason
        )

        # Audit Log
        AuditLog.objects.create(
            user=reviewer,
            action='CONDITIONAL_APPROVE',
            table_name=req.target_content_type.model,
            record_id=str(req.target_object_id),
            reason=f"Conditions: {conditions} | Reason: {reason}",
            attachment=decision_doc,
            new_values={'status': 'CONDITIONAL_APPROVAL', 'conditions': conditions}
        )
        
        return True, "Request conditionally approved."
