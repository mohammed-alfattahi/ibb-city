from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from places.models import Place, Establishment, Category
from interactions.models import Review, PlaceComment
from interactions.services.comment_service import CommentService

User = get_user_model()

class ReviewVisibilityTest(TestCase):
    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username='owner', password='password')
        self.user = User.objects.create_user(username='user', password='password')
        self.public_user = User.objects.create_user(username='public', password='password')
        self.admin = User.objects.create_superuser(username='admin', password='password', email='admin@test.com')

        # Establishment (Is a Place)
        self.category = Category.objects.create(name="Test Cat")
        self.establishment = Establishment.objects.create(
            name="Test Est", 
            category=self.category,
            is_active=True,
            owner=self.owner,
            license_number="123",
            approval_status='approved'
        )
        self.place = self.establishment
        
        # Review
        self.review = Review.objects.create(
            user=self.user,
            place=self.place,
            rating=5,
            comment="Great place!",
            visibility_state='visible'
        )

    def test_visibility_service_hide_by_owner(self):
        """Owner should be able to hide a review."""
        success, msg = CommentService.set_visibility(
            user=self.owner, 
            comment_id=self.review.id, 
            visibility='partner_hidden',
            model_class=Review
        )
        self.assertTrue(success)
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'partner_hidden')
        self.assertEqual(self.review.hidden_by, self.owner)

    def test_visibility_service_hide_by_public_fail(self):
        """Public user should NOT be able to hide a review."""
        success, msg = CommentService.set_visibility(
            user=self.public_user, 
            comment_id=self.review.id, 
            visibility='partner_hidden',
            model_class=Review
        )
        self.assertFalse(success)
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'visible')

    def test_visibility_service_admin_hidden_unhide_fail(self):
        """Owner cannot unhide Admin Hidden content."""
        self.review.visibility_state = 'admin_hidden'
        self.review.save()
        
        success, msg = CommentService.set_visibility(
            user=self.owner, 
            comment_id=self.review.id, 
            visibility='visible',
            model_class=Review
        )
        self.assertFalse(success)
        self.review.refresh_from_db()
        self.assertEqual(self.review.visibility_state, 'admin_hidden')

    def test_view_public_filtering(self):
        """Public view should NOT show hidden reviews."""
        self.review.visibility_state = 'partner_hidden'
        self.review.save()
        
        c = Client()
        # Anonymous
        response = c.get(f'/place/{self.place.id}/')
        # If redirect to login, force login as public
        c.force_login(self.public_user)
        response = c.get(f'/place/{self.place.id}/')
        
        self.assertEqual(response.status_code, 200)
        reviews = response.context['reviews']
        self.assertFalse(reviews.contains(self.review))

    def test_view_owner_visibility(self):
        """Owner SHOULD see hidden reviews."""
        self.review.visibility_state = 'partner_hidden'
        self.review.save()
        
        c = Client()
        c.force_login(self.owner)
        response = c.get(f'/place/{self.place.id}/')
        
        self.assertEqual(response.status_code, 200)
        reviews = response.context['reviews']
        self.assertTrue(reviews.contains(self.review))

    def test_reply_filtering(self):
        """Replies should be filtered too."""
        reply = PlaceComment.objects.create(
            user=self.owner, # Owner replies
            place=self.place,
            review=self.review,
            content="Thanks!",
            visibility_state='partner_hidden' # Hidden reply
        )
        
        c = Client()
        c.force_login(self.public_user)
        response = c.get(f'/place/{self.place.id}/')
        
        # Review is visible
        review_in_ctx = response.context['reviews'][0]
        # Check replies
        self.assertEqual(review_in_ctx.replies.count(), 0) # Should be 0 visible
