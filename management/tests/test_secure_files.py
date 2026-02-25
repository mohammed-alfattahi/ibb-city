
from django.test import TestCase
from users.models import User, Role
from django.conf import settings
from django.urls import reverse
import os
import shutil

class SecureFileTest(TestCase):
    def setUp(self):
        # Users
        role_partner = Role.objects.create(name='partner')
        role_tourist = Role.objects.create(name='tourist')
        
        self.staff_user = User.objects.create_superuser(username='staff', password='p')
        self.tourist_user = User.objects.create_user(username='tourist', password='p', role=role_tourist)
        
        # Create a dummy file in MEDIA_ROOT
        self.test_filename = 'test_secure_doc.txt'
        self.test_path = os.path.join(settings.MEDIA_ROOT, self.test_filename)
        
        # Ensure directory exists (media root might not exist in test env)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        with open(self.test_path, 'w') as f:
            f.write("Secret Content")
            
    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
            
    def test_staff_can_access(self):
        self.client.force_login(self.staff_user)
        # Using the view name we defined 'secure_file' with parameter 'file_path'
        url = reverse('secure_file', kwargs={'file_path': self.test_filename})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check content is served - for FileResponse we can check streaming_content if needed, or just status
        # FileResponse serves file object.
        self.assertEqual(b''.join(response.streaming_content), b"Secret Content")

    def test_tourist_cannot_access(self):
        self.client.force_login(self.tourist_user)
        url = reverse('secure_file', kwargs={'file_path': self.test_filename})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
