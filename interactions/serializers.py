from rest_framework import serializers
from .models import Review, Favorite, Report, Notification

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    # reply field removed as ReviewReply is gone. 
    # If using PlaceComment as reply, it's a separate list usually.

    class Meta:
        model = Review
        fields = ('id', 'place', 'user_name', 'user_avatar', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_user_avatar(self, obj):
        request = self.context.get('request')
        if obj.user.profile_image:
             return request.build_absolute_uri(obj.user.profile_image.url)
        return None

    def validate(self, attrs):
        # Unique validation for user-place review is handled by DB constraint, 
        # but good to check here or let DB raise IntegrityError
        request = self.context.get('request')
        if request and request.method == 'POST':
             if Review.objects.filter(user=request.user, place=attrs['place']).exists():
                 raise serializers.ValidationError("You have already reviewed this place.")
        return attrs

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'place', 'created_at')
        read_only_fields = ('id', 'created_at')

class ReportSerializer(serializers.ModelSerializer):
    # content_object handled via GenericFK, but for serialization we might want details. 
    # For creation we send content_type and object_id usually not here but in view/create logic. 
    # View handles creation details.
    
    class Meta:
        model = Report
        fields = ('id', 'report_type', 'description', 'proof_image', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

from .models import PlaceComment

class PlaceCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    # Handle threaded replies if needed (e.g. recursive)
    # For simplicity, shallow serialization
    
    class Meta:
        model = PlaceComment
        fields = ('id', 'place', 'user_name', 'user_avatar', 'content', 'parent', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_user_avatar(self, obj):
        request = self.context.get('request')
        if obj.user.profile_image:
             try:
                return request.build_absolute_uri(obj.user.profile_image.url)
             except: return None
        return None

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id', 'notification_type', 'title', 'message', 
            'is_read', 'read_at', 'action_url', 'created_at'
        )
        read_only_fields = (
            'id', 'notification_type', 'title', 'message', 
            'action_url', 'created_at'
        )
