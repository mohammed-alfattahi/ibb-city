"""
Management app URL patterns.
"""
from django.urls import path

from .views_approvals import (
    UnifiedApprovalsView,
    ApprovePartnerView,
    RejectPartnerView,
    RequestInfoPartnerView,
    ApproveEstablishmentView,
    RejectEstablishmentView,
    ApprovePendingChangeView,
    RejectPendingChangeView,
    ApprovalStatsAPIView,
)

from .views_api import PartnerAnalyticsAPI

app_name = 'management'

urlpatterns = [
    # Unified Approvals Dashboard
    path('office/approvals/', UnifiedApprovalsView.as_view(), name='unified_approvals'),
    
    # Partner Approval Actions
    path('office/partner/<int:pk>/approve/', ApprovePartnerView.as_view(), name='approve_partner'),
    path('office/partner/<int:pk>/reject/', RejectPartnerView.as_view(), name='reject_partner'),
    path('office/partner/<int:pk>/request-info/', RequestInfoPartnerView.as_view(), name='request_info_partner'),
    
    # Establishment Approval Actions
    path('office/establishment/<int:pk>/approve/', ApproveEstablishmentView.as_view(), name='approve_establishment'),
    path('office/establishment/<int:pk>/reject/', RejectEstablishmentView.as_view(), name='reject_establishment'),
    
    # PendingChange Approval Actions
    path('office/change/<int:pk>/approve/', ApprovePendingChangeView.as_view(), name='approve_change'),
    path('office/change/<int:pk>/reject/', RejectPendingChangeView.as_view(), name='reject_change'),
    
    # API
    path('api/approvals/stats/', ApprovalStatsAPIView.as_view(), name='approval_stats_api'),
    path('api/analytics/partner/', PartnerAnalyticsAPI.as_view(), name='partner_analytics_api'),
]
