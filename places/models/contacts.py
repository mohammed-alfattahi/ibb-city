"""
Establishment Contact Models
نماذج جهات اتصال المنشآت

Supports multiple phone numbers with Yemen carrier types and social/contact methods.
"""
import uuid
import re
from django.db import models
from django.core.validators import EmailValidator, URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ibb_guide.base_models import TimeStampedModel

User = get_user_model()


def validate_yemen_phone(value):
    """
    Validate Yemen phone number formats:
    - +967 7xx xxx xxx
    - 7xxxxxxxx
    - 0x xxx xxx (landline)
    """
    # Remove spaces, dashes
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Pattern for Yemen mobile: +967 7xxxxxxxx or 7xxxxxxxx
    mobile_pattern = r'^(\+967)?7[0-9]{8}$'
    # Pattern for landline: +967 x xxx xxx or 0x xxx xxx
    landline_pattern = r'^(\+967)?0?[1-6][0-9]{6,7}$'
    
    if re.match(mobile_pattern, cleaned) or re.match(landline_pattern, cleaned):
        return cleaned
    
    raise ValidationError(
        _('رقم هاتف يمني غير صالح. استخدم صيغة: 7xxxxxxxx أو +967 7xxxxxxxx'),
        code='invalid_yemen_phone'
    )


