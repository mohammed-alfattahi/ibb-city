from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from places.models import Place, Establishment, Category
from interactions.models import Review, PlaceComment

User = get_user_model()

class ToggleVisibilityViewTest(TestCase):
    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username='owner', password='password')
        self.public_user = User.objects.create_user(username='public', password='password')
        self.other_owner = User.objects.create_user(username='other', password='password')

        # Establishment
        self.category = Category.objects.create(name="Test Cat")
        self.establishment = Establishment.objects.create(
            name="Test Est", 
            category=self.category,
            is_active=True,
            owner=self.owner,
            approval_status='approved'
        )
        self.place = self.establishment
        
        # Data
        self.review = Review.objects.create(
            user=self.public_user,
            place=self.place,
            rating=5,
            comment="Test Review",
            visibility_state='visible'
        )
        
        self.comment = PlaceComment.objects.create(
            user=self.owner,
            place=self.place,
            review=self.review,
            content="Test Reply",
            visibility_state='visible'
        )
        
        self.client = Client()

    def test_toggle_review_visibility_owner(self):
        """Owner can toggle review visibility."""
        self.client.force_login(self.owner)
        url = reverse('toggle_comment_visibility', kwargs={'pk': self.review.pk, 'model_type': 'review'})
        response = self.client.post(url, {'reason': 'Spam'})
        
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'partner_hidden')
        self.assertEqual(self.review.hidden_by, self.owner)
        
        # Toggle back
        response = self.client.post(url)
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'visible')

    def test_toggle_reply_visibility_owner(self):
        """Owner can toggle reply visibility."""
        self.client.force_login(self.owner)
        url = reverse('toggle_comment_visibility', kwargs={'pk': self.comment.pk, 'model_type': 'comment'})
        response = self.client.post(url, {'reason': 'Hide it'})
        
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.visibility_state, 'partner_hidden')
        
    def test_toggle_permission_denied(self):
        """Public user cannot toggle."""
        self.client.force_login(self.public_user)
        url = reverse('toggle_comment_visibility', kwargs={'pk': self.review.pk, 'model_type': 'review'})
        response = self.client.post(url)
        
        # Should redirect or error, but NOT change state
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'visible')
        
    def test_toggle_other_owner_denied(self):
        """Another partner cannot toggle my reviews."""
        self.client.force_login(self.other_owner)
        url = reverse('toggle_comment_visibility', kwargs={'pk': self.review.pk, 'model_type': 'review'})
        response = self.client.post(url)
        
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'visible')
