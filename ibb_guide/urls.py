from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    RegisterView, UserProfileView, VisitorSignUpView, UnifiedLoginView,
    VerificationSentView, EmailVerificationView, ResendVerificationView, SettingsView
)
from places.views import PlaceViewSet
from interactions.views import ReviewViewSet, FavoriteViewSet, ReportViewSet


from places.views_partner import (
    PartnerDashboardView, 
    PartnerEstablishmentDetailView,
    PartnerEstablishmentListView, 
    PartnerEstablishmentCreateView, 
    PartnerEstablishmentUpdateView,
    EstablishmentUnitListView,
    EstablishmentUnitCreateView,
    EstablishmentUnitUpdateView,
    EstablishmentUnitDeleteView,
    PartnerGalleryView,
    PartnerMediaDeleteView,
    toggle_establishment_status,
    toggle_comment_visibility as partner_toggle_comment_visibility,  # Fix: alias to avoid collision
    PartnerOfferListView, PartnerOfferCreateView, PartnerOfferUpdateView, PartnerOfferDeleteView
)
from interactions.views_partner import PartnerReviewListView, PartnerReviewReplyCreateView
from users.views_partner import PartnerProfileUpdateView, PartnerSignUpView, PartnerPendingView, TouristToPartnerUpgradeView, PartnerRequestListView, PartnerRequestDetailView, PartnerAuditLogListView
from django.contrib.auth.views import LogoutView
from management.views_partner import PartnerAdsListView, AdvertisementCreateView, AdPaymentView, AdvertisementUpdateView
from management.views_public import InvestmentListView, InvestmentDetailView, OfferListView, OfferDetailView, WeatherAlertPublicView, AdSlotView
from users.views_api import (
    SaveFCMTokenView, SendVerificationEmailAPIView, 
    VerifyEmailAPIView, ResendVerificationAPIView
)
from management import views_admin, views_ads
from management.admin_utils import toggle_boolean_field
from management import views as management_views
from places.views_public import (
    HomeView, PlaceDetailView, PlaceListView, CategoryPlaceListView, MapDataView, NearbyPlacesView, 
    NatureListView, LandmarksListView, PlaceWeatherView,
    RestaurantListView, HotelListView, ParkListView,
    GlobalPlaceSearchView, SmartSearchView, WeatherPageView
)
from places import views_partner_contacts
from management.views_content import EmergencyPageView, CulturePageView
from interactions.views_public import (
    review_create, review_delete, report_place, add_reply,
    NotificationListView, mark_notification_read, mark_all_notifications_read, delete_notification, delete_all_notifications,
    toggle_favorite, FavoriteListView, toggle_comment_visibility, toggle_follow,
    add_place_comment, reply_to_comment, unread_count, bulk_delete_favorites, notifications_snapshot
)
from interactions.views_preferences import (
    get_preferences as notification_get_preferences,
    update_preferences as notification_update_preferences
)
from interactions.views_liveshare import (
    StartShareView, StopShareView, PingView, 
    ControlPanelView, PublicShareView, LatestLocationAPI
)
from interactions import views_itinerary

# ... (router code)

