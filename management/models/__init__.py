"""
Management Models Package
وحدة نماذج الإدارة المقسمة

الهيكل:
- requests.py: نماذج الطلبات والموافقات
- advertisements.py: نماذج الإعلانات والفواتير
- alerts.py: نماذج التنبيهات والطوارئ
- geo.py: نماذج الموقع الجغرافي
- audit.py: نماذج التدقيق والإصدارات
- pending_changes.py: نماذج التغييرات المعلقة
- content.py: نماذج إدارة المحتوى (CMS)
"""

# Request Models
from .requests import (
    Request,
    ApprovalAssignment,
    RequestStatusLog,
    ApprovalDecision,
)

# Advertisement Models
from .advertisements import (
    Advertisement,
    InvestmentOpportunity,
    Invoice,
)

# Alert Models
from .alerts import (
    WeatherAlert,
    EmergencyAlert,
    EmergencyContact,
)

# Geo Models
from .geo import (
    VehicleProfile,
    RouteLog,
    GeoZone,
    UserLocation,
)

# Audit Models
from .audit import (
    AuditLog,
    GeneralGuideline,
    ErrorLog,
    EntityVersion,
)

# Pending Changes Models
from .pending_changes import (
    PendingChange,
)

from .moderation import BannedWord, ModerationEvent, ModerationRule, ModerationQueueItem

# Content Models
from .content import (
    CulturalLandmark,
    PublicEmergencyContact,
    SafetyGuideline,
    HeroSlide,
    TeamMember,
    TransportCompany,
    # Base Architecture
    SiteSetting,
    Menu,
    SidebarWidget,
    SidebarLink,
    SocialLink,
    HomePageSection,
    ListingConfiguration,
    PlaceDetailBlock,
    FeatureToggle,
    CommunitySetting,
    NotificationSetting,
    NotificationType,
    WizardStep,
    WizardStep,
    WizardField,
)

from .settings import SystemSetting

# Analytics
from .analytics import AdDailyStats

__all__ = [
    # Requests
    'Request',
    'ApprovalAssignment',
    'RequestStatusLog',
    'ApprovalDecision',
    # Advertisements
    'Advertisement',
    'InvestmentOpportunity',
    'Invoice',
    'AdDailyStats',
    # Alerts
    'WeatherAlert',
    'EmergencyAlert',
    'EmergencyContact',
    # Geo
    'VehicleProfile',
    'RouteLog',
    'GeoZone',
    'UserLocation',
    # Audit
    'AuditLog',
    'GeneralGuideline',
    'ErrorLog',
    'EntityVersion',
    # Pending Changes
    'PendingChange',
    # Content
    'CulturalLandmark',
    'PublicEmergencyContact',
    'SafetyGuideline',
    'HeroSlide',
    'TeamMember',
    'TransportCompany',
    # Base Architecture
    'SiteSetting',
    'Menu',
    'SidebarWidget',
    'SidebarLink',
    'SocialLink',
    'HomePageSection',
    'ListingConfiguration',
    'PlaceDetailBlock',
    'FeatureToggle',
    'CommunitySetting',
    'NotificationSetting',
    'NotificationType',
    'WizardStep',
    'WizardField',
    'WizardField',
    'SystemSetting',
    'BannedWord',
    'ModerationEvent',
    'ModerationRule',
    'ModerationQueueItem',
]
