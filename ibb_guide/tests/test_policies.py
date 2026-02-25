"""
Tests for policy objects (authorization layer).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from users.models import Role
from ibb_guide.policies import UserPolicy, PlacePolicy, RequestPolicy
from places.models import Place, Establishment
from management.models import Request

User = get_user_model()


class UserPolicyTests(TestCase):
    """Test UserPolicy authorization rules."""
    
    def setUp(self):
        self.partner_role = Role.objects.create(name='partner')
        self.tourist_role = Role.objects.create(name='tourist')
        
        # Active partner
        self.partner = User.objects.create_user(
            username='partner', password='pass', 
            role=self.partner_role, account_status='active'
        )
        
        # Tourist
        self.tourist = User.objects.create_user(
            username='tourist', password='pass', 
            role=self.tourist_role
        )
        
        # Suspended partner
        self.suspended = User.objects.create_user(
            username='suspended', password='pass',
            role=self.partner_role, account_status='suspended'
        )
        
        # Admin
        self.admin = User.objects.create_superuser(
            username='admin', password='admin'
        )
    
    def test_partner_can_access_dashboard(self):
        """Active partners should access dashboard."""
        policy = UserPolicy(self.partner)
        self.assertTrue(policy.check('access_dashboard'))
    
    def test_tourist_cannot_access_dashboard(self):
        """Tourists should not access dashboard."""
        policy = UserPolicy(self.tourist)
        self.assertFalse(policy.check('access_dashboard'))
    
    def test_suspended_cannot_access_dashboard(self):
        """Suspended users should not access dashboard."""
        policy = UserPolicy(self.suspended)
        self.assertFalse(policy.check('access_dashboard'))
    
    def test_admin_can_access_dashboard(self):
        """Admins should always access dashboard."""
        policy = UserPolicy(self.admin)
        self.assertTrue(policy.check('access_dashboard'))
    
    def test_admin_can_manage_users(self):
        """Only admins can manage users."""
        self.assertTrue(UserPolicy(self.admin).check('manage_users'))
        self.assertFalse(UserPolicy(self.partner).check('manage_users'))
    
    def test_authorize_raises_permission_denied(self):
        """authorize() should raise PermissionDenied on failure."""
        policy = UserPolicy(self.tourist)
        with self.assertRaises(PermissionDenied):
            policy.authorize('access_dashboard')


class PlacePolicyTests(TestCase):
    """Test PlacePolicy authorization rules."""
    
    def setUp(self):
        from places.models import Category
        self.category = Category.objects.create(name='Hotels')
        self.partner_role = Role.objects.create(name='partner')
        
        self.owner = User.objects.create_user(
            username='owner', password='pass',
            role=self.partner_role, account_status='active'
        )
        self.other_partner = User.objects.create_user(
            username='other', password='pass',
            role=self.partner_role, account_status='active'
        )
        self.admin = User.objects.create_superuser(username='admin', password='admin')
        
        self.establishment = Establishment.objects.create(
            name='Test Place', owner=self.owner, category=self.category
        )
    
    def test_owner_can_edit_place(self):
        """Owners can edit their own places."""
        policy = PlacePolicy(self.owner)
        self.assertTrue(policy.check('edit_place', self.establishment))
    
    def test_non_owner_cannot_edit(self):
        """Non-owners cannot edit places."""
        policy = PlacePolicy(self.other_partner)
        self.assertFalse(policy.check('edit_place', self.establishment))
    
    def test_admin_can_edit_any_place(self):
        """Admins can edit any place."""
        policy = PlacePolicy(self.admin)
        self.assertTrue(policy.check('edit_place', self.establishment))
    
    def test_active_partner_can_create(self):
        """Active partners can create places."""
        policy = PlacePolicy(self.owner)
        self.assertTrue(policy.check('create_place'))


from unittest import skip

@skip("Pending migration for Request.assigned_to field")
class RequestPolicyTests(TestCase):
    """Test RequestPolicy authorization rules."""
    
    def setUp(self):
        self.partner_role = Role.objects.create(name='partner')
        
        self.partner = User.objects.create_user(
            username='partner', password='pass', role=self.partner_role
        )
        self.other_user = User.objects.create_user(
            username='other', password='pass', role=self.partner_role
        )
        self.admin = User.objects.create_superuser(username='admin', password='admin')
        
        self.request = Request.objects.create(
            user=self.partner,
            request_type='ADD_PLACE',
            status='PENDING'
        )
    
    def test_owner_can_view_own_request(self):
        """Users can view their own requests."""
        policy = RequestPolicy(self.partner)
        self.assertTrue(policy.check('view_own_request', self.request))
    
    def test_other_cannot_view_request(self):
        """Users cannot view others' requests."""
        policy = RequestPolicy(self.other_user)
        self.assertFalse(policy.check('view_own_request', self.request))
    
    def test_admin_can_view_any_request(self):
        """Admins can view any request."""
        policy = RequestPolicy(self.admin)
        self.assertTrue(policy.check('view_own_request', self.request))
    
    def test_admin_can_approve(self):
        """Admins can approve pending requests."""
        policy = RequestPolicy(self.admin)
        self.assertTrue(policy.check('approve_request', self.request))
    
    def test_partner_cannot_approve(self):
        """Partners cannot approve requests."""
        policy = RequestPolicy(self.partner)
        self.assertFalse(policy.check('approve_request', self.request))
    
    def test_cannot_approve_finalized_request(self):
        """Cannot approve already finalized requests."""
        self.request.status = 'APPROVED'
        self.request.save()
        
        policy = RequestPolicy(self.admin)
        self.assertFalse(policy.check('approve_request', self.request))
