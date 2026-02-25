from django.test import TestCase
from unittest.mock import patch, MagicMock
from management.tests.base import BaseTestCase
from management.models import Request, RequestStatusLog, ApprovalDecision, GeoZone
from management.services.approval_service import ApprovalService
from management.services.safety_service import SafetyService

class ServiceTests(BaseTestCase):
    
    @patch('interactions.notifications.notification_service.NotificationService.emit_event')
    def test_approval_workflow_add_place(self, mock_notify):
        """
        Test typical Approval Flow:
        User requests ADD_PLACE -> Admin checks -> Approves -> Request Status Updated + Notification
        """
        # 1. Given: A pending request
        request = self.create_request(self.partner, 'ADD_PLACE')
        
        # 2. When: Admin assumes and approves
        ApprovalService.assign_request(request, self.admin)
        ApprovalService.process_decision(
            request_obj=request,
            admin_user=self.admin,
            decision='APPROVE',
            reason="Valid Place"
        )
        
        # 3. Then: Status is APPROVED
        request.refresh_from_db()
        self.assertEqual(request.status, 'APPROVED')
        
        # 4. Then: Decision is logged
        decision = ApprovalDecision.objects.filter(request=request).first()
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, 'APPROVE')
        
        # 5. Then: Notification executed
        self.assertTrue(mock_notify.called)

    @patch('interactions.notifications.notification_service.NotificationService.emit_event')
    @patch('management.services.safety_service.NotificationService._send_sms_notification') # Patch SMS simulation
    def test_safety_sos_trigger(self, mock_sms, mock_notify):
        """
        Test Critical SOS Flow:
        User triggers SOS -> Alert Created -> Staff Notified -> Contacts Notified
        """
        # 1. Given: User with emergency contact
        from management.models import EmergencyContact
        EmergencyContact.objects.create(user=self.tourist, name="Mom", phone_number="123", relation="Mother")
        
        # 2. When: SOS triggered
        alert = SafetyService.trigger_sos(self.tourist, 15.123, 44.123, 'SECURITY')
        
        # 3. Then: Alert matches
        self.assertEqual(alert.alert_type, 'SECURITY')
        self.assertEqual(alert.status, 'ACTIVE')
        
        # 4. Then: Notification Broadcast to Staff (Critical)
        mock_notify.assert_called_with(
            event_name='SOS_ALERT',
            payload=MagicMock(), # We don't check exact payload structure strict here
            audience_criteria={'role': 'staff'},
            priority='critical'
        )
        
        # 5. Then: SMS sent to contacts
        self.assertTrue(mock_sms.called)
