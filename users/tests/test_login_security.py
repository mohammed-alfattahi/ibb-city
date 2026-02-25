"""
Tests for Authentication Security Features
Phase 4: Remember Me and Session Expiry
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class RememberMeTestCase(TestCase):
    """Test Remember Me functionality affects session expiry."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
    
    def test_remember_me_checked_extends_session(self):
        """When Remember Me is checked, session should last 30 days."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
            'remember_me': 'on'
        }, follow=True)
        
        # Check session expiry is set (not 0 = browser close)
        session_expiry = self.client.session.get_expiry_age()
        
        # Should be approximately 30 days (2592000 seconds)
        self.assertGreater(session_expiry, 0, "Session should not expire on browser close")
        self.assertEqual(session_expiry, 60 * 60 * 24 * 30, "Session should last 30 days")
    
    def test_remember_me_unchecked_expires_on_browser_close(self):
        """When Remember Me is not checked, session should expire on browser close."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
            # remember_me NOT checked
        }, follow=True)
        
        # Check session expiry is 0 (browser close)
        session_expiry = self.client.session.get_expiry_age()
        
        # Session should expire when browser closes (expiry_age returns SESSION_COOKIE_AGE when set to 0)
        # We check by verifying get_expire_at_browser_close() returns True
        self.assertTrue(
            self.client.session.get_expire_at_browser_close(),
            "Session should expire when browser closes"
        )


class LoginSecurityTestCase(TestCase):
    """Test login security features."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='securityuser',
            email='security@example.com',
            password='securepass123',
            is_email_verified=True
        )
    
    def test_remaining_attempts_shown_in_context(self):
        """Remaining attempts should be passed to template context."""
        # First, make a failed attempt
        response = self.client.post(reverse('login'), {
            'username': 'securityuser',
            'password': 'wrongpassword'
        })
        
        # Check context has remaining_attempts
        self.assertIn('remaining_attempts', response.context)
    
    def test_login_page_accessible(self):
        """Login page should be accessible."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تسجيل الدخول')
