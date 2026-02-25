from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from places.models import Establishment, EstablishmentDraft
from places.services.draft_service import DraftService
from places.models.base import Category
from management.models import PendingChange

User = get_user_model()

@override_settings(LANGUAGE_CODE='en-us')
class DraftSystemTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='partner', password='password')
        self.category = Category.objects.create(name='Hotel')

    def test_create_new_draft(self):
        """Test creating a draft for a new establishment."""
        draft = DraftService.create_new_draft(self.user)
        self.assertTrue(draft.is_create_mode)
        self.assertEqual(draft.establishment.approval_status, 'draft')
        self.assertEqual(draft.establishment.owner, self.user)
        self.assertEqual(draft.current_step, 1)

    def test_save_step_json_and_sync(self):
        """Test that validation save updates JSON and syncs to Establishment (create mode)."""
        draft = DraftService.create_new_draft(self.user)
        data = {'name': 'Test Place', 'description': 'Detailed Desc'}
        
        # Simulate Save Step
        DraftService.save_step(draft, 1, data)
        
        draft.refresh_from_db()
        
        # JSON Updated
        self.assertEqual(draft.data['name'], 'Test Place')
        
        # Establishment Updated (Create Mode Sync)
        self.assertEqual(draft.establishment.name, 'Test Place')
        self.assertEqual(draft.establishment.description, 'Detailed Desc')

    def test_submit_new_draft(self):
        """Test submitting a new draft moves it to pending status."""
        draft = DraftService.create_new_draft(self.user)
        data = {'name': 'Final Name', 'category': self.category.id}
        DraftService.save_step(draft, 1, data)
        
        success, msg = DraftService.submit_draft(draft)
        self.assertTrue(success)
        self.assertEqual(draft.status, 'submitted')
        
        draft.establishment.refresh_from_db()
        self.assertEqual(draft.establishment.approval_status, 'pending')

    def test_edit_draft_sensitive_change(self):
        """Test editing an existing approved establishment creates PendingChanges."""
        # Create approved establishment
        est = Establishment.objects.create(
            owner=self.user, 
            name="Old Name", 
            description="Old Desc",
            approval_status='approved', 
            category=self.category
        )
        
        # Create Draft
        draft = DraftService.create_edit_draft(self.user, est)
        self.assertFalse(draft.is_create_mode)
        
        # Change Sensitive (name) and Non-Sensitive (working_hours - assuming non-sensitive logic implemented in service?)
        # DraftService logic: "Update non-sensitive fields immediately? ... Prompt: update non-sensitive now."
        # Service Implementation says: "Update non-sensitive fields immediately" but restricted 'name' and 'description'
        
        changes = {'name': 'New Name', 'description': 'New Desc'} # Both sensitive
        DraftService.save_step(draft, 1, changes)
        
        # Submit
        success, msg = DraftService.submit_draft(draft)
        self.assertTrue(success)
        
        # Est name should NOT change immediately
        est.refresh_from_db()
        self.assertEqual(est.name, "Old Name")
        
        # PendingChange should exist
        pc_name = PendingChange.objects.filter(establishment=est, field_name='name').first()
        self.assertIsNotNone(pc_name)
        self.assertEqual(pc_name.new_value, 'New Name')
