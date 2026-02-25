from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import PartnerProfile

User = get_user_model()

class ProfileUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('user_profile')

    def test_profile_update_persistence(self):
        """Test P1-17: Profile settings persistence."""
        data = {
            'username': 'updateduser', # Should be ignored/not updated
            'full_name': 'New Full Name',
            'email': 'updated@example.com',
            'phone_number': '123456789'
        }
        
        response = self.client.post(self.url, data, follow=True)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser') # Username should NOT change
        self.assertEqual(self.user.full_name, 'New Full Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.phone_number, '123456789')
        
        self.assertContains(response, "تم تحديث الملف الشخصي بنجاح")

    def test_htmx_update(self):
        """Test HTMX update response."""
        data = {
            'full_name': 'Htmx User',
            'email': 'htmx@example.com'
        }
        headers = {'HX-Request': 'true'}
        response = self.client.post(self.url, data, headers=headers)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Htmx User')
        
        # Should return OOB swaps
        self.assertIn('hx-swap-oob="outerHTML:#profile-sidebar"', response.content.decode('utf-8'))
