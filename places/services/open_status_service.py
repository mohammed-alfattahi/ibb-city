
from django.utils.translation import gettext as _
from django.utils import timezone
from places.models import Establishment
from management.models import AuditLog
from interactions.notifications.notification_service import NotificationService

class OpenStatusService:
    """
    Service to handle Manual Open/Closed Status for Establishments.
    Business Rules:
    - Only Owner can toggle.
    - Updates are instant.
    - Logs audit trail.
    - Notifies Office.
    """
    
    @staticmethod
    def toggle_open_status(user, establishment, is_open_now, ip=None):
        """
        Toggles the 'is_open_now' flag.
        """
        # 1. Permission Check
        if establishment.owner != user:
            return False, _("You do not have permission to modify this establishment.")

        old_status = establishment.is_open_now
        
        # No change check?
        if old_status == is_open_now:
            return True, _("Status is already set to this value.")

        # 2. Update
        establishment.is_open_now = is_open_now
        # updated_at/by handled by explicit set or auto_now if field configured? 
        # auto_now=True handles updated_at. I need to set updated_by manually.
        establishment.open_status_updated_by = user
        establishment.save(update_fields=['is_open_now', 'open_status_updated_at', 'open_status_updated_by'])
        
        # 3. Audit Log
        status_label_old = "Open" if old_status else "Closed"
        status_label_new = "Open" if is_open_now else "Closed"
        
        AuditLog.objects.create(
            user=user,
            action='UPDATE_OPEN_STATUS',
            table_name='places_establishment',
            record_id=establishment.id,
            diff={
                'is_open_now': {'old': status_label_old, 'new': status_label_new}
            },
            ip_address=ip
        )
        
        # 4. Notify Office
        NotificationService.emit_event(
            'OPEN_STATUS_CHANGED',
            {
                'place_name': establishment.name,
                'status': status_label_new,
                'user': user.username
            },
            {'role': 'staff'},
            priority='medium'
        )
        
        return True, _(f"Status updated to {status_label_new}.")
