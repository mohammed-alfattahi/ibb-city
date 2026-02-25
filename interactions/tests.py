"""
Tests for the interactions app.
Covers Reviews, Favorites, Notifications, and Reports.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock

from places.models import Place, Establishment, Category
from interactions.models import Review, Favorite, Notification, Report
from users.models import Role

User = get_user_model()


@patch('interactions.signals.NotificationService')
class ReviewModelTests(TestCase):
    """Test Review model functionality."""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.user = User.objects.create_user(username='reviewer', password='pass123')
        self.category = Category.objects.create(name='Restaurant')
        # Use Establishment which has owner field
        self.place = Establishment.objects.create(
            name='Test Establishment', 
            category=self.category,
            owner=self.owner
        )
    
    def test_create_review(self, mock_notify):
        """Test basic review creation."""
        review = Review.objects.create(
            user=self.user,
            place=self.place,
            rating=4,
            comment="Great place!"
        )
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.status, 'approved')
        self.assertFalse(review.is_edited)
    
    def test_unique_user_place_constraint(self, mock_notify):
        """User can only review a place once."""
        Review.objects.create(user=self.user, place=self.place, rating=5, comment="First")
        
        with self.assertRaises(Exception):
            Review.objects.create(user=self.user, place=self.place, rating=3, comment="Second")
    
    def test_edit_comment_saves_original(self, mock_notify):
        """Editing a comment should save the original."""
        review = Review.objects.create(
            user=self.user, place=self.place, rating=4, comment="Original comment"
        )
        review.edit_comment("Updated comment")
        
        self.assertTrue(review.is_edited)
        self.assertEqual(review.original_comment, "Original comment")
        self.assertEqual(review.comment, "Updated comment")
        self.assertIsNotNone(review.edited_at)
    
    def test_add_warning_hides_after_three(self, mock_notify):
        """Three warnings should hide the review."""
        review = Review.objects.create(
            user=self.user, place=self.place, rating=4, comment="Test"
        )
        
        review.add_warning("First warning")
        self.assertEqual(review.warning_count, 1)
        self.assertEqual(review.status, 'approved')
        
        review.add_warning("Second warning")
        self.assertEqual(review.warning_count, 2)
        
        review.add_warning("Third warning")
        self.assertEqual(review.warning_count, 3)
        self.assertEqual(review.status, 'hidden')


class FavoriteTests(TestCase):
    """Test Favorite functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='tourist', password='pass123')
        self.place = Place.objects.create(name='Favorite Place')
        self.client = Client()
    
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
        """Test notification creation."""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Test Notification',
            message='This is a test'
        )
        self.assertFalse(notif.is_read)
        self.assertIsNone(notif.read_at)
    
    def test_mark_as_read(self):
        """Test marking notification as read."""
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type='general',
            title='Test',
            message='Test'
        )
        notif.mark_as_read()
        
        self.assertTrue(notif.is_read)
        self.assertIsNotNone(notif.read_at)


class ReportTests(TestCase):
    """Test Report model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='admin')
        self.place = Place.objects.create(name='Reported Place')
    
    def test_create_report(self):
        """Test report creation."""
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
        self.assertEqual(report.priority, 'medium')
    
    def test_assign_and_resolve(self):
        """Test report assignment and resolution workflow."""
        from django.contrib.contenttypes.models import ContentType
        
        ct = ContentType.objects.get_for_model(Place)
        report = Report.objects.create(
            user=self.user,
            content_type=ct,
            object_id=self.place.pk,
            report_type='SPAM'
        )
        
        # Assign
        report.assign_to(self.admin)
        self.assertEqual(report.status, 'IN_PROGRESS')
        self.assertEqual(report.assigned_to, self.admin)
        
        # Resolve
        report.resolve('Fixed the issue')
        self.assertEqual(report.status, 'RESOLVED')
        self.assertIsNotNone(report.resolved_at)
