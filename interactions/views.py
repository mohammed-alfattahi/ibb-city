from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Review, Favorite, Report, PlaceComment, Notification
from .serializers import (
    ReviewSerializer, FavoriteSerializer, ReportSerializer, 
    PlaceCommentSerializer, NotificationSerializer
)
from .services import (
    ReviewService, PlaceCommentService, ReportService, NotificationService
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        # Delegate to service
        instance = ReviewService.create_review(self.request.user, serializer.validated_data)
        # Set instance on serializer for response data
        serializer.instance = instance

    def perform_update(self, serializer):
        instance = ReviewService.update_review(
            self.request.user, 
            serializer.instance, 
            serializer.validated_data
        )
        serializer.instance = instance

    def perform_destroy(self, instance):
        ReviewService.delete_review(self.request.user, instance)

class PlaceCommentViewSet(viewsets.ModelViewSet):
    queryset = PlaceComment.objects.all()
    serializer_class = PlaceCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        data = serializer.validated_data
        comment, success, msg = PlaceCommentService.create_comment(
            user=self.request.user, 
            place=data['place'],
            content=data['content'],
            parent_id=data.get('parent').pk if data.get('parent') else None
        )
        if not success:
            raise serializers.ValidationError(msg)
        serializer.instance = comment

    def perform_update(self, serializer):
        comment, success, msg = PlaceCommentService.edit_comment(
            user=self.request.user, 
            comment_id=serializer.instance.pk, 
            new_content=serializer.validated_data.get('content')
        )
        if not success:
             raise serializers.ValidationError(msg)
        # Refresh instance from DB if needed, or assume modified
        serializer.instance.refresh_from_db()

    def perform_destroy(self, instance):
        PlaceCommentService.delete_comment(self.request.user, instance)

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        NotificationService.mark_as_read(notification)
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        NotificationService.mark_all_as_read(request.user)
        return Response({'status': 'all notifications marked as read'})

class ReportCreateView(viewsets.ModelViewSet):
    """
    Specialized ViewSet/View for creating reports with dynamic content types.
    Ideally this should be a GenericAPIView or just an action on ReportViewSet, 
    but keeping as ModelViewSet to match legacy name/routing.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            # Resolve Content Object
            model_type = request.data.get('model_type')
            object_id = request.data.get('object_id')
            
            # Helper aliases for frontend convenience
            MODEL_ALIASES = {
                'comment': 'placecomment',
                'placecomment': 'placecomment',
                'review': 'review',
                'place': 'place',
                'establishment': 'establishment',
                'ad': 'advertisement',
                'advertisement': 'advertisement',
            }
            
            from django.contrib.contenttypes.models import ContentType
            
            if '.' in model_type:
                app_label, model_name = model_type.split('.')
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
            else:
                # Use alias or fallback to lowercase
                cleaned_model = MODEL_ALIASES.get(model_type.lower(), model_type.lower())
                ct = ContentType.objects.get(model=cleaned_model)
            
            content_object = ct.get_object_for_this_type(pk=object_id)

            report = ReportService.create_report(
                user=request.user,
                content_object=content_object,
                report_type=request.data.get('report_type', 'OTHER'),
                description=request.data.get('description', ''),
                proof_image=request.FILES.get('proof_image')
            )
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
            
        except ContentType.DoesNotExist:
            return Response({'error': f"Model '{model_type}' not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Return specific error to help debug
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
