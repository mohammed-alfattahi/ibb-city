from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from places.models import Establishment, Place, Category
from interactions.models import PlaceComment
from management.models import FeatureToggle

User = get_user_model()

class CommentTest(TestCase):
    def setUp(self):
        # Enable comments if toggled (using enable_reviews as per template)
        FeatureToggle.objects.create(key='enable_reviews', is_enabled=True)

        self.user = User.objects.create_user(username='commenter', email='c@e.com', password='password')
        self.owner = User.objects.create_user(username='owner', email='o@e.com', password='password')
        self.category = Category.objects.create(name='Test Category')
        self.establishment = Establishment.objects.create(
            name='Discussed Place',
            owner=self.owner,
            category=self.category,
            approval_status='approved'
        )
        self.place = Place.objects.get(pk=self.establishment.pk)
        
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('place_detail', args=[self.place.pk])

    def test_add_comment(self):
        """Test P1-20: Adding a comment works."""
        # Check URL for adding comment
        try:
            url = reverse('add_place_comment', args=[self.place.pk])
        except:
            # Fallback based on urls.py reading: path('place/<int:place_pk>/comment/', add_place_comment...)
            url = f'/place/{self.place.pk}/comment/'
            
        data = {'content': 'Nice place info!'}
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(PlaceComment.objects.count(), 1)
        comment = PlaceComment.objects.first()
        self.assertEqual(comment.content, 'Nice place info!')
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.place, self.place)

    def test_reply_comment(self):
        """Test replying to a comment."""
        parent = PlaceComment.objects.create(place=self.place, user=self.owner, content='Original')
        
        try:
            url = reverse('reply_to_comment', args=[parent.pk])
        except:
             url = f'/comment/{parent.pk}/reply/'
             
        data = {'content': 'Reply'}
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(PlaceComment.objects.count(), 2)
        reply = PlaceComment.objects.last()
        self.assertEqual(reply.content, 'Reply')
        self.assertEqual(reply.parent, parent)
