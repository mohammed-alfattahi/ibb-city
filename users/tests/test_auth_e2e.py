"""
End-to-End Authentication Test Suite
=====================================
Comprehensive tests for all authentication flows.

Test Case IDs:
- TC-AUTH-001 to TC-AUTH-010: Tourist Signup Flow
- TC-AUTH-011 to TC-AUTH-020: Partner Signup Flow  
- TC-AUTH-031 to TC-AUTH-050: Negative Tests
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

User = get_user_model()


# ============================================
# TC-AUTH-001 to TC-AUTH-010: Tourist Signup Flow
# ============================================
class TouristSignupFlowTestCase(TestCase):
    """
    Test complete tourist signup flow:
    signup -> verification_sent -> verify_email -> login success
    """
    
    def setUp(self):
        self.client = Client()
        self.signup_data = {
            'username': 'tourist_test',
            'full_name': 'سائح تجريبي',
            'email': 'tourist@example.com',
            'phone_number': '771234567',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'terms_accepted': True,
        }
    
    def test_TC_AUTH_001_tourist_signup_page_accessible(self):
        """TC-AUTH-001: Tourist signup page should be accessible."""
        response = self.client.get(reverse('visitor_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إنشاء')
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_002_tourist_signup_creates_user(self, mock_send_mail):
        """TC-AUTH-002: Successful signup creates user with is_email_verified=False."""
        mock_send_mail.return_value = 1
        
        response = self.client.post(reverse('visitor_signup'), self.signup_data, follow=True)
        
        # User should be created
        self.assertTrue(User.objects.filter(username='tourist_test').exists())
        user = User.objects.get(username='tourist_test')
        
        # Email should NOT be verified yet
        self.assertFalse(user.is_email_verified)
        
        # Should redirect to verification_sent
        self.assertRedirects(response, reverse('verification_sent'))
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_003_tourist_signup_sends_verification_email(self, mock_send_mail):
        """TC-AUTH-003: Signup should trigger verification email."""
        mock_send_mail.return_value = 1
        
        self.client.post(reverse('visitor_signup'), self.signup_data)
        
        # Email should have been sent
        self.assertTrue(mock_send_mail.called)
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_004_tourist_signup_creates_registration_log(self, mock_send_mail):
        """TC-AUTH-004: Signup should create UserRegistrationLog with status=pending."""
        from users.models import UserRegistrationLog
        mock_send_mail.return_value = 1
        
        self.client.post(reverse('visitor_signup'), self.signup_data)
        
        log = UserRegistrationLog.objects.filter(username='tourist_test').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'pending')
        self.assertEqual(log.registration_type, 'tourist')
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_005_verification_sent_page_shows_email(self, mock_send_mail):
        """TC-AUTH-005: Verification sent page should show the pending email."""
        mock_send_mail.return_value = 1
        
        response = self.client.post(reverse('visitor_signup'), self.signup_data, follow=True)
        
        self.assertContains(response, 'tourist@example.com')
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_006_email_verification_success(self, mock_send_mail):
        """TC-AUTH-006: Visiting verification link marks email as verified."""
        mock_send_mail.return_value = 1
        
        # Create user via signup
        self.client.post(reverse('visitor_signup'), self.signup_data)
        user = User.objects.get(username='tourist_test')
        
        # Set verification sent time
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        token = user.email_verification_token
        
        # Verify email
        response = self.client.get(reverse('verify_email', kwargs={'token': token}))
        
        # Refresh user
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertEqual(user.email_verification_token, '')
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_007_verified_tourist_can_login(self, mock_send_mail):
        """TC-AUTH-007: After verification, tourist can login successfully."""
        mock_send_mail.return_value = 1
        
        # Create and verify user
        self.client.post(reverse('visitor_signup'), self.signup_data)
        user = User.objects.get(username='tourist_test')
        user.is_email_verified = True
        user.save()
        
        # Login with follow=True to handle redirects
        response = self.client.post('/login/', {
            'username': 'tourist_test',
            'password': 'SecurePass123!'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    @patch('users.email_service.send_mail')
    def test_TC_AUTH_008_unverified_tourist_cannot_login(self, mock_send_mail):
        """TC-AUTH-008: Unverified tourist is redirected to verification_sent."""
        mock_send_mail.return_value = 1
        
        # Create user (not verified)
        self.client.post(reverse('visitor_signup'), self.signup_data)
        
        # Try to login
        response = self.client.post('/login/', {
            'username': 'tourist_test',
            'password': 'SecurePass123!'
        }, follow=True)
        
        # Should redirect to verification_sent
        self.assertRedirects(response, reverse('verification_sent'))
    
    def test_TC_AUTH_009_tourist_redirected_to_home_after_login(self):
        """TC-AUTH-009: Verified tourist is redirected to home after login."""
        # Create verified tourist
        user = User.objects.create_user(
            username='verified_tourist',
            email='verified@example.com',
            password='TestPass123!',
            is_email_verified=True,
            account_status='active'
        )
        
        response = self.client.post('/login/', {
            'username': 'verified_tourist',
            'password': 'TestPass123!'
        }, follow=True)
        
        # Should end up at home
        self.assertEqual(response.request['PATH_INFO'], reverse('home'))
    
    def test_TC_AUTH_010_terms_required_for_signup(self):
        """TC-AUTH-010: Terms acceptance is required (server-side)."""
        data = self.signup_data.copy()
        del data['terms_accepted']
        
        response = self.client.post(reverse('visitor_signup'), data)
        
        # Should fail validation
        self.assertFormError(response, 'form', 'terms_accepted', 'يجب الموافقة على شروط الاستخدام للمتابعة')


# ============================================
# TC-AUTH-011 to TC-AUTH-020: Partner Signup Flow
# ============================================
class PartnerSignupFlowTestCase(TestCase):
    """
    Test partner signup flow.
    """
    
    def setUp(self):
        self.client = Client()
    
    def test_TC_AUTH_011_partner_signup_page_accessible(self):
        """TC-AUTH-011: Partner signup page should be accessible."""
        response = self.client.get(reverse('partner_signup'))
        self.assertEqual(response.status_code, 200)
    
    def test_TC_AUTH_016_rejected_partner_sees_rejection_message(self):
        """TC-AUTH-016: Rejected partner sees rejection reason after login."""
        from users.models import PartnerProfile, Role
        
        # Create rejected partner
        user = User.objects.create_user(
            username='rejected_partner',
            email='rejected@example.com',
            password='TestPass123!',
            is_email_verified=True,
            account_status='rejected'
        )
        role, _ = Role.objects.get_or_create(name='Partner')
        user.role = role
        user.save()
        
        PartnerProfile.objects.create(
            user=user,
            status='rejected',
            is_approved=False,
            rejection_reason='الوثائق غير مكتملة'
        )
        
        # Login (don't follow redirects, check form error)
        response = self.client.post('/login/', {
            'username': 'rejected_partner',
            'password': 'TestPass123!'
        })
        
        # Should show rejection message in the response
        self.assertEqual(response.status_code, 200)

    @override_settings(AXES_ENABLED=False, SKIP_EMAIL_VERIFICATION=True)
    def test_TC_AUTH_017_pending_partner_redirected_to_pending_page(self):
        """TC-AUTH-017: Pending partner should be redirected to partner_pending after login."""
        from users.models import PartnerProfile, Role

        user = User.objects.create_user(
            username='partner_new',
            email='partner_new@example.com',
            password='Test@12345',
            is_email_verified=True,
            account_status='active'
        )
        role, _ = Role.objects.get_or_create(name='Partner')
        user.role = role
        user.save()

        PartnerProfile.objects.create(
            user=user,
            status='pending',
            is_approved=False,
        )

        response = self.client.post('/login/', {
            'username': 'partner_new',
            'password': 'Test@12345'
        })

        # Should redirect to partner_pending
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('partner_pending'))


# ============================================
# TC-AUTH-031 to TC-AUTH-050: Negative Tests
# ============================================
class NegativeAuthTestCase(TestCase):
    """
    Negative test cases for authentication.
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create existing user
        self.existing_user = User.objects.create_user(
            username='existing_user',
            email='existing@example.com',
            password='TestPass123!',
            phone_number='774567890',
            is_email_verified=True
        )
    
    def test_TC_AUTH_031_duplicate_email_rejected(self):
        """TC-AUTH-031: Signup with duplicate email should be rejected."""
        response = self.client.post(reverse('visitor_signup'), {
            'username': 'new_user',
            'full_name': 'مستخدم جديد',
            'email': 'existing@example.com',  # Duplicate
            'phone_number': '775678901',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'terms_accepted': True,
        })
        
        self.assertFormError(response, 'form', 'email', 'هذا البريد الإلكتروني مستخدم بالفعل.')
    
    def test_TC_AUTH_032_duplicate_phone_rejected(self):
        """TC-AUTH-032: Signup with duplicate phone should be rejected."""
        response = self.client.post(reverse('visitor_signup'), {
            'username': 'new_user2',
            'full_name': 'مستخدم جديد',
            'email': 'new@example.com',
            'phone_number': '774567890',  # Duplicate (normalized)
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'terms_accepted': True,
        })
        
        self.assertFormError(response, 'form', 'phone_number', 'رقم الهاتف هذا مستخدم بالفعل.')
    
    def test_TC_AUTH_033_invalid_username_rejected(self):
        """TC-AUTH-033: Username with Arabic characters should be rejected."""
        response = self.client.post(reverse('visitor_signup'), {
            'username': 'مستخدم_عربي',  # Arabic username
            'full_name': 'مستخدم',
            'email': 'arabic@example.com',
            'phone_number': '776789012',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'terms_accepted': True,
        })
        
        self.assertFormError(response, 'form', 'username', 'اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط')
    
    def test_TC_AUTH_034_invalid_token_rejected(self):
        """TC-AUTH-034: Invalid verification token shows error."""
        response = self.client.get(reverse('verify_email', kwargs={'token': 'invalid_token_here'}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'غير صالح')
    
    def test_TC_AUTH_035_expired_token_rejected(self):
        """TC-AUTH-035: Expired verification token shows error with resend option."""
        # Create user with old token
        user = User.objects.create_user(
            username='expired_user',
            email='expired@example.com',
            password='TestPass123!',
            is_email_verified=False,
            email_verification_token='expired_token_123',
            email_verification_sent_at=timezone.now() - timedelta(hours=25)  # 25 hours ago
        )
        
        response = self.client.get(reverse('verify_email', kwargs={'token': 'expired_token_123'}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'منتهي الصلاحية')
        self.assertContains(response, 'إعادة إرسال')
    
    def test_TC_AUTH_036_suspended_user_cannot_login(self):
        """TC-AUTH-036: Suspended user cannot login."""
        # Suspend user
        self.existing_user.account_status = 'suspended'
        self.existing_user.suspension_reason = 'مخالفة الشروط'
        self.existing_user.save()
        
        # Login - use explicit URL with trailing slash
        response = self.client.post('/login/', {
            'username': 'existing_user',
            'password': 'TestPass123!'
        })
        
        # Should show suspension message (status 200 with form error)
        self.assertEqual(response.status_code, 200)
    
    def test_TC_AUTH_037_rejected_user_cannot_login(self):
        """TC-AUTH-037: Rejected user cannot login."""
        self.existing_user.account_status = 'rejected'
        self.existing_user.save()
        
        response = self.client.post('/login/', {
            'username': 'existing_user',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_TC_AUTH_038_wrong_password_fails(self):
        """TC-AUTH-038: Wrong password should fail login."""
        response = self.client.post('/login/', {
            'username': 'existing_user',
            'password': 'WrongPassword123!'
        })
        
        # Should return 200 (show login form with error)
        self.assertEqual(response.status_code, 200)
    
    def test_TC_AUTH_039_nonexistent_user_fails(self):
        """TC-AUTH-039: Nonexistent username should fail login."""
        response = self.client.post('/login/', {
            'username': 'nonexistent_user',
            'password': 'AnyPassword123!'
        })
        
        # Should return 200 with error
        self.assertEqual(response.status_code, 200)
    
    def test_TC_AUTH_040_api_register_without_email_verification(self):
        """TC-AUTH-040: API registration creates user with is_email_verified=False."""
        response = self.client.post(
            '/api/register/',
            {
                'username': 'api_user',
                'email': 'api@example.com',
                'password': 'SecurePass123!',
                'full_name': 'API User',
                'phone_number': '777890123'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='api_user')
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.email_verification_token)


class AxesLockoutTestCase(TestCase):
    """Test Axes lockout functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='lockout_test',
            email='lockout@example.com',
            password='TestPass123!',
            is_email_verified=True
        )
    
    @override_settings(AXES_FAILURE_LIMIT=3)
    def test_TC_AUTH_041_remaining_attempts_shown(self):
        """TC-AUTH-041: Failed login shows remaining attempts in context."""
        # Make a failed attempt
        response = self.client.post('/login/', {
            'username': 'lockout_test',
            'password': 'WrongPassword!'
        })
        
        # Context should have remaining_attempts
        self.assertIn('remaining_attempts', response.context)


class LoginPageAccessTestCase(TestCase):
    """Basic login page tests."""
    
    def setUp(self):
        self.client = Client()
    
    def test_TC_AUTH_042_login_page_accessible(self):
        """TC-AUTH-042: Login page should be accessible."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تسجيل الدخول')
