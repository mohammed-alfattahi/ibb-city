"""
URL patterns for security module.
"""
from django.urls import path
from .views import ServePrivateDocumentView, ServePartnerDocumentView

app_name = 'security'

urlpatterns = [
    # Generic private document serving
    path(
        'private/<path:document_path>',
        ServePrivateDocumentView.as_view(),
        name='serve_private_document'
    ),
    
    # Partner document serving (specialized)
    path(
        'partner/<int:profile_id>/document/<str:document_type>/',
        ServePartnerDocumentView.as_view(),
        name='serve_partner_document'
    ),
]
