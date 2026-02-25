from django.urls import path
from .views_public import review_create, review_delete, stream_notifications

urlpatterns = [
    path('place/<int:place_pk>/review/create/', review_create, name='review_create'),
    path('place/<int:place_pk>/review/<int:review_pk>/delete/', review_delete, name='review_delete'),
    path('stream/notifications/', stream_notifications, name='stream_notifications'),
]
