from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from places.models import Place, Establishment, Category
from interactions.models import Review, Favorite, Notification, Report
from interactions.services.review_service import ReviewService

User = get_user_model()

@patch('interactions.services.review_service.ReviewService._notify_establishment_owner')
class ReviewServiceTests(TestCase):
    """Test ReviewService functionality."""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.user = User.objects.create_user(username='reviewer', password='pass123')
        # Ensure Category has all required fields? Name is usually enough.
        self.category = Category.objects.create(name='Restaurant') 
        self.place = Establishment.objects.create(
            name='Test Establishment', 
            category=self.category,
            owner=self.owner,
            description='Test desc'
        )
    
    def test_create_review_success(self, mock_notify):
        """Test basic review creation via service."""
        success, result = ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=4,
            comment="Great place!"
        )
        self.assertTrue(success)
        self.assertIsInstance(result, Review)
        self.assertEqual(result.rating, 4)
        self.assertEqual(result.comment, "Great place!")
    
    def test_duplicate_review_prevention(self, mock_notify):
        """Service should prevent duplicate reviews."""
        ReviewService.create_review(self.user, self.place, 5, "First")
        
        success, message = ReviewService.create_review(self.user, self.place, 3, "Second")
        self.assertFalse(success)
        self.assertIn("لديك تقييم سابق", message)
    
    @patch('management.services.moderation_service.analyze_text')
    def test_moderation_block(self, mock_analyze, mock_notify):
        """Service should block bad content."""
        # Mock moderation result
        mock_result = MagicMock()
        mock_result.action = 'block'
        mock_result.message = 'Blocked content'
        mock_result.matched = ['bad'] # Actual list, not a Mock
        mock_result.severity = 'high'
        mock_analyze.return_value = mock_result
        
        success, result = ReviewService.create_review(
            self.user, 
            self.place, 
            1, 
            "Bad words"
        )
        self.assertFalse(success)
        self.assertEqual(result, mock_result)
        self.assertEqual(Review.objects.count(), 0)

    def test_update_review(self, mock_notify):
        """Test updating a review."""
        # First creation
        success, review = ReviewService.create_review(self.user, self.place, 4, "Old logic")
        self.assertTrue(success)
        
        # Update
        success, updated = ReviewService.update_review(
            self.user, 
            review.pk, 
            rating=5, 
            comment="Updated logic"
        )
        self.assertTrue(success)
        self.assertEqual(updated.rating, 5)
        self.assertEqual(updated.comment, "Updated logic")
        
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)


class FavoriteTests(TestCase):
    """Test Favorite functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='tourist', password='pass123')
        self.owner = User.objects.create_user(username='fav_owner', password='pass')
        self.category = Category.objects.create(name='Cat')
        self.place = Establishment.objects.create(name='Favorite Place', category=self.category, owner=self.owner)
    
    def test_create_favorite(self):
        """Test adding a favorite."""
        fav = Favorite.objects.create(user=self.user, place=self.place)
        self.assertEqual(fav.user, self.user)
        self.assertEqual(fav.place, self.place)
    
    def test_unique_favorite_constraint(self):
        """User can't favorite same place twice."""
        Favorite.objects.create(user=self.user, place=self.place)
        with self.assertRaises(Exception):
            Favorite.objects.create(user=self.user, place=self.place)


class NotificationTests(TestCase):
    """Test Notification model."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='notify_user', password='pass')
    
    def test_create_notification(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Test Notification',
            message='This is a test'
        )
        self.assertFalse(notif.is_read)
    
    def test_mark_as_read(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Test',
            message='Test'
        )
        notif.mark_as_read()
        self.assertTrue(notif.is_read)


class ReportTests(TestCase):
    """Test Report model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='admin')
        self.owner = User.objects.create_user(username='rep_owner', password='pass')
        self.category = Category.objects.create(name='Cat')
        self.place = Establishment.objects.create(name='Reported Place', category=self.category, owner=self.owner)
    
    def test_create_report(self):
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Place)
        report = Report.objects.create(
            user=self.user,
            content_type=ct,
            object_id=self.place.pk,
            report_type='INACCURATE',
            description='Wrong address'
        )
        self.assertEqual(report.status, 'NEW')
