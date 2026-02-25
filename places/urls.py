from django.urls import path
from .views_wizard import (
    WizardStartView,
    WizardView,
    WizardAutoSaveView,
    WizardSubmitView,
    WizardPreviewView
)
from .views_api import TrackContactClickView

urlpatterns = [
    path('partner/wizard/start/', WizardStartView.as_view(), name='wizard_start'),
    path('partner/wizard/edit/<int:pk>/', WizardStartView.as_view(), name='wizard_edit'),
    # step is a KEY (e.g. basic/location/hours/services/media/review)
    path('partner/wizard/<int:draft_id>/step/<str:step>/', WizardView.as_view(), name='wizard_step'),
    path('partner/wizard/<int:draft_id>/autosave/', WizardAutoSaveView.as_view(), name='wizard_autosave'),
    path('partner/wizard/<int:draft_id>/submit/', WizardSubmitView.as_view(), name='wizard_submit'),
    path('partner/wizard/<int:draft_id>/submit/', WizardSubmitView.as_view(), name='wizard_submit'),
    path('partner/wizard/<int:draft_id>/preview/', WizardPreviewView.as_view(), name='wizard_preview'),
    
    # API Tracking
    path('api/track-click/<int:pk>/', TrackContactClickView.as_view(), name='track_contact_click'),
]