router = DefaultRouter()
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    # ..
    # Public
    path('', HomeView.as_view(), name='home'),
    path('pages/safety/', TemplateView.as_view(template_name='pages/safety_guide.html'), name='safety_guide'),
    path('pages/gallery/', TemplateView.as_view(template_name='pages/gallery.html'), name='gallery'),
    path('places/', PlaceListView.as_view(), name='place_list'),
    path('places/category/<int:pk>/', CategoryPlaceListView.as_view(), name='category_place_list'), # New Category Path
    path('places/nature/', NatureListView.as_view(), name='places_nature_list'),
    path('places/landmarks/', LandmarksListView.as_view(), name='places_landmarks_list'),
    # Specialized Views
    path('places/search/', SmartSearchView.as_view(), name='places_search'),
    path('places/restaurants/', RestaurantListView.as_view(), name='places_restaurants_list'),
    path('places/hotels/', HotelListView.as_view(), name='places_hotels_list'),
    path('places/parks/', ParkListView.as_view(), name='places_parks_list'),
    
    path('nature/', NatureListView.as_view(), name='nature_list'),
    path('place/<int:pk>/', PlaceDetailView.as_view(), name='place_detail'),
    path('place/<int:place_pk>/review/create/', review_create, name='review_create'),
    path('place/<int:place_pk>/review/<int:review_pk>/delete/', review_delete, name='review_delete'),
    path('review/<int:review_pk>/reply/', add_reply, name='add_reply'),
    path('place/<int:place_pk>/comment/', add_place_comment, name='add_place_comment'), # New
    path('comment/<int:comment_pk>/reply/', reply_to_comment, name='reply_to_comment'), # New
    path('places/<int:place_pk>/favorite-toggle/', toggle_favorite, name='favorite_toggle'),
    path('favorites/bulk-delete/', bulk_delete_favorites, name='bulk_delete_favorites'),
    path('place/<int:place_pk>/follow/', toggle_follow, name='toggle_follow'),
    path('favorites/', FavoriteListView.as_view(), name='favorite_list'),
    path('ads/slot/<str:placement>/', AdSlotView.as_view(), name='ad_slot'),
    path('place/<int:place_pk>/report/', report_place, name='report_place'),
    path('comment/toggle-visibility/<int:pk>/<str:model_type>/', toggle_comment_visibility, name='toggle_comment_visibility'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('settings/', SettingsView.as_view(), name='user_settings'),

    # partner
    path('partner/', PartnerDashboardView.as_view(), name='partner_dashboard'),
    path('partner/my-places/', PartnerEstablishmentListView.as_view(), name='partner_establishment_list'),
    path('partner/place/new/', PartnerEstablishmentCreateView.as_view(), name='establishment_create'),
    path('partner/place/<int:pk>/', PartnerEstablishmentDetailView.as_view(), name='partner_place_dashboard'),
    path('partner/place/<int:pk>/edit/', PartnerEstablishmentUpdateView.as_view(), name='establishment_update'),
    
    # Establishment Units (Rooms/Meals)
    path('partner/place/<int:place_pk>/units/', EstablishmentUnitListView.as_view(), name='partner_unit_list'),
    path('partner/place/<int:place_pk>/units/add/', EstablishmentUnitCreateView.as_view(), name='partner_unit_create'),
    path('partner/unit/<int:pk>/edit/', EstablishmentUnitUpdateView.as_view(), name='partner_unit_update'),
    path('partner/unit/<int:pk>/delete/', EstablishmentUnitDeleteView.as_view(), name='partner_unit_delete'),

    # Partner Reviews
    path('partner/reviews/', PartnerReviewListView.as_view(), name='partner_review_list'),
    path('partner/review/<int:review_pk>/reply/', PartnerReviewReplyCreateView.as_view(), name='partner_review_reply'),

    # Partner Profile
    path('partner/profile/', PartnerProfileUpdateView.as_view(), name='partner_profile'),

    # Gallery
    path('partner/place/<int:place_pk>/gallery/', PartnerGalleryView.as_view(), name='partner_gallery'),
    path('partner/media/<int:pk>/delete/', PartnerMediaDeleteView.as_view(), name='partner_media_delete'),
    
    # Partner Offers
    path('partner/places/<int:place_pk>/offers/', PartnerOfferListView.as_view(), name='partner_offer_list'),
    path('partner/places/<int:place_pk>/offers/add/', PartnerOfferCreateView.as_view(), name='partner_offer_create'),
    path('partner/offers/<int:pk>/edit/', PartnerOfferUpdateView.as_view(), name='partner_offer_edit'),
    path('partner/offers/<int:pk>/delete/', PartnerOfferDeleteView.as_view(), name='partner_offer_delete'),
    
    # Partner Actions
    path('partner/place/<int:pk>/toggle-status/', toggle_establishment_status, name='toggle_establishment_status'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/<int:pk>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/delete/<int:pk>/', delete_notification, name='delete_notification'),
    path('notifications/delete-all/', delete_all_notifications, name='delete_all_notifications'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/api/unread-count/', unread_count, name='unread_count'),
    path('notifications/api/snapshot/', notifications_snapshot, name='notifications_snapshot'),
    path('notifications/api/preferences/', notification_get_preferences, name='notification_get_preferences'),
    path('notifications/api/preferences/update/', notification_update_preferences, name='notification_update_preferences'),
    
    # Partner Auth
    path('partner/register/', PartnerSignUpView.as_view(), name='partner_signup'),
    path('partner/pending/', PartnerPendingView.as_view(), name='partner_pending'),
    path('partner/upgrade/', TouristToPartnerUpgradeView.as_view(), name='partner_upgrade'),

    # Ads
    path('partner/ads/', PartnerAdsListView.as_view(), name='partner_ads'),
    path('partner/ads/create/', AdvertisementCreateView.as_view(), name='ad_create'),
    path('partner/ads/<int:pk>/edit/', AdvertisementUpdateView.as_view(), name='ad_update'),
    path('partner/ads/<int:pk>/pay/', AdPaymentView.as_view(), name='ad_payment'),
    
    # Partner Requests
    path('partner/requests/', PartnerRequestListView.as_view(), name='partner_request_list'),
    path('partner/requests/<int:pk>/', PartnerRequestDetailView.as_view(), name='partner_request_detail'),
    
    # Partner Comment Controls
    path('partner/comment/toggle-visibility/<int:pk>/<str:model_type>/', partner_toggle_comment_visibility, name='partner_toggle_comment_visibility'),
    
    # Partner Audit Log
    path('partner/logs/', PartnerAuditLogListView.as_view(), name='partner_audit_log'),
    
    # Partner Contact Management
    path('partner/establishments/<int:pk>/contacts/', 
         views_partner_contacts.ContactListView.as_view(), name='partner_contact_list'),
    path('partner/establishments/<int:pk>/contacts/add/', 
         views_partner_contacts.ContactCreateView.as_view(), name='partner_contact_create'),
    path('partner/establishments/<int:pk>/contacts/<uuid:contact_id>/edit/', 
         views_partner_contacts.ContactUpdateView.as_view(), name='partner_contact_update'),
    path('partner/establishments/<int:pk>/contacts/<uuid:contact_id>/delete/', 
         views_partner_contacts.ContactDeleteView.as_view(), name='partner_contact_delete'),
    path('partner/establishments/<int:pk>/contacts/<uuid:contact_id>/toggle/', 
         views_partner_contacts.ContactToggleVisibilityView.as_view(), name='partner_contact_toggle'),
    path('partner/establishments/<int:pk>/contacts/reorder/', 
         views_partner_contacts.ContactReorderView.as_view(), name='partner_contact_reorder'),

    # Itineraries (Trips)
    path('itineraries/', views_itinerary.ItineraryListView.as_view(), name='itinerary_list'),
    path('itineraries/new/', views_itinerary.ItineraryCreateView.as_view(), name='itinerary_create'),
    path('itineraries/search/', views_itinerary.ItineraryPlaceSearchView.as_view(), name='itinerary_search_place'),
    path('itineraries/<int:pk>/', views_itinerary.ItineraryDetailView.as_view(), name='itinerary_detail'),
    path('itineraries/<int:pk>/delete/', views_itinerary.ItineraryDeleteView.as_view(), name='itinerary_delete'),
    path('itineraries/<int:pk>/toggle-public/', views_itinerary.ItineraryTogglePublicView.as_view(), name='itinerary_toggle_public'),
    path('itineraries/public/<int:pk>/', views_itinerary.PublicItineraryView.as_view(), name='itinerary_public'),
    path('itineraries/item/<int:pk>/delete/', views_itinerary.ItineraryItemDeleteView.as_view(), name='itinerary_item_delete'),
    path('itineraries/item/<int:pk>/add/<int:place_pk>/', views_itinerary.ItineraryAddItemView.as_view(), name='itinerary_add_item'),
    path('itineraries/reorder/', views_itinerary.ItineraryReorderItemsView.as_view(), name='itinerary_reorder_items'),
    


    # Ad Tracking (Public)
    # Ad Tracking (Public)
    # Ad Tracking (Public)
    path('ad/<int:pk>/click/', views_ads.AdClickView.as_view(), name='ad_click'),
    path('api/ad/<int:pk>/view/', views_ads.AdImpressionView.as_view(), name='ad_impression'),

    
    # Investments
    path('investments/', InvestmentListView.as_view(), name='investment_list'),
    path('investments/<int:pk>/', InvestmentDetailView.as_view(), name='investment_detail'),
    
    # Tourism Offers
    path('offers/', OfferListView.as_view(), name='offer_list'),
    path('offers/<int:pk>/', OfferDetailView.as_view(), name='offer_detail'),
    
    # Events & Seasons
    path('events/', include('events.urls', namespace='events')),

    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),

    # Unified Auth (All Users)
    path('login/', UnifiedLoginView.as_view(), name='login'),
    path('partner/login/', RedirectView.as_view(url='/login/', permanent=True)),  # Redirect old partner login
    path('logout/', LogoutView.as_view(), name='logout'),
    path('partner/logout/', RedirectView.as_view(url='/logout/', permanent=True), name='partner_logout'), # Redirect old partner logout
    
    # Redirects for standard Django/Allauth paths to Unified paths
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),
    path('accounts/signup/', RedirectView.as_view(url='/join/', permanent=True)),
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),  # Social Auth (Google, etc.)
    path('communities/', include('communities.urls', namespace='communities')),
    path('join/', TemplateView.as_view(template_name='registration/signup.html'), name='signup_selection'),
    path('join/tourist/', VisitorSignUpView.as_view(), name='visitor_signup'),
    
    # Email Verification
    path('verification-sent/', VerificationSentView.as_view(), name='verification_sent'),
    path('verify-email/<str:token>/', EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),

    # Surveys
    path('surveys/', include('surveys.urls')),

    # Guidebook & Static Pages
    path('emergency/', EmergencyPageView.as_view(), name='emergency'),
    path('transport/', TemplateView.as_view(template_name='pages/transport.html'), name='transport'),
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('info/entry-visa/', TemplateView.as_view(template_name='pages/entry_visa.html'), name='entry_visa'),
    
    # Map
    path('explore-map/', TemplateView.as_view(template_name='places/map_explore.html'), name='map_explore'),
    path('map/data/', MapDataView.as_view(), name='map_data'),
    path('api/nearby/', NearbyPlacesView.as_view(), name='nearby_places'),
    path('places/weather/', PlaceWeatherView.as_view(), name='place_weather_api'), # Renamed for clarity API
    path('weather/', WeatherPageView.as_view(), name='weather_page'), # New User Page
    
    # Tourist Guides (Req 18)
    path('guides/', TemplateView.as_view(template_name='pages/guides.html'), name='guides_hub'),
    path('guides/markets/', TemplateView.as_view(template_name='pages/markets.html'), name='guide_markets'),
    path('guides/culture/', CulturePageView.as_view(), name='guide_culture'),
    path('guides/food/', TemplateView.as_view(template_name='pages/food.html'), name='guide_food'),
    
    # Firebase Service Worker (Served at Root - No Redirect for Service Workers)
    path('firebase-messaging-sw.js', TemplateView.as_view(
        template_name='firebase-messaging-sw.js', 
        content_type='application/javascript'
    ), name='firebase_sw'),

    # PWA
    path('serviceworker.js', TemplateView.as_view(
        template_name='serviceworker.js', 
        content_type='application/javascript'
    ), name='serviceworker'),
    path('manifest.json', TemplateView.as_view(
        template_name='manifest.json', 
        content_type='application/json'
    ), name='manifest'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),

    # Custom Admin
    path('custom-admin/', views_admin.AdminDashboardView.as_view(), name='custom_admin_dashboard'),
    path('places/api/search/', GlobalPlaceSearchView.as_view(), name='global_search'),
    path('custom-admin/search/', views_admin.AdminGlobalSearchView.as_view(), name='admin_global_search'),
    path('custom-admin/partners/', views_admin.PendingPartnersListView.as_view(), name='admin_pending_partners'),
    path('custom-admin/alerts/create/', views_admin.CreateSystemAlertView.as_view(), name='admin_create_alert'),
    path('custom-admin/partner/<int:pk>/approve/', views_admin.ApprovePartnerView.as_view(), name='admin_partner_approve'),
    path('custom-admin/partner/<int:pk>/reject/', views_admin.RejectPartnerView.as_view(), name='admin_partner_reject'),
    path('custom-admin/partner/<int:pk>/needs-info/', views_admin.PartnerNeedsInfoView.as_view(), name='admin_partner_needs_info'),
    path('custom-admin/export/<str:model_type>/', views_admin.AdminExportView.as_view(), name='admin_export'),
    
    # Generic Request Management (Updates etc)
    path('custom-admin/requests/', views_admin.AdminRequestListView.as_view(), name='admin_request_list'),
    path('custom-admin/requests/<int:pk>/', views_admin.AdminRequestDetailView.as_view(), name='admin_request_detail'),
    path('custom-admin/requests/<int:pk>/action/', views_admin.AdminRequestActionView.as_view(), name='admin_request_action'),
    
    # Weather Alerts (Admin)
    path('custom-admin/weather/', views_admin.WeatherAlertListView.as_view(), name='admin_weather_alerts'),
    path('custom-admin/weather/create/', views_admin.WeatherAlertCreateView.as_view(), name='admin_weather_alert_create'),
    path('custom-admin/weather/<int:pk>/delete/', views_admin.AdminWeatherDeleteView.as_view(), name='admin_weather_alert_delete'),
    
    # Favorites Management
    path('custom-admin/favorites/', views_admin.AdminFavoriteListView.as_view(), name='admin_favorite_list'),
    path('custom-admin/favorites/bulk-delete/', views_admin.AdminBulkDeleteFavoritesView.as_view(), name='admin_bulk_delete_favorites'),
    
    # Ad Management (Admin)
    path('custom-admin/ads/', views_admin.AdRequestListView.as_view(), name='admin_ad_list'),
    path('custom-admin/ads/<int:pk>/approve/', views_admin.ApproveAdView.as_view(), name='admin_ad_approve'),
    path('custom-admin/ads/<int:pk>/reject/', views_admin.RejectAdView.as_view(), name='admin_ad_reject'),
    path('custom-admin/ads/<int:pk>/pause/', views_admin.PauseAdView.as_view(), name='admin_ad_pause'),
    path('custom-admin/ads/<int:pk>/resume/', views_admin.ResumeAdView.as_view(), name='admin_ad_resume'),
    
    # Establishment Management (Suspension)
    path('custom-admin/establishments/', views_admin.AdminEstablishmentListView.as_view(), name='admin_establishment_list'),
    path('custom-admin/establishments/bulk/', views_admin.AdminEstablishmentBulkActionView.as_view(), name='admin_establishment_bulk'),
    path('custom-admin/establishments/<int:pk>/suspend/', views_admin.SuspendEstablishmentView.as_view(), name='admin_establishment_suspend'),

    # Reports Management
    path('custom-admin/reports/', views_admin.AdminReportsListView.as_view(), name='admin_reports_list'),
    path('custom-admin/reports/<int:pk>/action/', views_admin.AdminReportActionView.as_view(), name='admin_report_action'),
    
    # Users Management
    path('custom-admin/users/', views_admin.AdminUsersListView.as_view(), name='admin_users_list'),
    path('custom-admin/users/<int:pk>/toggle/', views_admin.AdminUserToggleActiveView.as_view(), name='admin_user_toggle'),

    # Events Management
    path('custom-admin/events/', views_admin.AdminEventListView.as_view(), name='admin_event_list'),
    path('custom-admin/events/create/', views_admin.AdminEventCreateView.as_view(), name='admin_event_create'),
    path('custom-admin/events/<int:pk>/edit/', views_admin.AdminEventUpdateView.as_view(), name='admin_event_update'),
    path('custom-admin/events/<int:pk>/delete/', views_admin.AdminEventDeleteView.as_view(), name='admin_event_delete'),


    # System Health
    path('custom-admin/system-health/', views_admin.SystemHealthView.as_view(), name='admin_system_health'),
    
    # Pending Changes (Field-Level Approval)
    path('custom-admin/pending-changes/', views_admin.PendingChangeListView.as_view(), name='admin_pending_changes'),
    path('custom-admin/pending-changes/<uuid:pk>/', views_admin.PendingChangeDetailView.as_view(), name='admin_pending_change_detail'),
    path('custom-admin/pending-changes/<uuid:pk>/action/', views_admin.PendingChangeActionView.as_view(), name='admin_pending_change_action'),

    # System Settings
    path('custom-admin/settings/', views_admin.AdminSettingsView.as_view(), name='admin_settings'),

    # Establishment Approval Workflow
    path('custom-admin/establishments/pending/', views_admin.EstablishmentApprovalListView.as_view(), name='admin_establishment_approval'),
    path('custom-admin/establishments/<int:pk>/approve/', views_admin.EstablishmentApproveView.as_view(), name='admin_establishment_approve'),
    path('custom-admin/establishments/<int:pk>/reject/', views_admin.EstablishmentRejectView.as_view(), name='admin_establishment_reject'),

    # Partner Approval Workflow
    path('custom-admin/partners/pending/', views_admin.PartnerApprovalListView.as_view(), name='admin_partner_approval'),
    # Note: approve/reject routes are defined in singular 'partner' path above (L265-267)

    # Tourism Office - Landmark Management
    path('custom-admin/tourism/landmarks/', views_admin.TourismOfficeLandmarkListView.as_view(), name='tourism_landmark_list'),
    path('custom-admin/tourism/landmarks/<int:pk>/', views_admin.TourismOfficeLandmarkDetailView.as_view(), name='tourism_landmark_detail'),
    path('custom-admin/tourism/landmarks/<int:pk>/verify/', views_admin.TourismOfficeVerifyLandmarkView.as_view(), name='tourism_landmark_verify'),
    path('custom-admin/tourism/landmarks/<int:pk>/edit/', views_admin.TourismOfficeLandmarkEditView.as_view(), name='tourism_landmark_edit'),

    # Weather Alerts (Public)
    path('weather-alerts/', WeatherAlertPublicView.as_view(), name='weather_alerts'),

    # Django Admin
    path('admin/toggle_boolean_field/', toggle_boolean_field, name='admin_toggle_boolean_field'),
    path('admin/', admin.site.urls),

    # API Routes
    path('api/', include(router.urls)),
    
    # JWT API Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    
    # FCM Token Save
    path('api/save-fcm-token/', SaveFCMTokenView.as_view(), name='save_fcm_token'),
    
    # Email Verification API
    path('api/send-verification-email/', SendVerificationEmailAPIView.as_view(), name='api_send_verification'),
    path('api/verify-email/', VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('api/resend-verification/', ResendVerificationAPIView.as_view(), name='api_resend_verification'),
    
    # Places Wizard (Drafts)
    path('', include('places.urls')),
    
    # Security (Private Documents)
    # Security (Private Documents)
    path('secure-file/<path:file_path>/', views_admin.secure_file_view, name='secure_file'),
    
    # Management (Office Approvals)
    path('', include('management.urls')),
    # Live Share (MVP)
    path('share/start/', StartShareView.as_view(), name='live_share_start'),
    path('share/stop/<str:token>/', StopShareView.as_view(), name='live_share_stop'),
    path('share/ping/', PingView.as_view(), name='live_share_ping'),
    path('tools/live-share/control/<str:token>/', ControlPanelView.as_view(), name='live_share_control'),
    path('share/<str:token>/view/', PublicShareView.as_view(), name='live_share_public'),
    path('share/<str:token>/latest/', LatestLocationAPI.as_view(), name='live_share_latest'),

    # Interactions (HTMX)
    path('interactions/', include('interactions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
