from django.test import TestCase
from django.contrib.auth.models import Group
from users.models import User, Role, PartnerProfile
from management.models import Request
from ibb_guide.policies import UserPolicy, RequestPolicy

class AuthorizationTest(TestCase):
    def setUp(self):
        # Roles
        self.role_partner = Role.objects.create(name='partner')
        self.role_tourist = Role.objects.create(name='tourist')
        
        # User 1: Active Partner (with approved PartnerProfile)
        self.partner = User.objects.create_user(username='partner', password='p', role=self.role_partner)
        PartnerProfile.objects.create(user=self.partner, status='approved')
        
        # User 2: Tourist
        self.tourist = User.objects.create_user(username='tourist', password='p', role=self.role_tourist)
        
        # User 3: Suspended Partner
        self.suspended_partner = User.objects.create_user(username='suspended', password='p', role=self.role_partner, account_status='suspended')
        PartnerProfile.objects.create(user=self.suspended_partner, status='approved')
        
        # Admin
        self.admin = User.objects.create_superuser(username='admin', password='p')

    def test_signal_syncs_group(self):
        """Test that assigning a Role adds the user to the corresponding Group"""
        self.assertTrue(self.partner.groups.filter(name='partner').exists())
        self.assertTrue(self.tourist.groups.filter(name='tourist').exists())

    def test_user_policy_dashboard(self):
        """Test dashboard access policy"""
        # Active Partner -> True
        self.assertTrue(UserPolicy(self.partner).check('access_dashboard'))
        
        # Tourist -> False
        self.assertFalse(UserPolicy(self.tourist).check('access_dashboard'))
        
        # Suspended Partner -> False
        self.assertFalse(UserPolicy(self.suspended_partner).check('access_dashboard'))
        
        # Admin -> True
        self.assertTrue(UserPolicy(self.admin).check('access_dashboard'))

    def test_request_policy(self):
        """Test request viewing and approval policy"""
        req = Request.objects.create(user=self.partner, request_type='ADD_PLACE')
        
        # Partner can view own request
        self.assertTrue(RequestPolicy(self.partner).check('view_own_request', req))
        
        # Tourist cannot view partner's request
        self.assertFalse(RequestPolicy(self.tourist).check('view_own_request', req))
        
        # Admin can view any request
        self.assertTrue(RequestPolicy(self.admin).check('view_own_request', req))
        
        # Partner cannot approve request
        self.assertFalse(RequestPolicy(self.partner).check('approve_request', req))
        
        # Admin can approve request
        self.assertTrue(RequestPolicy(self.admin).check('approve_request', req))
