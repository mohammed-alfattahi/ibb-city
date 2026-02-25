from django.utils import timezone
from users.models import UserRegistrationLog

class PartnerService:
    """Service for handling Partner lifecycle events."""
    
    @staticmethod
    def handle_registration(request, user):
        """
        Handle post-registration actions for a new partner.
        - Send verification email
        - Log registration
        - Notify admins/partner
        """
        from django.conf import settings
        
        # Check if verification should be skipped (Temporary)
        if getattr(settings, 'SKIP_EMAIL_VERIFICATION', False):
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            # Don't send email, proceed as verified
        else:
            # Send verification email
            from users.email_service import send_verification_email
            send_verification_email(user, request)
        
        # Log registration
        UserRegistrationLog.log_registration(
            request=request,
            user=user,
            email=user.email,
            username=user.username,
            registration_type='partner',
            status='pending'
        )
        
        # Notify staff
        from interactions.notifications.admin import AdminNotifications
        if hasattr(user, 'partner_profile'):
            AdminNotifications.notify_new_partner_registration(user.partner_profile)
            
            # Notify partner
            from interactions.notifications.partner import PartnerNotifications
            PartnerNotifications.notify_partner_request_received(user.partner_profile)
            
        return True

    @staticmethod
    def request_upgrade(user):
        """
        Handle upgrade request from Tourist to Partner.
        """
        profile = getattr(user, 'partner_profile', None)
        if not profile:
            return False, "Profile not found"
            
        profile.submitted_at = timezone.now()
        profile.rejection_reason = ''
        profile.status = 'pending'
        profile.is_approved = False
        profile.save()
        
        # Notify office users
        try:
            from interactions.notifications.admin import AdminNotifications
            AdminNotifications.notify_new_partner_registration(profile)
        except Exception:
            pass
            
        return True, "تم إرسال طلب الترقية بنجاح! سيتم مراجعته قريباً."
