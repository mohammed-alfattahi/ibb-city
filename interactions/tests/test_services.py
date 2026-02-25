"""
Tests for ReviewService and ReportService
اختبارات خدمة التقييمات والبلاغات
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from interactions.models import Review, PlaceComment, Report
from interactions.services.review_service import ReviewService
from interactions.services.report_service import ReportService
from places.models import Place, Category

User = get_user_model()


class ReviewServiceTestCase(TransactionTestCase):
    """Test ReviewService methods."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@test.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='reviewer2',
            email='reviewer2@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Test Category')
        self.place = Place.objects.create(
            name='Test Place',
            category=self.category,
            is_active=True,
            avg_rating=0,
            rating_count=0
        )
    
    @patch('interactions.services.review_service.analyze_text')
    def test_create_review_success(self, mock_analyze):
        """Creating a review should succeed with valid data."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        success, result = ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=5,
            comment='مكان رائع جداً! أنصح الجميع بزيارته.'
        )
        
        self.assertTrue(success)
        self.assertIsInstance(result, Review)
        self.assertEqual(result.rating, 5)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.place, self.place)
    
    @patch('interactions.services.review_service.analyze_text')
    def test_create_review_updates_place_rating(self, mock_analyze):
        """Creating a review should update place's avg_rating."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        # Create first review with 5 stars
        ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=5,
            comment='ممتاز'
        )
        
        self.place.refresh_from_db()
        self.assertEqual(self.place.avg_rating, 5.0)
        self.assertEqual(self.place.rating_count, 1)
        
        # Create second review with 3 stars
        ReviewService.create_review(
            user=self.user2,
            place=self.place,
            rating=3,
            comment='جيد'
        )
        
        self.place.refresh_from_db()
        self.assertEqual(self.place.avg_rating, 4.0)  # (5+3)/2
        self.assertEqual(self.place.rating_count, 2)
    
    @patch('interactions.services.review_service.analyze_text')
    def test_create_review_duplicate_fails(self, mock_analyze):
        """User cannot create duplicate review for same place."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        # First review
        ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=4,
            comment='جيد جداً'
        )
        
        # Duplicate attempt
        success, result = ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=5,
            comment='ممتاز'
        )
        
        self.assertFalse(success)
        self.assertIn('تقييم سابق', result)
    
    def test_create_review_invalid_rating(self):
        """Rating must be between 1 and 5."""
        success, result = ReviewService.create_review(
            user=self.user,
            place=self.place,
            rating=6,  # Invalid
            comment='Test'
        )
        
        self.assertFalse(success)
        self.assertIn('1 و 5', result)
    
    @patch('interactions.services.review_service.analyze_text')
    def test_create_review_rate_limited(self, mock_analyze):
        """User cannot create more than 10 reviews per day."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        # Create 10 places and reviews
        for i in range(10):
            place = Place.objects.create(
                name=f'Place {i}',
                category=self.category,
                is_active=True
            )
            Review.objects.create(
                user=self.user,
                place=place,
                rating=4,
                comment='Test'
            )
        
        # 11th attempt should fail
        new_place = Place.objects.create(
            name='New Place',
            category=self.category,
            is_active=True
        )
        
        success, result = ReviewService.create_review(
            user=self.user,
            place=new_place,
            rating=5,
            comment='Test'
        )
        
        self.assertFalse(success)
        self.assertIn('الحد اليومي', result)
    
    @patch('interactions.services.review_service.analyze_text')
    def test_update_review_success(self, mock_analyze):
        """Updating a review should work for owner."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        review = Review.objects.create(
            user=self.user,
            place=self.place,
            rating=3,
            comment='جيد نوعاً ما'
        )
        
        success, result = ReviewService.update_review(
            user=self.user,
            review_id=review.pk,
            rating=5,
            comment='ممتاز بعد التحديثات الأخيرة'
        )
        
        self.assertTrue(success)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertIn('ممتاز', review.comment)


class ReportServiceTestCase(TransactionTestCase):
    """Test ReportService methods."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='reporter',
            email='reporter@test.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_superuser(
            username='admin_report',
            email='admin_report@test.com',
            password='adminpass123'
        )
        
        self.category = Category.objects.create(name='Test Category')
        self.place = Place.objects.create(
            name='Report Test Place',
            category=self.category,
            is_active=True
        )
    
    @patch('interactions.services.report_service.analyze_text')
    @patch('interactions.services.report_service.ReportService._notify_admins')
    def test_create_report_success(self, mock_notify, mock_analyze):
        """Creating a report should succeed with valid data."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        report = ReportService.create_report(
            user=self.user,
            content_object=self.place,
            report_type='INACCURATE',
            description='معلومات الموقع غير دقيقة'
        )
        
        self.assertIsNotNone(report)
        self.assertEqual(report.status, 'NEW')
        self.assertEqual(report.report_type, 'INACCURATE')
        self.assertEqual(report.priority, 'medium')  # INACCURATE = medium
    
    @patch('interactions.services.report_service.analyze_text')
    @patch('interactions.services.report_service.ReportService._notify_admins')
    def test_create_report_safety_is_critical(self, mock_notify, mock_analyze):
        """Safety reports should have critical priority."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        report = ReportService.create_report(
            user=self.user,
            content_object=self.place,
            report_type='SAFETY',
            description='مخاطر أمنية في هذا المكان'
        )
        
        self.assertEqual(report.priority, 'critical')
        self.assertIsNotNone(report.expected_resolution_at)
    
    @patch('interactions.services.report_service.analyze_text')
    @patch('interactions.services.report_service.ReportService._notify_admins')
    def test_create_report_sla_is_set(self, mock_notify, mock_analyze):
        """Report should have SLA based on type."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        report = ReportService.create_report(
            user=self.user,
            content_object=self.place,
            report_type='SAFETY',
            description='مخاطر'
        )
        
        # SAFETY SLA is 1 hour
        expected_sla = timezone.now() + timedelta(hours=1)
        self.assertAlmostEqual(
            report.expected_resolution_at.timestamp(),
            expected_sla.timestamp(),
            delta=60  # Within 1 minute
        )
    
    @patch('interactions.services.report_service.analyze_text')
    @patch('interactions.services.report_service.ReportService._notify_admins')
    def test_rate_limit_exceeded(self, mock_notify, mock_analyze):
        """User cannot create more than 5 reports per day."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        # Create 5 reports on different places
        for i in range(5):
            place = Place.objects.create(
                name=f'Report Place {i}',
                category=self.category,
                is_active=True
            )
            Report.objects.create(
                user=self.user,
                content_object=place,
                report_type='OTHER',
                description=f'Test {i}',
                status='NEW'
            )
        
        # 6th attempt should fail
        new_place = Place.objects.create(
            name='New Report Place',
            category=self.category,
            is_active=True
        )
        
        with self.assertRaises(ValidationError) as ctx:
            ReportService.create_report(
                user=self.user,
                content_object=new_place,
                report_type='OTHER',
                description='Test'
            )
        
        self.assertIn('الحد اليومي', str(ctx.exception))
    
    @patch('interactions.services.report_service.analyze_text')
    @patch('interactions.services.report_service.ReportService._notify_admins')
    def test_duplicate_report_prevented(self, mock_notify, mock_analyze):
        """Cannot submit duplicate report for same object."""
        mock_analyze.return_value = MagicMock(action='allow', message='')
        
        # First report
        ReportService.create_report(
            user=self.user,
            content_object=self.place,
            report_type='SPAM',
            description='محتوى مزعج'
        )
        
        # Duplicate attempt
        with self.assertRaises(ValidationError) as ctx:
            ReportService.create_report(
                user=self.user,
                content_object=self.place,
                report_type='SPAM',
                description='نفس المشكلة'
            )
        
        self.assertIn('مشابه', str(ctx.exception))
    
    def test_resolve_report(self):
        """Resolving a report should update status and timestamp."""
        report = Report.objects.create(
            user=self.user,
            content_object=self.place,
            report_type='INACCURATE',
            description='Test',
            status='IN_PROGRESS'
        )
        
        result = ReportService.resolve_report(
            report=report,
            resolver=self.admin,
            resolution_note='تم تصحيح المعلومات'
        )
        
        self.assertTrue(result)
        report.refresh_from_db()
        self.assertEqual(report.status, 'RESOLVED')
        self.assertIsNotNone(report.resolved_at)
        self.assertEqual(report.assigned_to, self.admin)
    
    def test_reject_report(self):
        """Rejecting a report should update status."""
        report = Report.objects.create(
            user=self.user,
            content_object=self.place,
            report_type='OTHER',
            description='Test',
            status='NEW'
        )
        
        result = ReportService.reject_report(
            report=report,
            resolver=self.admin,
            rejection_reason='البلاغ غير صحيح'
        )
        
        self.assertTrue(result)
        report.refresh_from_db()
        self.assertEqual(report.status, 'REJECTED')
