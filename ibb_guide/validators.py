"""
Central Validation Service - Unified validation logic for the entire application.

This module consolidates all validation rules in one place for use across:
- Django Forms
- DRF Serializers
- Model clean() methods
- Service layer

Usage:
    from ibb_guide.validators import ValidationService
    
    # In a form or serializer
    ValidationService.validate_establishment_name(name, owner)
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ValidationService:
    """Centralized validation logic for the application."""
    
    # ==========================================
    # Establishment Validators
    # ==========================================
    
    @staticmethod
    def validate_establishment_name(name: str, owner, directorate=None, exclude_pk=None) -> None:
        """
        Validate establishment name uniqueness per owner AND directorate.
        Allows same name in different locations (branches).
        """
        from places.models import Establishment
        
        if not name or len(name.strip()) < 3:
            raise ValidationError(_("اسم المنشأة يجب أن يكون 3 أحرف على الأقل."))
        
        query = Establishment.objects.filter(
            owner=owner,
            name__iexact=name.strip()
        )
        
        # If directorate is provided, scope uniqueness to it.
        # If not provided, it falls back to strict unique-per-owner (safe default)
        if directorate:
            query = query.filter(directorate=directorate)

        if exclude_pk:
            query = query.exclude(pk=exclude_pk)
        
        if query.exists():
            if directorate:
                raise ValidationError(_("لديك منشأة أخرى بنفس الاسم في هذه المديرية."))
            else:
                raise ValidationError(_("لديك منشأة أخرى بنفس الاسم."))
    
    @staticmethod
    def validate_working_hours(working_hours: dict) -> None:
        """
        Validate working hours format.
        
        Expected format: {"monday": {"open": "09:00", "close": "22:00"}, ...}
        """
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        for day, hours in working_hours.items():
            if day.lower() not in valid_days:
                raise ValidationError(_(f"يوم غير صالح: {day}"))
            
            if hours and isinstance(hours, dict):
                if 'open' in hours and hours['open'] and not time_pattern.match(hours['open']):
                    raise ValidationError(_(f"وقت فتح غير صالح ليوم {day}"))
                if 'close' in hours and hours['close'] and not time_pattern.match(hours['close']):
                    raise ValidationError(_(f"وقت إغلاق غير صالح ليوم {day}"))
    
    # ==========================================
    # Advertisement Validators
    # ==========================================
    
    @staticmethod
    def validate_ad_for_place(place, status: str, exclude_pk=None) -> None:
        """
        Validate that there's no duplicate pending/active ad for a place.
        
        Raises:
            ValidationError: If duplicate ad exists
        """
        from management.models import Advertisement
        
        if status in ['pending', 'active']:
            query = Advertisement.objects.filter(
                place=place,
                status=status
            )
            if exclude_pk:
                query = query.exclude(pk=exclude_pk)
            
            if query.exists():
                status_display = "معلق" if status == 'pending' else "نشط"
                raise ValidationError(_(f"يوجد إعلان {status_display} لهذا المكان بالفعل."))
    
    @staticmethod
    def validate_ad_duration(duration_days: int) -> None:
        """Validate advertisement duration."""
        if duration_days < 1:
            raise ValidationError(_("مدة الإعلان يجب أن تكون يوم واحد على الأقل."))
        if duration_days > 365:
            raise ValidationError(_("مدة الإعلان لا يمكن أن تتجاوز 365 يوماً."))
    
    @staticmethod
    def validate_ad_price(price, discount_price=None) -> None:
        """Validate advertisement pricing."""
        if price is not None and price < 0:
            raise ValidationError(_("السعر لا يمكن أن يكون سالباً."))
        
        if discount_price is not None:
            if discount_price < 0:
                raise ValidationError(_("سعر الخصم لا يمكن أن يكون سالباً."))
            if price and discount_price >= price:
                raise ValidationError(_("سعر الخصم يجب أن يكون أقل من السعر الأصلي."))
    
    # ==========================================
    # User/Partner Validators
    # ==========================================
    
    @staticmethod
    def validate_phone_number(phone: str) -> None:
        """Validate Yemeni phone number format."""
        if not phone:
            return
        
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', phone)
        
        # Yemeni mobile: starts with 7 followed by 8 digits
        if not re.match(r'^(967)?7[0-9]{8}$', phone):
            raise ValidationError(_("رقم الهاتف غير صالح. يجب أن يبدأ بـ 7 ويتكون من 9 أرقام."))
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format."""
        from django.core.validators import validate_email as django_validate_email
        try:
            django_validate_email(email)
        except ValidationError:
            raise ValidationError(_("البريد الإلكتروني غير صالح."))
    
    # ==========================================
    # Common Validators
    # ==========================================
    
    @staticmethod
    def validate_coordinates(latitude, longitude) -> None:
        """Validate geographic coordinates."""
        if latitude is not None:
            if latitude < -90 or latitude > 90:
                raise ValidationError(_("خط العرض غير صالح."))
        
        if longitude is not None:
            if longitude < -180 or longitude > 180:
                raise ValidationError(_("خط الطول غير صالح."))
    
    # Allowed file types for security
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    ALLOWED_DOCUMENT_TYPES = ['application/pdf']
    
    @staticmethod
    def validate_image_size(image, max_mb: int = 5) -> None:
        """Validate image file size."""
        if image and hasattr(image, 'size'):
            max_bytes = max_mb * 1024 * 1024
            if image.size > max_bytes:
                raise ValidationError(_(f"حجم الصورة يجب ألا يتجاوز {max_mb} ميجابايت."))
    
    @staticmethod
    def validate_image_type(image) -> None:
        """
        Validate image file type for security.
        Prevents upload of malicious files disguised as images.
        """
        if not image:
            return
        
        content_type = getattr(image, 'content_type', None)
        if content_type and content_type not in ValidationService.ALLOWED_IMAGE_TYPES:
            raise ValidationError(_("نوع الملف غير مدعوم. الأنواع المسموحة: JPEG, PNG, WebP, GIF"))
    
    @staticmethod
    def validate_document_type(document) -> None:
        """Validate document file type (PDF only)."""
        if not document:
            return
        
        content_type = getattr(document, 'content_type', None)
        if content_type and content_type not in ValidationService.ALLOWED_DOCUMENT_TYPES:
            raise ValidationError(_("نوع المستند غير مدعوم. النوع المسموح: PDF فقط"))
    
    @staticmethod
    def validate_required_field(value, field_name: str) -> None:
        """Generic required field validator."""
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationError(_(f"الحقل {field_name} مطلوب."))

