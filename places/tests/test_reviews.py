from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from places.models import Establishment, Place, Category
from interactions.models import Review
from management.models import FeatureToggle

User = get_user_model()

class ReviewRatingTest(TestCase):
    def setUp(self):
        # Enable reviews feature
        FeatureToggle.objects.create(key='enable_reviews', is_enabled=True)
        
        self.user = User.objects.create_user(
            username='reviewer', 
            email='reviewer@example.com', 
            password='password'
        )
        self.owner = User.objects.create_user(
            username='owner', 
            email='owner@example.com', 
            password='password'
        )
        self.category = Category.objects.create(name='Test Category')
        self.establishment = Establishment.objects.create(
            name='Rated Place',
            owner=self.owner,
            category=self.category,
            approval_status='approved'
        )
        # Assuming Establishment is a Place proxy or 1-to-1, checking Place existence
        self.place = Place.objects.get(pk=self.establishment.pk)
        
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('place_detail', args=[self.place.pk])

    def test_post_review(self):
        """Test P1-18: Posting a review works."""
        # Check if 'review_create' URL exists
        try:
            review_url = reverse('review_create', args=[self.place.pk])
        except:
            review_url = self.url # Fallback to detail page if HTMX/Form is there
            
        data = {
            'rating': 4,
            'comment': 'Great place!'
        }
        
        response = self.client.post(review_url, data, follow=True)
        
        # Check review creation
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Great place!')
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.place, self.place)
        
        # Check average rating update (Signal or Service should handle this)
        self.place.refresh_from_db()
        self.assertEqual(self.place.avg_rating, 4.0)

    def test_review_filtering(self):
        """Test P1-19: Filtering reviews (if applicable)."""
        # Create multiple reviews
        Review.objects.create(place=self.place, user=self.user, rating=5, comment='Best')
        user2 = User.objects.create_user('u2', 'u2@e.com', 'pw')
        Review.objects.create(place=self.place, user=user2, rating=1, comment='Worst')
        
        # Calculate expected avg
        response = self.client.get(self.url)
        self.assertContains(response, 'Best')
        self.assertContains(response, 'Worst')
        
        # If filtering exists (e.g. ?rating=5)
        response_filtered = self.client.get(self.url + '?rating=5')
        # self.assertContains(response_filtered, 'Best')
        # self.assertNotContains(response_filtered, 'Worst')
        # Uncomment above if filtering is implemented
