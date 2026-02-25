from django.utils import timezone
from management.models import EmergencyAlert
from interactions.notifications.notification_service import NotificationService
from django.db import transaction

class SafetyService:
    """
    Critical Service for Safety & SOS Operations.
    Handles high-priority distress signals.
    """

    @staticmethod
    @transaction.atomic
    def trigger_sos(user, lat, lon, alert_type, metadata=None):
        """
        Trigger an immediate SOS alert.
        """
        # 1. Create Record
        alert = EmergencyAlert.objects.create(
            user=user,
            latitude=lat,
            longitude=lon,
            alert_type=alert_type,
            metadata=metadata or {},
            status='ACTIVE'
        )

        # 2. Trigger Critical Notification (Broadcast to Admins/Security)
        # Using the new NotificationService Event System
        NotificationService.emit_event(
            event_name='SOS_ALERT',
            payload={
                'alert_id': alert.id,
                'user': user.username,
                'type': alert.get_alert_type_display(),
                'lat': float(lat),
                'lon': float(lon),
                'time': str(timezone.now())
            },
            audience_criteria={'role': 'staff'}, # In real app: + nearby partners/police
            priority='critical'
        )

        # 3. Notify Emergency Contacts (SMS/Alert)
        from management.models import EmergencyContact
        contacts = EmergencyContact.objects.filter(user=user, is_active=True)
        if contacts.exists():
            contact_msg = f"EMERGENCY: {user.username} sent SOS! Location: https://maps.google.com/?q={lat},{lon}"
            NotificationService._send_sms_notification(contacts, contact_msg) # Simulated

        return alert

    @staticmethod
    def responsive_action(alert_id, responder_user, action_note):
        """
        Mark alert as 'Responding'.
        """
        try:
            alert = EmergencyAlert.objects.get(pk=alert_id)
            alert.status = 'RESPONDING'
            alert.responded_by = responder_user
            alert.responded_at = timezone.now()
            alert.resolution_note = f"Action started: {action_note}"
            alert.save()
            return True
        except EmergencyAlert.DoesNotExist:
            return False

    @staticmethod
    def resolve_alert(alert_id, user, note):
        """
        Close the alert.
        """
        # Only admin or original user can close? Usually admin/responder for safety.
        try:
            alert = EmergencyAlert.objects.get(pk=alert_id)
            alert.status = 'RESOLVED'
            alert.resolution_note += f"\nClosed: {note}"
            alert.save()
            return True
        except EmergencyAlert.DoesNotExist:
            return False