class EstablishmentContact(TimeStampedModel):
    """
    Normalized contact model for establishments.
    Supports multiple phones with carrier types and social/contact methods.
    """
    
    # Contact Types
    CONTACT_TYPE_CHOICES = [
        ('phone', _('هاتف')),
        ('whatsapp', _('واتساب')),
        ('telegram', _('تيليجرام')),
        ('facebook', _('فيسبوك')),
        ('instagram', _('انستغرام')),
        ('tiktok', _('تيك توك')),
        ('snapchat', _('سناب شات')),
        ('youtube', _('يوتيوب')),
        ('website', _('موقع إلكتروني')),
        ('email', _('بريد إلكتروني')),
        ('google_maps', _('خرائط جوجل')),
        ('other', _('أخرى')),
    ]
    
    # Yemen Carrier Choices (for phone type only)
    CARRIER_CHOICES = [
        ('sabafon', _('سبأفون')),
        ('yemen_mobile', _('يمن موبايل')),
        ('you', _('يو')),
        ('wai', _('واي')),
        ('landline', _('أرضي')),
        ('other', _('أخرى')),
    ]
    
    # Types that require URL validation
    URL_TYPES = ['website', 'facebook', 'instagram', 'tiktok', 'snapchat', 'youtube', 'google_maps']
    
    # Types that can be phone-based
    PHONE_BASED_TYPES = ['phone', 'whatsapp', 'telegram']
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    establishment = models.ForeignKey(
        'places.Establishment',
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('المنشأة')
    )
    
    type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        verbose_name=_('نوع جهة الاتصال')
    )
    
    carrier = models.CharField(
        max_length=20,
        choices=CARRIER_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('الناقل/المشغل')
    )
    
    label = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_('التسمية'),
        help_text=_('مثال: الرقم الرئيسي، خدمة العملاء')
    )
    
    value = models.CharField(
        max_length=255,
        verbose_name=_('القيمة'),
        help_text=_('رقم الهاتف أو الرابط أو البريد')
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('جهة اتصال رئيسية')
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('ترتيب العرض')
    )
    
    is_visible = models.BooleanField(
        default=True,
        verbose_name=_('مرئي للزوار')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_contacts',
        verbose_name=_('أضيف بواسطة')
    )
    
    class Meta:
        verbose_name = _('جهة اتصال')
        verbose_name_plural = _('جهات الاتصال')
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['establishment', 'type', 'display_order']),
            models.Index(fields=['establishment', 'is_visible']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value[:30]}"
    
    def clean(self):
        """Validate contact based on type."""
        super().clean()
        
        # Phone validation
        if self.type == 'phone':
            if not self.carrier:
                raise ValidationError({'carrier': _('يجب تحديد المشغل للهاتف')})
            try:
                self.value = validate_yemen_phone(self.value)
            except ValidationError as e:
                raise ValidationError({'value': e.message})
        
        # Email validation
        elif self.type == 'email':
            validator = EmailValidator()
            try:
                validator(self.value)
            except ValidationError:
                raise ValidationError({'value': _('بريد إلكتروني غير صالح')})
        
        # URL validation for social/website types
        elif self.type in self.URL_TYPES:
            # Allow handles without full URL for social media
            if self.type in ['instagram', 'tiktok', 'snapchat'] and not self.value.startswith('http'):
                # Accept username/handle format
                if not re.match(r'^@?[\w.]+$', self.value):
                    raise ValidationError({'value': _('اسم مستخدم غير صالح')})
            else:
                validator = URLValidator()
                try:
                    validator(self.value)
                except ValidationError:
                    raise ValidationError({'value': _('رابط غير صالح')})
        
        # WhatsApp/Telegram can be phone or username
        elif self.type in ['whatsapp', 'telegram']:
            # Try phone validation first
            try:
                cleaned = re.sub(r'[\s\-\(\)]', '', self.value)
                if cleaned.startswith('+') or cleaned[0].isdigit():
                    self.value = validate_yemen_phone(self.value)
            except ValidationError:
                # Accept as username if not a valid phone
                if self.type == 'telegram' and not re.match(r'^@?[\w]+$', self.value):
                    raise ValidationError({'value': _('اسم مستخدم أو رقم هاتف غير صالح')})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Ensure only one primary per establishment
        if self.is_primary:
            EstablishmentContact.objects.filter(
                establishment=self.establishment,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @property
    def icon_class(self):
        """Return Font Awesome icon class for contact type."""
        icons = {
            'phone': 'fas fa-phone',
            'whatsapp': 'fab fa-whatsapp',
            'telegram': 'fab fa-telegram',
            'facebook': 'fab fa-facebook',
            'instagram': 'fab fa-instagram',
            'tiktok': 'fab fa-tiktok',
            'snapchat': 'fab fa-snapchat',
            'youtube': 'fab fa-youtube',
            'website': 'fas fa-globe',
            'email': 'fas fa-envelope',
            'google_maps': 'fas fa-map-marker-alt',
            'other': 'fas fa-link',
        }
        return icons.get(self.type, 'fas fa-link')
    
    @property
    def carrier_icon_class(self):
        """Return CSS class for Yemen carrier icon (Fallback)."""
        carriers = {
            'sabafon': 'carrier-sabafon',
            'yemen_mobile': 'carrier-yemen-mobile',
            'you': 'carrier-you',
            'wai': 'carrier-wai',
            'landline': 'carrier-landline',
        }
        return carriers.get(self.carrier, '')

    @property
    def carrier_icon_path(self):
        """Return path to carrier SVG icon."""
        if not self.carrier or self.carrier == 'other':
            return None
        return f"img/carriers/{self.carrier}.svg"

    
    @property
    def action_url(self):
        """Return the action URL for quick actions."""
        if self.type == 'phone':
            return f"tel:{self.value}"
        elif self.type == 'whatsapp':
            # Clean phone for WhatsApp
            phone = re.sub(r'[^\d+]', '', self.value)
            if not phone.startswith('+'):
                phone = '+967' + phone.lstrip('0')
            return f"https://wa.me/{phone.replace('+', '')}"
        elif self.type == 'telegram':
            if self.value.startswith('@'):
                return f"https://t.me/{self.value[1:]}"
            elif self.value.startswith('http'):
                return self.value
            else:
                # Assume phone number
                return f"https://t.me/{self.value}"
        elif self.type == 'email':
            return f"mailto:{self.value}"
        elif self.type in self.URL_TYPES:
            if self.value.startswith('http'):
                return self.value
            # Build URL for social handles
            if self.type == 'instagram':
                return f"https://instagram.com/{self.value.lstrip('@')}"
            elif self.type == 'facebook':
                return f"https://facebook.com/{self.value.lstrip('@')}"
            elif self.type == 'tiktok':
                return f"https://tiktok.com/@{self.value.lstrip('@')}"
            elif self.type == 'snapchat':
                return f"https://snapchat.com/add/{self.value.lstrip('@')}"
            elif self.type == 'youtube':
                return f"https://youtube.com/{self.value}"
        return self.value
    
    @property
    def action_label(self):
        """Return action button label."""
        labels = {
            'phone': _('اتصال'),
            'whatsapp': _('مراسلة'),
            'telegram': _('مراسلة'),
            'facebook': _('زيارة'),
            'instagram': _('زيارة'),
            'tiktok': _('زيارة'),
            'snapchat': _('إضافة'),
            'youtube': _('مشاهدة'),
            'website': _('زيارة'),
            'email': _('إرسال'),
            'google_maps': _('عرض'),
            'other': _('فتح'),
        }
        return labels.get(self.type, _('فتح'))
