"""
Email Service for User Verification
خدمة البريد الإلكتروني للتحقق من المستخدمين
"""
import secrets
import logging
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.conf import settings
from django.utils import timezone


def generate_verification_token():
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


def send_verification_email(user, request):
    """
    Send verification email to user.
    
    Args:
        user: User instance
        request: HTTP request object (to build absolute URL)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Generate token
    token = generate_verification_token()
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
    
    # Build verification URL
    verification_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'token': token})
    )
    
    # Email content
    subject = 'تأكيد بريدك الإلكتروني - دليل إب السياحي'
    
    html_message = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">مرحباً {user.full_name or user.username}!</h2>
        
        <p>شكراً لتسجيلك في دليل إب السياحي.</p>
        
        <p>لإكمال عملية التسجيل، يرجى تأكيد بريدك الإلكتروني بالضغط على الزر أدناه:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" 
               style="background-color: #3498db; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; font-size: 16px;">
                تأكيد البريد الإلكتروني
            </a>
        </div>
        
        <p>أو انسخ الرابط التالي وافتحه في متصفحك:</p>
        <p style="word-break: break-all; color: #7f8c8d;">{verification_url}</p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #95a5a6; font-size: 12px;">
            إذا لم تقم بإنشاء حساب في دليل إب السياحي، يمكنك تجاهل هذه الرسالة.
        </p>
        
        <p style="color: #95a5a6; font-size: 12px;">
            دليل إب السياحي - اكتشف جمال محافظة إب
        </p>
    </div>
    """
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}", exc_info=True)
        return False


def resend_verification_email(user, request):
    """
    Resend verification email (with rate limiting check).
    
    Rate Limits:
    - 1 email per 2 minutes (short-term)
    - 5 emails per 24 hours (daily limit)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    from django.core.cache import cache
    
    # Daily rate limit key
    daily_key = f"resend_verification_daily_{user.pk}"
    daily_count = cache.get(daily_key, 0)
    
    # Check daily limit (5 emails per 24 hours)
    DAILY_LIMIT = 5
    if daily_count >= DAILY_LIMIT:
        return False, f"لقد تجاوزت الحد اليومي ({DAILY_LIMIT} رسائل). حاول غداً."
    
    # Check short-term rate limit (1 email per 2 minutes)
    if user.email_verification_sent_at:
        time_since_last = timezone.now() - user.email_verification_sent_at
        if time_since_last.total_seconds() < 120:  # 2 minutes
            remaining = 120 - int(time_since_last.total_seconds())
            return False, f"يرجى الانتظار {remaining} ثانية قبل إعادة الإرسال"
    
    success = send_verification_email(user, request)
    if success:
        # Increment daily counter (expires in 24 hours)
        cache.set(daily_key, daily_count + 1, 86400)  # 86400 = 24 hours
        return True, "تم إرسال رسالة التحقق بنجاح"
    else:
        return False, "حدث خطأ أثناء إرسال الرسالة. حاول مرة أخرى."

