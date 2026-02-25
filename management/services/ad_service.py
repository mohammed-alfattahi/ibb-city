from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from management.models import Advertisement, Invoice


class AdService:
    """
    Domain Service for Advertisement Lifecycle & Financials.
    Handles: Draft -> Invoice -> Payment -> Review -> Active -> Expired.
    """

    # Read from settings with fallback
    COST_PER_DAY = getattr(settings, 'AD_COST_PER_DAY', 1000)

    @staticmethod
    @transaction.atomic
    def create_ad_draft(
        user,
        place,
        title,
        description,
        banner_image,
        duration_days,
        placement=None,
        target_url=None,
        start_date=None,
        price=None,
        discount_price=None,
    ):
        """
        Create an Ad Draft and generating a corresponding Unpaid Invoice.
        """
        # 1. Validation
        if duration_days < 1:
            raise ValidationError("Duration must be at least 1 day.")

        # 2. Create Ad Ticket
        ad = Advertisement.objects.create(
            owner=user,
            place=place,
            title=title,
            description=description,
            banner_image=banner_image,
            placement=placement or 'banner',
            target_url=target_url,
            duration_days=duration_days,
            start_date=start_date or timezone.now().date(),
            price=price,
            discount_price=discount_price,
            status='draft'
        )

        # 3. Calculate Cost
        total_cost = AdService._calculate_cost(duration_days)

        # 4. Generate Invoice
        place_name = place.name if place else "General"
        Invoice.objects.create(
            advertisement=ad,
            partner=user,
            amount=total_cost,
            total_amount=total_cost,
            note=f"Ad campaign for {place_name} ({duration_days} days)",
            is_paid=False
        )

        return ad

    @staticmethod
    def submit_payment(ad, receipt_image, transaction_ref=""):
        """
        Partner submits payment proof for an invoice.
        """
        # 1. Validation
        if ad.status not in ['draft', 'payment_issue']:
            raise ValidationError("Cannot submit payment for this ad status.")

        # 2. Update Ad with Proof
        ad.receipt_image = receipt_image
        ad.transaction_reference = transaction_ref
        ad.status = 'pending'  # Pending Admin Review
        ad.save()

        return True

    @staticmethod
    @transaction.atomic
    def process_approval(ad, admin_user, approved=True, rejection_reason=""):
        """
        Admin reviews the payment and content.
        """
        if approved:
            # 1. Activate Ad
            ad.status = 'active'
            today = timezone.now().date()
            if not ad.start_date or ad.start_date < today:
                ad.start_date = today
            ad.end_date = ad.start_date + timedelta(days=ad.duration_days)
            ad.admin_notes = "Approved by admin."
            ad.save()

            # 2. Mark Invoice as Paid
            invoice = ad.invoices.last()
            if invoice:
                invoice.is_paid = True
                invoice.payment_date = timezone.now()
                invoice.save()
            
            # 3. Notify Partner
            from interactions.notifications.notification_service import NotificationService
            NotificationService.notify(
                event='AD_APPROVED',
                user=ad.owner,
                metadata={'ad_id': ad.pk, 'ad_title': ad.title}
            )

        else:
            # Reject
            ad.status = 'rejected'
            ad.admin_notes = rejection_reason
            ad.save()
            
            # Notify Partner
            from interactions.notifications.notification_service import NotificationService
            NotificationService.notify(
                event='AD_REJECTED',
                user=ad.owner,
                metadata={'ad_id': ad.pk, 'reason': rejection_reason}
            )

        return ad

    @staticmethod
    def pause_ad(ad, user=None):
        """
        Pause an active advertisement.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if ad.status != 'active':
            return False, "يمكن إيقاف الإعلانات النشطة فقط."
        
        # Calculate remaining days
        today = timezone.now().date()
        if ad.end_date:
            remaining_days = (ad.end_date - today).days
            ad.duration_days = max(remaining_days, 0)  # Store remaining days
        
        ad.status = 'paused'
        ad.admin_notes = f"Paused by {'admin' if user and user.is_staff else 'partner'} on {today}"
        ad.save()
        
        return True, "تم إيقاف الإعلان مؤقتاً بنجاح."

    @staticmethod
    def resume_ad(ad, user=None):
        """
        Resume a paused advertisement.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if ad.status != 'paused':
            return False, "يمكن استئناف الإعلانات المتوقفة فقط."
        
        # Recalculate end date from remaining days
        today = timezone.now().date()
        ad.start_date = today
        ad.end_date = today + timedelta(days=ad.duration_days)
        ad.status = 'active'
        ad.admin_notes = f"Resumed on {today}"
        ad.save()
        
        return True, "تم استئناف الإعلان بنجاح."

    @staticmethod
    def extend_ad(ad, extra_days, user=None):
        """
        Extend an active or paused advertisement.
        
        Returns:
            tuple: (success: bool, message: str, cost: Decimal)
        """
        if ad.status not in ['active', 'paused']:
            return False, "يمكن تمديد الإعلانات النشطة أو المتوقفة فقط.", 0
        
        if extra_days < 1:
            return False, "يجب أن تكون فترة التمديد يوم واحد على الأقل.", 0
        
        # Calculate extension cost
        extension_cost = AdService._calculate_cost(extra_days)
        
        # Update duration
        ad.duration_days += extra_days
        if ad.end_date:
            ad.end_date += timedelta(days=extra_days)
        ad.save()
        
        # Create extension invoice
        Invoice.objects.create(
            advertisement=ad,
            partner=ad.owner,
            amount=extension_cost,
            total_amount=extension_cost,
            note=f"Extension: {extra_days} days for {ad.title}",
            is_paid=False
        )
        
        return True, f"تم تمديد الإعلان {extra_days} أيام. الرجاء سداد رسوم التمديد.", extension_cost

    @staticmethod
    def check_expirations():
        """
        Background task to expire ads.
        Should be called by Celery Beat daily.
        
        Returns:
            int: Number of expired ads
        """
        today = timezone.now().date()
        expired_ads = Advertisement.objects.filter(
            status='active',
            end_date__lt=today
        )
        
        count = 0
        for ad in expired_ads:
            ad.status = 'expired'
            ad.save()
            count += 1
            
            # Notify Partner
            try:
                from interactions.notifications.notification_service import NotificationService
                NotificationService.notify(
                    event='AD_EXPIRED',
                    user=ad.owner,
                    metadata={'ad_id': ad.pk, 'ad_title': ad.title}
                )
            except Exception:
                pass  # Don't break loop for notification errors
        
        return count

    @staticmethod
    def expire_ads():
        """Backward-compatible alias for expire command."""
        return AdService.check_expirations()

    @staticmethod
    def get_partner_stats(user):
        """
        Get advertisement statistics for a partner.
        
        Returns:
            dict: Statistics including counts and totals
        """
        ads = Advertisement.objects.filter(owner=user)
        
        return {
            'total_ads': ads.count(),
            'active_ads': ads.filter(status='active').count(),
            'pending_ads': ads.filter(status='pending').count(),
            'expired_ads': ads.filter(status='expired').count(),
            'total_views': sum(ad.views for ad in ads),
            'total_clicks': sum(ad.clicks for ad in ads),
            'total_spent': sum(
                inv.total_amount for inv in Invoice.objects.filter(
                    partner=user, is_paid=True
                )
            ),
        }

    @staticmethod
    def _calculate_cost(days):
        cost_per_day = getattr(settings, 'AD_COST_PER_DAY', AdService.COST_PER_DAY)
        return days * cost_per_day
