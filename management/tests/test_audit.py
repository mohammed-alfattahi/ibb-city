"""
Tests for Audit Logging System
Uses existing AuditLog model and AuditService.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from management.models import AuditLog
from management.services.audit_service import AuditService

User = get_user_model()


class AuditLogModelTest(TestCase):
    """Test AuditLog model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            table_name='Establishment',
            record_id='123',
            old_values=None,
            new_values={'name': 'Test Place', 'status': 'approved'}
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'CREATE')
        self.assertIsNone(log.old_values)
        self.assertEqual(log.new_values['name'], 'Test Place')
    
    def test_audit_log_with_ip(self):
        """Test audit log with IP address."""
        log = AuditLog.objects.create(
            user=self.user,
            action='UPDATE',
            table_name='Establishment',
            record_id='456',
            ip_address='192.168.1.1'
        )
        
        self.assertEqual(log.ip_address, '192.168.1.1')


class AuditServiceTest(TestCase):
    """Test AuditService functions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner',
            email='partner@example.com',
            password='testpass'
        )
        self.factory = RequestFactory()
    
    def test_audit_service_log(self):
        """Test AuditService.log function."""
        initial_count = AuditLog.objects.count()
        
        AuditService.log(
            actor=self.user,
            action='UPDATE',
            target_model='Establishment',
            target_id='789',
            old_data={'name': 'Old Name'},
            new_data={'name': 'New Name'},
            reason='Testing'
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'UPDATE')
        self.assertEqual(log.old_values['name'], 'Old Name')
        self.assertEqual(log.new_values['name'], 'New Name')
    
    def test_audit_service_with_request(self):
        """Test AuditService extracts IP from request."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestBrowser/1.0'
        
        AuditService.log(
            actor=self.user,
            action='CREATE',
            target_model='Test',
            target_id='1',
            request=request
        )
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.ip_address, '10.0.0.1')
        self.assertIn('TestBrowser', log.user_agent)
    
    def test_diff_computation(self):
        """Test that diff is computed correctly."""
        old = {'name': 'Old', 'status': 'pending'}
        new = {'name': 'New', 'status': 'pending'}
        
        diff = AuditService._compute_diff(old, new)
        
        self.assertIn('name', diff)
        self.assertEqual(diff['name']['old'], 'Old')
        self.assertEqual(diff['name']['new'], 'New')
        self.assertNotIn('status', diff)  # Unchanged
    
    def test_get_client_ip_forwarded(self):
        """Test IP extraction with X-Forwarded-For header."""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 10.0.0.1'
        
        ip = AuditService._get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')


class AuditIntegrationTest(TestCase):
    """Integration tests for audit logging."""
    
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            is_staff=True
        )
    
    def test_sensitive_action_creates_log(self):
        """Test that sensitive actions create exactly one audit log."""
        initial_count = AuditLog.objects.count()
        
        AuditService.log(
            actor=self.staff,
            action='APPROVE',
            target_model='PartnerProfile',
            target_id='1',
            old_data={'status': 'pending'},
            new_data={'status': 'approved'},
            reason='Approved by admin'
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
    
    def test_audit_log_queryable(self):
        """Test audit logs are queryable by various fields."""
        # Create multiple logs
        for i in range(5):
            AuditService.log(
                actor=self.staff,
                action='UPDATE',
                target_model='TestEntity',
                target_id=str(i)
            )
        
        # Query by action
        logs = AuditLog.objects.filter(action='UPDATE')
        self.assertGreaterEqual(logs.count(), 5)
        
        # Query by user
        logs = AuditLog.objects.filter(user=self.staff)
        self.assertGreaterEqual(logs.count(), 5)
