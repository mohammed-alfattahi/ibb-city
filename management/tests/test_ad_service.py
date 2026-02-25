"""
Tests for AdService
اختبارات خدمة الإعلانات
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from management.models import Advertisement, Invoice
from management.services.ad_service import AdService
from places.models import Place, Category

User = get_user_model()


class AdServiceTestCase(TransactionTestCase):
    """Test AdService methods."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner_ad',
            email='partner_ad@test.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_superuser(
            username='admin_ad',
            email='admin_ad@test.com',
            password='adminpass123'
        )
        
        self.category = Category.objects.create(name='Test Category')
        self.place = Place.objects.create(
            name='Test Place',
            category=self.category,
            is_active=True
        )
    
    def test_create_ad_draft_creates_invoice(self):
        """Creating ad draft should also create an unpaid invoice."""
        ad = AdService.create_ad_draft(
            user=self.user,
            place=self.place,
            title='Test Ad',
            description='Test Description',
            banner_image='test.jpg',
            duration_days=7
        )
        
        self.assertEqual(ad.status, 'draft')
        self.assertEqual(ad.owner, self.user)
        
        # Check invoice was created
        invoice = Invoice.objects.filter(advertisement=ad).first()
        self.assertIsNotNone(invoice)
        self.assertFalse(invoice.is_paid)
        self.assertEqual(invoice.partner, self.user)
    
    def test_create_ad_draft_validation(self):
        """Duration must be at least 1 day."""
        with self.assertRaises(ValidationError):
            AdService.create_ad_draft(
                user=self.user,
                place=self.place,
                title='Test Ad',
                description='Test',
                banner_image='test.jpg',
                duration_days=0  # Invalid
            )
    
    def test_submit_payment_changes_status(self):
        """Submitting payment should change status to pending."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='draft'
        )
        
        result = AdService.submit_payment(
            ad=ad,
            receipt_image='receipt.jpg',
            transaction_ref='TXN123'
        )
        
        self.assertTrue(result)
        ad.refresh_from_db()
        self.assertEqual(ad.status, 'pending')
        self.assertEqual(ad.transaction_reference, 'TXN123')
    
    def test_process_approval_activates_ad(self):
        """Approval should activate ad and mark invoice as paid."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='pending'
        )
        
        invoice = Invoice.objects.create(
            advertisement=ad,
            partner=self.user,
            amount=7000,
            total_amount=7000,
            is_paid=False
        )
        
        result = AdService.process_approval(ad, self.admin, approved=True)
        
        ad.refresh_from_db()
        invoice.refresh_from_db()
        
        self.assertEqual(ad.status, 'active')
        self.assertIsNotNone(ad.end_date)
        self.assertTrue(invoice.is_paid)
    
    def test_process_rejection(self):
        """Rejection should set status and store reason."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='pending'
        )
        
        result = AdService.process_approval(
            ad, self.admin, 
            approved=False, 
            rejection_reason='صورة غير واضحة'
        )
        
        ad.refresh_from_db()
        self.assertEqual(ad.status, 'rejected')
        self.assertIn('صورة غير واضحة', ad.admin_notes)
    
    def test_pause_ad(self):
        """Pausing should store remaining days."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=10,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=10),
            status='active'
        )
        
        success, message = AdService.pause_ad(ad, self.user)
        
        self.assertTrue(success)
        ad.refresh_from_db()
        self.assertEqual(ad.status, 'paused')
        self.assertGreater(ad.duration_days, 0)  # Remaining days saved
    
    def test_pause_inactive_ad_fails(self):
        """Cannot pause non-active ad."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='draft'
        )
        
        success, message = AdService.pause_ad(ad)
        
        self.assertFalse(success)
    
    def test_resume_ad(self):
        """Resuming should recalculate end date."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=5,  # 5 remaining days
            start_date=timezone.now().date(),
            status='paused'
        )
        
        success, message = AdService.resume_ad(ad, self.user)
        
        self.assertTrue(success)
        ad.refresh_from_db()
        self.assertEqual(ad.status, 'active')
        expected_end = timezone.now().date() + timedelta(days=5)
        self.assertEqual(ad.end_date, expected_end)
    
    def test_extend_ad(self):
        """Extending should add days and create invoice."""
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Test Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=7),
            status='active'
        )
        
        original_end = ad.end_date
        invoice_count_before = Invoice.objects.filter(advertisement=ad).count()
        
        success, message, cost = AdService.extend_ad(ad, extra_days=3, user=self.user)
        
        self.assertTrue(success)
        ad.refresh_from_db()
        self.assertEqual(ad.duration_days, 10)  # 7 + 3
        self.assertEqual(ad.end_date, original_end + timedelta(days=3))
        
        # Check extension invoice created
        invoice_count_after = Invoice.objects.filter(advertisement=ad).count()
        self.assertEqual(invoice_count_after, invoice_count_before + 1)
    
    def test_check_expirations(self):
        """Expired ads should be marked as expired."""
        # Create expired ad
        ad = Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Expired Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=3),  # Expired 3 days ago
            status='active'
        )
        
        expired_count = AdService.check_expirations()
        
        self.assertEqual(expired_count, 1)
        ad.refresh_from_db()
        self.assertEqual(ad.status, 'expired')
    
    def test_get_partner_stats(self):
        """Should return correct statistics."""
        # Create some ads
        Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Active Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='active',
            views=100,
            clicks=10
        )
        
        Advertisement.objects.create(
            owner=self.user,
            place=self.place,
            title='Pending Ad',
            banner_image='test.jpg',
            duration_days=7,
            start_date=timezone.now().date(),
            status='pending'
        )
        
        stats = AdService.get_partner_stats(self.user)
        
        self.assertEqual(stats['total_ads'], 2)
        self.assertEqual(stats['active_ads'], 1)
        self.assertEqual(stats['pending_ads'], 1)
        self.assertEqual(stats['total_views'], 100)
        self.assertEqual(stats['total_clicks'], 10)
