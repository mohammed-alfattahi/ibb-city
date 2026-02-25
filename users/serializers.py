from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .email_service import generate_verification_token

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'profile_image')
        read_only_fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'full_name', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """
        Create user with email verification pending.
        Generates verification token and creates registration log.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            is_email_verified=False  # Require email verification
        )
        
        # Generate verification token
        user.email_verification_token = generate_verification_token()
        user.save(update_fields=['email_verification_token'])
        
        # Create registration log
        from .models import UserRegistrationLog
        request = self.context.get('request')
        UserRegistrationLog.log_registration(
            request=request,
            user=user,
            email=user.email,
            username=user.username,
            registration_type='api',  # Fix Gap 2: Use valid choice
            status='pending'  # Pending until email verified
        )
        
        # Fix Gap 3: Auto-send verification email
        from .email_service import send_verification_email
        request = self.context.get('request')
        if request:
            send_verification_email(user, request)
        
        return user
