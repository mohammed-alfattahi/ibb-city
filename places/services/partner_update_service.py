"""
Partner Update Service
خدمة تحديثات الشريك

Handles immediate field updates that don't require approval.
These changes apply instantly but must be logged and notify the tourism office.
"""
import logging
from typing import Tuple, Optional, Any
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from management.models import AuditLog
from interactions.models import Notification
from users.models import User

logger = logging.getLogger(__name__)


class PartnerUpdateService:
    """
    Domain Service for handling immediate partner updates.
    
    Immediate fields (no approval needed):
    - contact_info: Phone, email, social links
    - working_hours: Opening hours JSON
    - is_open_status: Manual open/closed toggle
    - price_range: Price tier
    - opening_hours_text: Human-readable hours
    - cover_image: Establishment cover photo
    - amenities: Available amenities (M2M)
    
    All changes:
    1. Apply immediately to the establishment
    2. Write audit log (before/after)
    3. Notify tourism office for visibility
    """
    
    IMMEDIATE_FIELDS = [
        'contact_info',
        'working_hours',
        'is_open_status',
        'price_range',
        'opening_hours_text',
        'cover_image',
        'amenities',
        'discounts',       # تخفيضات - بدون موافقة
        'features',        # ميزات - بدون موافقة
        'units',           # وحدات - بدون موافقة
        'media',           # صور - بدون موافقة
    ]
    
    # Human-readable field names for notifications
    FIELD_DISPLAY_NAMES = {
        'contact_info': 'معلومات الاتصال',
        'working_hours': 'ساعات العمل',
        'is_open_status': 'حالة الفتح/الإغلاق',
        'price_range': 'نطاق الأسعار',
        'opening_hours_text': 'نص ساعات العمل',
        'cover_image': 'صورة الغلاف',
        'amenities': 'المرافق والخدمات',
    }
    
    @staticmethod
    def is_immediate_field(field_name: str) -> bool:
        """Check if a field can be updated immediately without approval."""
        return field_name in PartnerUpdateService.IMMEDIATE_FIELDS
    
    @staticmethod
    def get_field_display_name(field_name: str) -> str:
        """Get Arabic display name for a field."""
        return PartnerUpdateService.FIELD_DISPLAY_NAMES.get(field_name, field_name)
    
    @staticmethod
    @transaction.atomic
    def apply_immediate_change(
        user: User,
        establishment,
        field_name: str,
        old_value: Any,
        new_value: Any,
        ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Apply an immediate change, write audit log, and notify office.
        
        Args:
            user: The partner user making the change
            establishment: The Establishment instance
            field_name: Field name being changed
            old_value: Previous value (for audit)
            new_value: New value being applied
            ip: Client IP address for audit
            
        Returns:
            Tuple of (success, message)
        """
        if field_name not in PartnerUpdateService.IMMEDIATE_FIELDS:
            return False, f"الحقل '{field_name}' يتطلب موافقة"
        
        field_display = PartnerUpdateService.get_field_display_name(field_name)
        
        # Serialize values for audit log
        old_serialized = PartnerUpdateService._serialize_value(old_value)
        new_serialized = PartnerUpdateService._serialize_value(new_value)
        
        # Write audit log
        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            table_name='places_establishment',
            record_id=str(establishment.pk),
            old_values={field_name: old_serialized},
            new_values={field_name: new_serialized},
            ip_address=ip,
            reason=f"تحديث فوري: {field_display}"
        )
        
        # Notify tourism office
        PartnerUpdateService._notify_office_of_update(
            user, establishment, field_name, old_serialized, new_serialized
        )
        
        # Notify followers
        PartnerUpdateService._notify_followers(establishment, field_name, new_value)
        
        logger.info(f"Immediate change applied: {field_name} on {establishment} by {user}")
        return True, f"تم تحديث {field_display} بنجاح"
    
    @staticmethod
    @transaction.atomic
    def log_batch_changes(
        user: User,
        establishment,
        changes: dict,
        ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Log multiple immediate changes at once.
        
        Args:
            user: The partner user making changes
            establishment: The Establishment instance
            changes: Dict of {field_name: (old_value, new_value)}
            ip: Client IP address for audit
            
        Returns:
            Tuple of (success, message listing changed fields)
        """
        if not changes:
            return False, "لا توجد تغييرات لتسجيلها"
        
        changed_fields = []
        
        for field_name, (old_value, new_value) in changes.items():
            if field_name in PartnerUpdateService.IMMEDIATE_FIELDS:
                old_serialized = PartnerUpdateService._serialize_value(old_value)
                new_serialized = PartnerUpdateService._serialize_value(new_value)
                
                # Write individual audit log
                AuditLog.objects.create(
                    user=user,
                    action='UPDATE',
                    table_name='places_establishment',
                    record_id=str(establishment.pk),
                    old_values={field_name: old_serialized},
                    new_values={field_name: new_serialized},
                    ip_address=ip,
                    reason=f"تحديث فوري: {PartnerUpdateService.get_field_display_name(field_name)}"
                )
                changed_fields.append(PartnerUpdateService.get_field_display_name(field_name))
        
        if changed_fields:
            # Send single notification for batch update
            PartnerUpdateService._notify_office_of_batch_update(
                user, establishment, changed_fields
            )
            
            # Notify followers for each interesting field (or batch them? simple loop for now)
            for field_name in changes.keys():
                # Get new value from tuple (old, new)
                new_val = changes[field_name][1]
                PartnerUpdateService._notify_followers(establishment, field_name, new_val)
        
        fields_str = ', '.join(changed_fields)
        logger.info(f"Batch changes applied: {fields_str} on {establishment} by {user}")
        return True, f"تم تحديث: {fields_str}"
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a value for storage in audit log."""
        if value is None:
            return None
        if hasattr(value, 'url'):  # FileField/ImageField
            return str(value.url) if value else None
        if hasattr(value, 'all'):  # M2M field
            return [str(obj) for obj in value.all()]
        if hasattr(value, 'isoformat'):  # datetime/date
            return value.isoformat()
        try:
            # Try JSON serialization
            import json
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            return str(value)
    
    @staticmethod
    def _notify_office_of_update(user, establishment, field_name, old_value, new_value):
        """Send notification to tourism office about field update."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        field_display = PartnerUpdateService.get_field_display_name(field_name)
        
        for staff_user in staff_users:
            Notification.objects.create(
                recipient=staff_user,
                notification_type='partner_field_update',
                title='تحديث حقل المنشأة',
                message=f"قام الشريك {user.username} بتحديث {field_display} للمنشأة '{establishment.name}'",
                content_type=ContentType.objects.get_for_model(establishment),
                object_id=establishment.pk,
                action_url=f'/custom-admin/establishments/{establishment.pk}/'
            )
    
    @staticmethod
    def _notify_office_of_batch_update(user, establishment, changed_fields: list):
        """Send notification to tourism office about batch field updates."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        fields_str = ', '.join(changed_fields)
        
        for staff_user in staff_users:
            Notification.objects.create(
                recipient=staff_user,
                notification_type='partner_field_update',
                title='تحديثات متعددة على المنشأة',
                message=f"قام الشريك {user.username} بتحديث ({fields_str}) للمنشأة '{establishment.name}'",
                content_type=ContentType.objects.get_for_model(establishment),
                object_id=establishment.pk,
                action_url=f'/custom-admin/establishments/{establishment.pk}/'
            )


    @staticmethod
    def _notify_followers(establishment, field_name, new_value):
        """Notify followers about relevant updates."""
        try:
            from interactions.models import EstablishmentFollow, Notification
            from django.utils.translation import gettext as _
            
            # Only notify for interesting fields
            interesting_fields = {
                'discounts': 'favorite_new_offer',
                'is_open_status': 'favorite_reactivated' if new_value is True else 'favorite_suspended',
                'units': 'favorite_new_offer',
            }
            
            if field_name not in interesting_fields:
                return

            followers = EstablishmentFollow.objects.filter(establishment=establishment).select_related('user')
            notif_type = interesting_fields[field_name]
            field_display = PartnerUpdateService.get_field_display_name(field_name)
            
            # Customize message based on field
            if field_name == 'discounts':
                title = f"عرض جديد من {establishment.name}"
                message = f"قام {establishment.name} بتحديث العروض والخصومات. تفقدها الآن!"
            elif field_name == 'is_open_status':
                status = "مفتوح الآن" if new_value else "مغلق مؤقتاً"
                title = f"تحديث حالة {establishment.name}"
                message = f"أصبحت منشأة {establishment.name} {status}."
            else:
                title = f"تحديث جديد من {establishment.name}"
                message = f"قام {establishment.name} بتحديث {field_display}."

            for follow in followers:
                Notification.objects.create(
                    recipient=follow.user,
                    notification_type=notif_type,
                    title=title,
                    message=message,
                    content_type=ContentType.objects.get_for_model(establishment),
                    object_id=establishment.pk,
                    action_url=f'/place/{establishment.pk}/'
                )
        except Exception as e:
            logger.error(f"Error notifying followers: {e}") 
