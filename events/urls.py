from django.urls import path
from .views import (
    EventListView, EventDetailView, 
    EventCreateView, EventUpdateView, EventDeleteView
)

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='list'),
    path('create/', EventCreateView.as_view(), name='create'),
    path('<int:pk>/', EventDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', EventUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', EventDeleteView.as_view(), name='delete'),
]
