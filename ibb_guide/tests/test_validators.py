"""
Tests for the centralized ValidationService.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from unittest.mock import MagicMock

from ibb_guide.validators import ValidationService

User = get_user_model()


class EstablishmentValidatorTests(TestCase):
    """Test establishment-related validators."""
    
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
    
    def test_valid_establishment_name(self):
        """Valid names should not raise."""
        # Should not raise
        ValidationService.validate_establishment_name("فندق الحديقة", self.owner)
    
    def test_short_name_raises(self):
        """Names less than 3 chars should raise."""
        with self.assertRaises(ValidationError) as ctx:
            ValidationService.validate_establishment_name("AB", self.owner)
        self.assertIn("3 أحرف", str(ctx.exception))
    
    def test_empty_name_raises(self):
        """Empty names should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_establishment_name("", self.owner)
    
    def test_duplicate_name_for_same_owner(self):
        """Duplicate name for same owner should raise."""
        from places.models import Establishment, Category
        
        # Create category first
        category = Category.objects.create(name='Hotels')
        
        # Create first establishment
        Establishment.objects.create(name="فندق الجبل", owner=self.owner, category=category)
        
        # Try to create another with same name
        with self.assertRaises(ValidationError) as ctx:
            ValidationService.validate_establishment_name("فندق الجبل", self.owner)
        self.assertIn("نفس الاسم", str(ctx.exception))


class WorkingHoursValidatorTests(TestCase):
    """Test working hours validation."""
    
    def test_valid_working_hours(self):
        """Valid working hours should not raise."""
        hours = {
            "monday": {"open": "09:00", "close": "22:00"},
            "tuesday": {"open": "09:00", "close": "22:00"},
        }
        # Should not raise
        ValidationService.validate_working_hours(hours)
    
    def test_invalid_day_raises(self):
        """Invalid day names should raise."""
        hours = {"invalidday": {"open": "09:00", "close": "22:00"}}
        with self.assertRaises(ValidationError) as ctx:
            ValidationService.validate_working_hours(hours)
        self.assertIn("غير صالح", str(ctx.exception))
    
    def test_invalid_time_format_raises(self):
        """Invalid time format should raise."""
        hours = {"monday": {"open": "9am", "close": "22:00"}}
        with self.assertRaises(ValidationError):
            ValidationService.validate_working_hours(hours)


class PhoneValidatorTests(TestCase):
    """Test Yemeni phone number validation."""
    
    def test_valid_phone(self):
        """Valid Yemeni mobile numbers should pass."""
        ValidationService.validate_phone_number("771234567")
        ValidationService.validate_phone_number("967771234567")
    
    def test_invalid_phone_raises(self):
        """Invalid phone numbers should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_phone_number("123456")  # Too short
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_phone_number("8712345678")  # Doesn't start with 7


class CoordinateValidatorTests(TestCase):
    """Test geographic coordinate validation."""
    
    def test_valid_coordinates(self):
        """Valid coordinates should pass."""
        ValidationService.validate_coordinates(15.35, 44.22)
    
    def test_latitude_out_of_range(self):
        """Latitude outside -90 to 90 should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_coordinates(91, 44.22)
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_coordinates(-91, 44.22)
    
    def test_longitude_out_of_range(self):
        """Longitude outside -180 to 180 should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_coordinates(15, 181)


class FileValidatorTests(TestCase):
    """Test file validation methods."""
    
    def test_valid_image_size(self):
        """Images under limit should pass."""
        mock_image = MagicMock()
        mock_image.size = 2 * 1024 * 1024  # 2MB
        ValidationService.validate_image_size(mock_image, max_mb=5)
    
    def test_oversized_image_raises(self):
        """Images over limit should raise."""
        mock_image = MagicMock()
        mock_image.size = 10 * 1024 * 1024  # 10MB
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_image_size(mock_image, max_mb=5)
    
    def test_valid_image_type(self):
        """Allowed image types should pass."""
        mock_image = MagicMock()
        mock_image.content_type = 'image/jpeg'
        ValidationService.validate_image_type(mock_image)
        
        mock_image.content_type = 'image/png'
        ValidationService.validate_image_type(mock_image)
    
    def test_invalid_image_type_raises(self):
        """Disallowed types should raise."""
        mock_image = MagicMock()
        mock_image.content_type = 'application/pdf'
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_image_type(mock_image)
    
    def test_valid_document_type(self):
        """PDF documents should pass."""
        mock_doc = MagicMock()
        mock_doc.content_type = 'application/pdf'
        ValidationService.validate_document_type(mock_doc)
    
    def test_invalid_document_type_raises(self):
        """Non-PDF documents should raise."""
        mock_doc = MagicMock()
        mock_doc.content_type = 'application/msword'
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_document_type(mock_doc)


class AdValidatorTests(TestCase):
    """Test advertisement validation."""
    
    def test_valid_ad_duration(self):
        """Valid durations should pass."""
        ValidationService.validate_ad_duration(7)
        ValidationService.validate_ad_duration(30)
        ValidationService.validate_ad_duration(365)
    
    def test_invalid_ad_duration(self):
        """Invalid durations should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_ad_duration(0)
        
        with self.assertRaises(ValidationError):
            ValidationService.validate_ad_duration(400)
    
    def test_valid_ad_pricing(self):
        """Valid pricing should pass."""
        ValidationService.validate_ad_price(100, discount_price=80)
    
    def test_negative_price_raises(self):
        """Negative prices should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_ad_price(-100)
    
    def test_discount_higher_than_price_raises(self):
        """Discount higher than original should raise."""
        with self.assertRaises(ValidationError):
            ValidationService.validate_ad_price(100, discount_price=120)
