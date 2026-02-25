from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from places.models import Establishment, Category
from places.models.contacts import EstablishmentContact

User = get_user_model()

class ContactDisplayTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name="Test Cat")
        self.establishment = Establishment.objects.create(
            name="Test Est", 
            category=self.category,
            is_active=True,
            approval_status='approved',
            owner=self.user
        )
        self.place = self.establishment # Treat as place

        # Create Contacts
        self.phone = EstablishmentContact.objects.create(
            establishment=self.establishment,
            type='phone',
            value='777777777',
            carrier='yemen_mobile',
            is_visible=True
        )
        self.whatsapp = EstablishmentContact.objects.create(
            establishment=self.establishment,
            type='whatsapp',
            value='777777777',
            is_visible=True
        )
        self.hidden_contact = EstablishmentContact.objects.create(
            establishment=self.establishment,
            type='email',
            value='hidden@test.com',
            is_visible=False
        )
        self.website = EstablishmentContact.objects.create(
            establishment=self.establishment,
            type='website',
            value='https://test.com',
            is_visible=True
        )

    def test_context_data(self):
        c = Client()
        c.force_login(self.user)
        response = c.get(f'/place/{self.place.id}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('grouped_contacts', response.context)
        
        grouped = response.context['grouped_contacts']
        
        # Check categorization
        self.assertEqual(len(grouped['phones']), 1)
        self.assertEqual(grouped['phones'][0].value, '777777777')
        
        self.assertEqual(len(grouped['messaging']), 1)
        self.assertEqual(grouped['messaging'][0].type, 'whatsapp')
        
        self.assertEqual(len(grouped['links']), 1)
        self.assertEqual(grouped['links'][0].type, 'website')
        
        # Ensure hidden is NOT present
        self.assertFalse(any(c.value == 'hidden@test.com' for c in grouped['links']))
