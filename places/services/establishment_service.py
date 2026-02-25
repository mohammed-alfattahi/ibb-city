"""
Establishment Service - Business Logic for Establishment Management.

This service handles establishment creation, updates, suspension, and status toggling.
"""
from django.utils import timezone
from django.db.models import Model
from decimal import Decimal
from datetime import date, datetime
from places.models import Establishment
from management.models import AuditLog
# Package 2 fix: Use modular notifications instead of broken event-driven system
from interactions.notifications.admin import AdminNotifications
from interactions.notifications.partner import PartnerNotifications
from interactions.notifications.notification_service import NotificationService  # For emit_event
# Local imports used in methods to avoid circular dependency with RequestManager


def normalize_change_value(value):
    """
    Normalize values for JSON serialization (Bug 3.3 fix).
    Converts Model instances to PKs, Decimals to strings, dates to ISO format.
    """
    if value is None:
        return None
    if isinstance(value, Model):
        return value.pk
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, 'pk'):  # QuerySet or related manager
        return value.pk
    return value


class EstablishmentService:
    """Service for handling establishment operations."""
    
    @staticmethod
    def handle_update(establishment: Establishment, form_instance, changed_data: list, cleaned_data: dict, user) -> tuple[bool, str, bool]:
        """
        Handle establishment update with sensitive field detection and audit logging.
        
        Uses field-level approval via PendingChangeService for name/description.
        Other sensitive fields use RequestManager for backward compatibility.
        Non-sensitive changes apply immediately with PartnerUpdateService logging.
        
        Args:
            establishment: The existing Establishment instance (database version)
            form_instance: The form instance with new data (unsaved)
            changed_data: List of changed field names (from form.changed_data)
            cleaned_data: Dictionary of cleaned form data
            user: The user performing the update
            
        Returns:
            tuple: (success: bool, message: str, has_sensitive_changes: bool)
        """
        from management.services.pending_change_service import PendingChangeService
        from places.services.partner_update_service import PartnerUpdateService
        from ibb_guide.core_utils import get_client_ip
        
        if not changed_data:
            return True, "No changes detected.", False
        
        # Field-level approval fields (new system)
        FIELD_LEVEL_APPROVAL_FIELDS = ['name', 'description']
        
        # Other sensitive fields (legacy system via RequestManager)
        OTHER_SENSITIVE_FIELDS = ['category', 'latitude', 'longitude']
        
        # Define all sensitive fields
        SENSITIVE_FIELDS = FIELD_LEVEL_APPROVAL_FIELDS + OTHER_SENSITIVE_FIELDS
            
        # Classification
        field_level_changes = {}  # name, description → PendingChange
        other_sensitive_changes = {}  # category, coords → RequestManager
        non_sensitive_changes = {}
        original_data = {}
        raw_original_data = {}
        new_data_log = {}
        
        for field in changed_data:
            # Get original value from form.initial or DB
            if hasattr(form_instance, 'initial') and field in form_instance.initial:
                old_val = form_instance.initial[field]
            else:
                old_val = Establishment.objects.filter(pk=establishment.pk).values_list(field, flat=True).first()
            new_val = cleaned_data.get(field)
            
            # Serialize for audit
            original_data[field] = str(old_val)
            raw_original_data[field] = old_val
            new_data_log[field] = str(new_val)
            
            if field in FIELD_LEVEL_APPROVAL_FIELDS:
                field_level_changes[field] = (old_val, new_val)
            elif field in OTHER_SENSITIVE_FIELDS:
                other_sensitive_changes[field] = new_val
            else:
                non_sensitive_changes[field] = (old_val, new_val)

        has_sensitive_changes = bool(field_level_changes or other_sensitive_changes)
        messages_list = []
        
        # 1. Handle field-level approval changes (name, description) via PendingChangeService
        if field_level_changes:
            for field_name, (old_val, new_val) in field_level_changes.items():
                success, msg, _ = PendingChangeService.request_sensitive_change(
                    user=user,
                    establishment=establishment,
                    field_name=field_name,
                    new_value=str(new_val) if new_val else '',
                    ip=None  # IP is handled at view level
                )
                if success:
                    messages_list.append(msg)
        
        # 2. Handle other sensitive changes (category, coords) via legacy RequestManager
        if other_sensitive_changes:
            from management.utils import RequestManager
            
            # Normalize values for JSON serialization
            normalized_changes = {
                k: normalize_change_value(v) for k, v in other_sensitive_changes.items()
            }
            
            RequestManager.submit_update_request(
                user=user,
                target_object=establishment,
                changes=normalized_changes,
                description="Establishment Details Update (Category/Location)"
            )
            
            AdminNotifications.notify_establishment_update_request(establishment)
            
            AuditLog.objects.create(
                user=user,
                action='REQUEST_UPDATE',
                table_name='Establishment',
                record_id=str(establishment.pk),
                old_values={k: original_data[k] for k in other_sensitive_changes},
                new_values=other_sensitive_changes
            )
            messages_list.append("تم إرسال تغييرات الموقع/الفئة للمراجعة")

        # 3. Handle non-sensitive changes (direct save + logging)
        if non_sensitive_changes or (changed_data and not has_sensitive_changes): 
            instance = form_instance.save(commit=False)
            
            # Revert ALL sensitive fields to original values before saving
            for field in list(field_level_changes.keys()) + list(other_sensitive_changes.keys()):
                if field in raw_original_data:
                    setattr(instance, field, raw_original_data[field])
            
            instance.save()
            form_instance.save_m2m()  # Handle M2M relations
            
            if non_sensitive_changes:
                # Log batch changes via PartnerUpdateService
                changes_for_logging = {}
                for field, (old_val, new_val) in non_sensitive_changes.items():
                    if field in PartnerUpdateService.IMMEDIATE_FIELDS:
                        changes_for_logging[field] = (old_val, new_val)
                
                if changes_for_logging:
                    PartnerUpdateService.log_batch_changes(
                        user=user,
                        establishment=establishment,
                        changes=changes_for_logging,
                        ip=None
                    )
                else:
                    # Fallback audit log for other non-sensitive fields
                    AuditLog.objects.create(
                        user=user,
                        action='UPDATE',
                        table_name='Establishment',
                        record_id=str(establishment.pk),
                        old_values=original_data,
                        new_values=new_data_log
                    )
                
                
                messages_list.append("تم حفظ التغييرات الفورية بنجاح")
                
                # Notify Admin about info update
                AdminNotifications.notify_establishment_info_update(
                    establishment, 
                    'info', 
                    f"تم تحديث الحقول: {', '.join(non_sensitive_changes.keys())}"
                )

        # 4. Construct final message
        if has_sensitive_changes:
            msg = "تم إرسال التغييرات الحساسة للمراجعة. "
            if non_sensitive_changes:
                msg += "التغييرات الأخرى تم حفظها فوراً."
        else:
            msg = "تم حفظ جميع التغييرات بنجاح."
            
        return True, msg, has_sensitive_changes

    @staticmethod
    def suspend(establishment: Establishment, admin_user, reason: str, end_date=None) -> tuple[bool, str]:
        """Suspend an establishment temporarily."""
        establishment.is_suspended = True
        establishment.is_active = False  # Hide from public
        establishment.suspension_reason = reason
        establishment.suspension_end_date = end_date or None
        establishment.save()
        
        AuditLog.objects.create(
            user=admin_user,
            action='SUSPEND_ESTABLISHMENT',
            table_name='Establishment',
            record_id=str(establishment.pk),
            reason=reason,
            new_values={'is_suspended': True, 'end_date': str(end_date)}
        )
        
        # Use new NotificationService
        NotificationService.emit_event(
            event_name='ESTABLISHMENT_SUSPENDED',
            payload={'place_name': establishment.name, 'reason': reason},
            audience_criteria={'user_id': establishment.owner.id},
            priority='high'
        )
        
        return True, f"Establishment {establishment.name} suspended."
    
    @staticmethod
    def unsuspend(establishment: Establishment, admin_user) -> tuple[bool, str]:
        """Remove suspension from an establishment."""
        establishment.is_suspended = False
        establishment.is_active = True
        establishment.suspension_reason = ""
        establishment.suspension_end_date = None
        establishment.save()
        
        AuditLog.objects.create(
            user=admin_user,
            action='UNSUSPEND_ESTABLISHMENT',
            table_name='Establishment',
            record_id=str(establishment.pk),
            new_values={'is_suspended': False}
        )
        
        # Notify partner that suspension was lifted
        PartnerNotifications.notify_establishment_unsuspended(establishment)
        
        return True, f"Establishment {establishment.name} unsuspended."
    
    @staticmethod
    def toggle_open_status(establishment: Establishment, owner_user) -> tuple[bool, str]:
        """Toggle the open/closed status of an establishment."""
        if establishment.owner != owner_user and not owner_user.is_superuser:
            return False, "Permission denied.", None
        
        old_status = establishment.is_open_now
        establishment.is_open_now = not establishment.is_open_now
        establishment.save(update_fields=['is_open_now'])
        
        # AuditLog
        AuditLog.objects.create(
            user=owner_user,
            action='TOGGLE_STATUS',
            table_name='Establishment',
            record_id=str(establishment.pk),
            old_values={'is_open_now': old_status},
            new_values={'is_open_now': establishment.is_open_now}
        )
        
        # Notification to partner about status change
        PartnerNotifications.notify_establishment_status_changed(establishment)
        
        status_text = "مفتوح" if establishment.is_open_status else "مغلق"
        return True, f"المنشأة الآن {status_text}", establishment.is_open_status

    @staticmethod
    def classify_changes(establishment: Establishment, new_data: dict) -> tuple[dict, dict]:
        """Legacy helper - kept for compatibility."""
        sensitive_changes = {}
        non_sensitive_changes = {}
        
        SENSITIVE_FIELDS = getattr(Establishment, 'SENSITIVE_FIELDS', ['name', 'category', 'latitude', 'longitude'])

        for field, new_value in new_data.items():
            if hasattr(establishment, field):
                old_value = getattr(establishment, field)
                if str(old_value) == str(new_value):
                    continue
            
            if field in SENSITIVE_FIELDS:
                sensitive_changes[field] = new_value
            else:
                non_sensitive_changes[field] = new_value
        
        return sensitive_changes, non_sensitive_changes
    
    @staticmethod
    def apply_non_sensitive_updates(establishment: Establishment, changes: dict, user) -> tuple[bool, str]:
        """Legacy helper - handled by handle_update now."""
        if not changes:
            return True, "No non-sensitive changes to apply."
        
        for field, value in changes.items():
            if hasattr(establishment, field):
                setattr(establishment, field, value)
        
        establishment.save()
        
        AuditLog.objects.create(
            user=user,
            action='IMMEDIATE_UPDATE',
            table_name='Establishment',
            record_id=str(establishment.pk),
            new_values=changes
        )
        
        return True, f"تم تحديث {len(changes)} حقل/حقول فوراً."
    
    @staticmethod
    def queue_sensitive_updates(establishment: Establishment, changes: dict, user) -> tuple[bool, str]:
        """Legacy helper - handled by handle_update now."""
        if not changes:
            return True, "No sensitive changes to queue."
        
        from management.utils import RequestManager
        
        RequestManager.submit_update_request(
            user=user,
            target_object=establishment,
            changes=changes,
            description="تعديل على حقول حساسة تتطلب موافقة الإدارة"
        )
        
        NotificationService.emit_event(
            event_name='REQUEST_UPDATE',
            payload={'target': establishment.name},
            audience_criteria={'role': 'staff'}
        )
        
        return True, f"تم إرسال {len(changes)} حقل/حقول للموافقة من الإدارة."

    @staticmethod
    def update_rating(establishment_id: int):
        """Recalculate and update the average rating for an establishment."""
        from interactions.models import Review
        from django.db import models
        
        # Only count visible reviews
        avg_rating = Review.objects.filter(
            place_id=establishment_id,
            visibility_state='visible'
        ).aggregate(rating_avg=models.Avg('rating'))['rating_avg']
        
        # Update using Place to handle inheritance properly
        Place.objects.filter(pk=establishment_id).update(
            avg_rating=round(avg_rating, 2) if avg_rating else 0.0
        )

    @staticmethod
    def create_establishment(user, cleaned_data) -> tuple[Establishment, str]:
        """
        Create a new establishment pending approval.
        Handles Request creation and Notifications.
        """
        from django.contrib.contenttypes.models import ContentType
        from management.models import Request, RequestStatusLog
        
        # 1. Create Establishment (Inactive)
        establishment = Establishment.objects.create(
            owner=user,
            is_active=False, # Require Admin Approval
            **cleaned_data
        )
        
        # 2. Create ADD_PLACE Request
        request_obj = Request.objects.create(
            user=user,
            request_type='ADD_PLACE',
            target_content_type=ContentType.objects.get_for_model(Establishment),
            target_object_id=establishment.pk,
            description=f"طلب إضافة منشأة: {establishment.name}",
            status='PENDING'
        )
        
        # 3. Log Status
        RequestStatusLog.log_status_change(
            request=request_obj,
            new_status='PENDING',
            changed_by=user,
            message='تم إنشاء طلب إضافة منشأة جديدة'
        )
        
        # 4. Notify
        # 4. Notify - handled by signals (interactions/signals.py) to avoid duplication
        # AdminNotifications.notify_new_establishment_request(establishment)
        # PartnerNotifications.notify_establishment_request_received(establishment)
        
        return establishment, "تم إنشاء المنشأة بنجاح! سيقوم الفريق بمراجعة طلبك وتفعيل المنشأة قريباً."

    @staticmethod
    def create_unit(user, establishment, cleaned_data) -> tuple[object, str]:
        """Create a unit and log audit/notify admin."""
        from places.models import EstablishmentUnit
        from ibb_guide.core_utils import create_audit_log
        
        unit = EstablishmentUnit.objects.create(
            establishment=establishment,
            **cleaned_data
        )
        
        # AdminNotifications.notify_establishment_info_update(establishment, 'unit', f"تم إنشاء وحدة جديدة: {unit.name}")
        
        create_audit_log(
            user, 
            'CREATE', 
            'EstablishmentUnit', 
            unit.pk, 
            new_val={'name': unit.name}
        )
        return unit, "Unit created successfully."

    @staticmethod
    def update_unit(user, unit, cleaned_data) -> tuple[object, str]:
        """Update a unit and log audit/notify admin."""
        from ibb_guide.core_utils import create_audit_log
        
        old_data = {'name': unit.name, 'price': str(unit.price)}
        
        for field, value in cleaned_data.items():
            setattr(unit, field, value)
        unit.save()
        
        # AdminNotifications.notify_establishment_info_update(
        #     unit.establishment, 
        #     'unit', 
        #     f"تم تحديث الوحدة: {unit.name}"
        # )
        
        create_audit_log(
            user, 
            'UPDATE', 
            'EstablishmentUnit', 
            unit.pk, 
            old_val=old_data, 
            new_val={'name': unit.name, 'price': str(unit.price)}
        )
        return unit, "Unit updated successfully."

    @staticmethod
    def delete_unit(user, unit) -> str:
        """Delete a unit and log audit/notify admin."""
        from ibb_guide.core_utils import create_audit_log
        
        establishment = unit.establishment
        audit_data = {'name': unit.name}
        unit_id = unit.pk
        
        unit.delete()
        
        # AdminNotifications.notify_establishment_info_update(
        #     establishment, 
        #     'unit', 
        #     f"تم حذف الوحدة: {unit.name}"
        # )
        
        create_audit_log(
            user, 
            'DELETE', 
            'EstablishmentUnit', 
            unit_id, 
            old_val=audit_data
        )
        return "Unit deleted successfully."

    @staticmethod
    def add_media(user, establishment, file_url) -> tuple[object, str]:
        """Add media to establishment."""
        from places.models import PlaceMedia
        from ibb_guide.core_utils import create_audit_log
        
        media = PlaceMedia.objects.create(
            place=establishment,
            media_url=file_url
        )
        
        AdminNotifications.notify_establishment_info_update(establishment, 'media', "تم إضافة صورة/وسائط جديدة")
        
        create_audit_log(
            user, 
            'CREATE', 
            'PlaceMedia', 
            media.pk, 
            new_val={'url': str(media.media_url)}
        )
        return media, "Media added successfully."

    @staticmethod
    def delete_media(user, media) -> str:
        """Delete media from establishment."""
        from ibb_guide.core_utils import create_audit_log
        
        establishment = media.place.establishment
        media_id = media.pk
        old_url = str(media.media_url)
        
        media.delete()
        
        AdminNotifications.notify_establishment_info_update(establishment, 'media', "تم حذف صورة/وسائط")
        
        create_audit_log(
            user, 
            'DELETE', 
            'PlaceMedia', 
            media_id, 
            old_val={'url': old_url}
        )
        return "Media deleted successfully."
