"""
Email Notification Provider
مزود الإشعارات عبر البريد الإلكتروني
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .base import BaseProvider, ProviderError, SendResult

logger = logging.getLogger(__name__)


class EmailProvider(BaseProvider):
    """Email notification provider."""
    
    provider_name = "email"
    
    # Email templates mapping for notification types
    TEMPLATES = {
        'partner_approved': 'notifications/email/partner_approved.html',
        'partner_rejected': 'notifications/email/partner_rejected.html',
        'establishment_approved': 'notifications/email/establishment_approved.html',
        'establishment_rejected': 'notifications/email/establishment_rejected.html',
        'new_review': 'notifications/email/new_review.html',
        'ad_approved': 'notifications/email/ad_approved.html',
        'ad_expiring_soon': 'notifications/email/ad_expiring.html',
        'general': 'notifications/email/general.html',
    }
    
    DEFAULT_TEMPLATE = 'notifications/email/general.html'
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ibbguide.com')
        self.site_name = getattr(settings, 'SITE_NAME', 'دليل إب السياحي')
    
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Email provider doesn't use device tokens.
        This method exists for interface compatibility.
        Use send_email() or send_to_user() instead.
        """
        raise ProviderError(
            "Use send_email() for email notifications",
            provider=self.provider_name,
            retriable=False
        )
    
    def send_email(
        self,
        to_email: str,
        title: str,
        body: str,
        notification_type: str = 'general',
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            title: Email subject
            body: Email body (plain text or used in template)
            notification_type: Type for template selection
            data: Additional context for template
            
        Returns:
            SendResult with success status
        """
        try:
            # Prepare template context
            context = {
                'title': title,
                'body': body,
                'site_name': self.site_name,
                'site_url': getattr(settings, 'SITE_URL', 'https://ibbguide.com'),
                **(data or {})
            }
            
            # Get template
            template_name = self.TEMPLATES.get(notification_type, self.DEFAULT_TEMPLATE)
            
            try:
                html_content = render_to_string(template_name, context)
                plain_content = strip_tags(html_content)
            except Exception as template_error:
                # Fallback to simple email if template fails
                logger.warning(f"Template {template_name} not found, using plain text: {template_error}")
                html_content = None
                plain_content = f"{title}\n\n{body}"
            
            # Send email
            if html_content:
                email = EmailMultiAlternatives(
                    subject=title,
                    body=plain_content,
                    from_email=self.from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                result = email.send(fail_silently=False)
            else:
                result = send_mail(
                    subject=title,
                    message=plain_content,
                    from_email=self.from_email,
                    recipient_list=[to_email],
                    fail_silently=False
                )
            
            if result:
                logger.info(f"Email sent to {to_email}: {title}")
                return SendResult(
                    success=True,
                    message_id=f"email_{to_email}_{title[:20]}"
                )
            else:
                raise ProviderError(
                    "Email send returned 0",
                    provider=self.provider_name,
                    retriable=True
                )
                
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Email send failed to {to_email}: {e}", exc_info=True)
            raise ProviderError(
                str(e),
                provider=self.provider_name,
                retriable=True
            )
    
    def send_to_user(
        self,
        user,
        title: str,
        body: str,
        notification_type: str = 'general',
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send email notification to a user.
        
        Args:
            user: User model instance
            title: Email subject
            body: Email body
            notification_type: Type for template selection
            data: Additional context
            
        Returns:
            SendResult
        """
        email = getattr(user, 'email', None)
        
        if not email:
            logger.warning(f"No email for user {user.pk}")
            return SendResult(
                success=False,
                error="No email address registered"
            )
        
        # Add user context
        context = {
            'user': user,
            'user_name': getattr(user, 'full_name', None) or getattr(user, 'username', 'مستخدم'),
            **(data or {})
        }
        
        return self.send_email(
            to_email=email,
            title=title,
            body=body,
            notification_type=notification_type,
            data=context,
            **kwargs
        )
    
    def send_bulk(
        self,
        recipients: list,
        title: str,
        body: str,
        notification_type: str = 'general',
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, SendResult]:
        """
        Send email to multiple recipients.
        
        Args:
            recipients: List of User objects or email strings
            title: Email subject
            body: Email body
            notification_type: Type for template selection
            data: Additional context
            
        Returns:
            Dict mapping recipient to SendResult
        """
        results = {}
        
        for recipient in recipients:
            try:
                if isinstance(recipient, str):
                    # Email string
                    result = self.send_email(recipient, title, body, notification_type, data)
                    results[recipient] = result
                else:
                    # User object
                    result = self.send_to_user(recipient, title, body, notification_type, data)
                    results[getattr(recipient, 'email', str(recipient.pk))] = result
            except Exception as e:
                logger.error(f"Bulk email failed for {recipient}: {e}")
                results[str(recipient)] = SendResult(success=False, error=str(e))
        
        return results
