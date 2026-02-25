"""
API Views for User-related operations
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@method_decorator(csrf_exempt, name='dispatch')
class SaveFCMTokenView(APIView):
    """
    API endpoint لحفظ FCM Token للمستخدم
    يُستخدم لإرسال الإشعارات عبر Firebase Cloud Messaging
    """
    permission_classes = [IsAuthenticated] # Step 1: Require Authentication
    
    def post(self, request):
        try:
            # Parse JSON body
            if isinstance(request.data, dict):
                data = request.data
            else:
                data = json.loads(request.body)
            
            # Step 2: Use request.user (Source of Truth) instead of user_id body param
            user = request.user
            fcm_token = data.get('fcm_token')
            
            if not fcm_token:
                return Response(
                    {'error': 'fcm_token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save token
            user.fcm_token = fcm_token
            user.save(update_fields=['fcm_token'])
                
            return Response({
                'status': 'success',
                'message': 'FCM token saved successfully'
            }, status=status.HTTP_200_OK)
                
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# Email Verification API Views
# ============================================
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django_ratelimit.decorators import ratelimit
from .email_service import send_verification_email, resend_verification_email

User = get_user_model()


class SendVerificationEmailAPIView(APIView):
    """
    API endpoint to send verification email after registration.
    POST /api/send-verification-email/
    Body: { "email": "user@example.com" } or authenticated user
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'البريد الإلكتروني مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Bug fix: Handle duplicate emails gracefully
            user_qs = User.objects.filter(email=email, is_email_verified=False)
            if not user_qs.exists():
                raise User.DoesNotExist
            user = user_qs.first()
        except User.DoesNotExist:
            return Response(
                {'error': 'لم يتم العثور على حساب غير مؤكد بهذا البريد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        success = send_verification_email(user, request)
        
        if success:
            return Response({
                'status': 'success',
                'message': 'تم إرسال رسالة التحقق بنجاح'
            })
        else:
            return Response(
                {'error': 'فشل إرسال البريد، حاول مرة أخرى'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailAPIView(APIView):
    """
    API endpoint to verify email using token.
    POST /api/verify-email/
    Body: { "token": "verification_token_here" }
    """
    permission_classes = [AllowAny]
    TOKEN_EXPIRY_HOURS = 24  # Token expires after 24 hours
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'رمز التحقق مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email_verification_token=token)
        except User.DoesNotExist:
            return Response(
                {'error': 'رمز التحقق غير صالح أو منتهي الصلاحية'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token expiry (24 hours)
        if user.email_verification_sent_at:
            from datetime import timedelta
            from django.utils import timezone
            expiry_time = user.email_verification_sent_at + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
            if timezone.now() > expiry_time:
                return Response({
                    'error': 'رمز التحقق منتهي الصلاحية. يرجى طلب رابط جديد.',
                    'expired': True,
                    'email': user.email
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark email as verified
        user.is_email_verified = True
        user.email_verification_token = ''  # Clear the token
        user.save(update_fields=['is_email_verified', 'email_verification_token'])
        
        # Update registration log status
        from .models import UserRegistrationLog
        UserRegistrationLog.objects.filter(
            user=user,
            status='pending'
        ).update(status='success')
        
        return Response({
            'status': 'success',
            'message': 'تم تأكيد بريدك الإلكتروني بنجاح',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_email_verified': True
            }
        })


class ResendVerificationAPIView(APIView):
    """
    API endpoint to resend verification email.
    POST /api/resend-verification/
    Body: { "email": "user@example.com" }
    Rate limited: 1 request per 2 minutes per email.
    """
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='post:email', rate='1/2m', method='POST', block=False))
    def post(self, request):
        # Check rate limit
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            return Response(
                {'error': 'يرجى الانتظار قبل إعادة الإرسال'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'البريد الإلكتروني مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Bug fix: Handle duplicate emails gracefully
            user_qs = User.objects.filter(email=email, is_email_verified=False)
            if not user_qs.exists():
                raise User.DoesNotExist
            user = user_qs.first()
        except User.DoesNotExist:
            return Response(
                {'error': 'لم يتم العثور على حساب غير مؤكد بهذا البريد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        success, message = resend_verification_email(user, request)
        
        if success:
            return Response({
                'status': 'success',
                'message': message
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
