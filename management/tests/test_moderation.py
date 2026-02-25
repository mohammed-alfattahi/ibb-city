"""
Moderation Tests
Tests for normalization, moderation logic, and integration.
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from management.models.moderation import BannedWord, ModerationEvent
from management.services.normalization import normalize_text
from management.services.moderation_service import analyze_text, invalidate_word_cache
from places.models import Place, Category

User = get_user_model()


class NormalizationTest(TestCase):
    def test_arabic_normalization(self):
        """Test normalization of Arabic variants."""
        # Alef variants
        self.assertEqual(normalize_text("إسلام"), "اسلام")
        self.assertEqual(normalize_text("آمل"), "امل")
        
        # Teh Marbuta
        self.assertEqual(normalize_text("مدرسة"), "مدرسه")
        
        # Yeh
        self.assertEqual(normalize_text("على"), "علي")
        
        # Diacritics
        self.assertEqual(normalize_text("مَرْحَبًا"), "مرحبا")
        
        # Mixed
        self.assertEqual(normalize_text("الإعْدَادَات"), "الاعدادات")

    def test_english_normalization(self):
        """Test English normalization."""
        self.assertEqual(normalize_text("HeLLo World"), "hello world")
        self.assertEqual(normalize_text("  Trim Me  "), "trim me")


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class ModerationServiceTest(TestCase):
    def setUp(self):
        cache.clear()
        invalidate_word_cache()
        # Create banned words
        BannedWord.objects.create(term="badword", severity="high", is_active=True)
        BannedWord.objects.create(term="mildword", severity="low", is_active=True)
        BannedWord.objects.create(term="شتم", severity="high", is_active=True)
        
    def test_clean_text(self):
        result = analyze_text("This is clean text")
        self.assertEqual(result.action, "allow")
        self.assertEqual(result.severity, "none")

    def test_high_severity_block(self):
        result = analyze_text("This contains badword in it")
        self.assertEqual(result.action, "block")
        self.assertEqual(result.severity, "high")
        self.assertIn("badword", result.matched)

    def test_low_severity_warn(self):
        result = analyze_text("This contains mildword in it")
        self.assertEqual(result.action, "warn")
        self.assertEqual(result.severity, "low")
        
    def test_arabic_block(self):
        result = analyze_text("هذا نص فيه شتم سيء")
        self.assertEqual(result.action, "block")
        self.assertEqual(result.severity, "high")
        self.assertIn("شتم", result.matched)

    def test_normalization_match(self):
        # "BaDWord" should match "badword"
        result = analyze_text("Don't say BaDwOrD")
        self.assertEqual(result.action, "block")


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class ModerationIntegrationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='tester', password='pw')
        # Fix: Category does not have a slug field
        self.category = Category.objects.create(name='Test Cat')
        self.place = Place.objects.create(name='Test Place', category=self.category)
        
        cache.clear()
        BannedWord.objects.create(term="spam", severity="high", is_active=True)
        invalidate_word_cache()

    def test_review_blocked(self):
        """Test that review_create blocks content."""
        from interactions.views_public import review_create
        
        # Need to handle messages framework mocking fully or use Client
        # Using Client is better for integration
        self.client.force_login(self.user)
        # Fix URL: /place/{pk}/review/create/
        response = self.client.post(f'/place/{self.place.pk}/review/create/', {
            'rating': 5,
            'comment': 'This is spam content'
        })
        
        # Should redirect back to place detail
        self.assertEqual(response.status_code, 302)
        
        # Verify event logged
        self.assertTrue(ModerationEvent.objects.filter(user=self.user, severity='high').exists())
        
        # Verify review NOT created
        from interactions.models import Review
        self.assertEqual(Review.objects.count(), 0)

    def test_review_allowed(self):
        self.client.force_login(self.user)
        # Fix URL: /place/{pk}/review/create/
        response = self.client.post(f'/place/{self.place.pk}/review/create/', {
            'rating': 5,
            'comment': 'This is good content'
        })
        self.assertEqual(response.status_code, 302)
        
        from interactions.models import Review
        self.assertEqual(Review.objects.count(), 1)
