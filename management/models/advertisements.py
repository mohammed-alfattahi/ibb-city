"""
Advertisement Models
نماذج الإعلانات والفواتير
"""
from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel


class Advertisement(models.Model):
    """
    Advertisement Lifecycle States:
    - DRAFT: Partner is preparing the ad (not submitted)
    - PENDING: Submitted for admin approval
    - ACTIVE: Approved and currently running
    - PAUSED: Temporarily stopped by partner
    - EXPIRED: Ad duration has ended
    - REJECTED: Admin rejected the ad
    - PAYMENT_ISSUE: Payment needs to be re-uploaded
    """
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('pending', 'قيد المراجعة'),
        ('active', 'نشط'),
        ('paused', 'متوقف مؤقتاً'),
        ('expired', 'منتهي'),
        ('rejected', 'مرفوض'),
        ('payment_issue', 'مشكلة في الدفع'),
    )

    PLACEMENT_CHOICES = (
        ('banner', 'بانر رئيسي (Homepage)'),
        ('sidebar', 'شريط جانبي (Sidebar)'),
        ('navbar', 'شريط علوي (Navbar)'),
    )

    placement = models.CharField(
        max_length=20, 
        choices=PLACEMENT_CHOICES, 
        default='banner',
        verbose_name='مكان الإعلان'
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ads', null=True, blank=True)
    place = models.ForeignKey('places.Place', on_delete=models.CASCADE, related_name='ads', null=True, blank=True)
    title = models.CharField(max_length=200, default='New Ad')
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='ads/banners/', null=True, blank=True)
    target_url = models.URLField(blank=True, null=True, verbose_name='رابط التحويل (اختياري)')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=7, help_text="Duration in days")
    
    # Offer Details
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Discounted price (optional)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')  # Step 8-أ: Start as draft
    
    # Payment Proof
    receipt_image = models.ImageField(upload_to='ads/receipts/', blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    admin_notes = models.TextField(blank=True, help_text="Reason for rejection or reupload request")
    
    # Analytics
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        place_name = self.place.name if self.place else "No Place"
        return f"Ad for {place_name} ({self.get_status_display()})"
    
    def clean(self):
        """Validate that there's no duplicate pending/active ad for the same place."""
        from django.core.exceptions import ValidationError
        
        if self.place and self.status in ['pending', 'active']:
            duplicate = Advertisement.objects.filter(
                place=self.place,
                status=self.status
            ).exclude(pk=self.pk)
            
            if duplicate.exists():
                status_display = "معلق" if self.status == 'pending' else "نشط"
                raise ValidationError(
                    f"يوجد إعلان {status_display} لهذا المكان بالفعل."
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "إعلان"
        verbose_name_plural = "الإعلانات"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['placement']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            # Composite index for core ad slot queries
            models.Index(fields=['status', 'placement', 'start_date', 'end_date']),
        ]


class InvestmentOpportunity(TimeStampedModel):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments_created')
    title = models.CharField(max_length=200)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pdf_file = models.FileField(upload_to='investments/pdfs/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default='Open')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Invoice(TimeStampedModel):
    """نموذج الفاتورة للإعلانات والخدمات"""
    advertisement = models.ForeignKey(Advertisement, on_delete=models.SET_NULL, null=True, related_name='invoices')
    partner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='رقم الفاتورة')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المبلغ')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='الضريبة')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الإجمالي')
    
    issue_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الإصدار')
    is_paid = models.BooleanField(default=False, verbose_name='مدفوعة')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الدفع')
    
    note = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-issue_date']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.partner}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            import uuid
            self.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
