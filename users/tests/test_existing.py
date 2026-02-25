from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Role, PartnerProfile

User = get_user_model()


class UnifiedLoginTests(TestCase):
    """اختبارات نظام تسجيل الدخول الموحد"""
    
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.client = Client()
        self.login_url = reverse('login')
        
        # إنشاء مستخدم سائح
        self.tourist = User.objects.create_user(
            username='tourist_test',
            email='tourist@test.com',
            password='testpass123',
            account_status='active'
        )
        
        # إنشاء مستخدم شريك
        self.partner_user = User.objects.create_user(
            username='partner_test',
            email='partner@test.com',
            password='testpass123',
            account_status='active'
        )
        PartnerProfile.objects.create(
            user=self.partner_user,
            status='approved',
            is_approved=True
        )

    def test_login_page_loads(self):
        """اختبار تحميل صفحة تسجيل الدخول"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تسجيل الدخول')

    def test_login_with_username(self):
        """اختبار تسجيل الدخول باستخدام اسم المستخدم"""
        response = self.client.post(self.login_url, {
            'username': 'tourist_test',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_login_with_email(self):
        """اختبار تسجيل الدخول باستخدام البريد الإلكتروني"""
        response = self.client.post(self.login_url, {
            'username': 'tourist@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_partner_login_redirect(self):
        """اختبار توجيه الشريك إلى لوحة التحكم"""
        response = self.client.post(self.login_url, {
            'username': 'partner_test',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)


class AccountStatusModelTests(TestCase):
    """اختبارات نموذج حالة الحساب"""
    
    def test_user_account_status_default(self):
        """اختبار القيمة الافتراضية لحالة الحساب"""
        user = User.objects.create_user(
            username='test_user',
            password='testpass123'
        )
        self.assertEqual(user.account_status, 'active')
    
    def test_user_can_login_method(self):
        """اختبار دالة can_login"""
        active_user = User.objects.create_user(
            username='active_user',
            password='testpass123',
            account_status='active'
        )
        suspended_user = User.objects.create_user(
            username='suspended_user',
            password='testpass123',
            account_status='suspended'
        )
        
        self.assertTrue(active_user.can_login())
        self.assertFalse(suspended_user.can_login())
    
    def test_partner_profile_status_sync(self):
        """اختبار مزامنة حالة الشريك مع is_approved"""
        user = User.objects.create_user(
            username='partner_sync_test',
            password='testpass123'
        )
        
        # إنشاء ملف شريك مع حالة approved
        profile = PartnerProfile.objects.create(
            user=user,
            status='approved'
        )
        self.assertTrue(profile.is_approved)
        
        # تغيير الحالة لـ pending
        profile.status = 'pending'
        profile.save()
        self.assertFalse(profile.is_approved)
