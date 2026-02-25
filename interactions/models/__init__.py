"""
Interactions Models Package
وحدة نماذج التفاعلات المقسمة

الهيكل:
- favorites.py: المفضلة وجدول الرحلات (Favorite, Itinerary, ItineraryItem)
- reviews.py: التقييمات والتعليقات (Review, ReviewReply, PlaceComment)
- reports.py: البلاغات (Report)
- notifications.py: الإشعارات (Notification, NotificationPreference)
"""

# Favorites & Itinerary
from .favorites import (
    Favorite,
    Itinerary,
    ItineraryItem,
)

# Reviews & Comments
from .reviews import (
    Review,
    PlaceComment,
)

# Reports
from .reports import Report

# Follows
from .follows import EstablishmentFollow

# Live Share
from .liveshare import LiveShareSession, LiveLocationPing

# Notifications
from .notifications import (
    Notification,
    NotificationPreference,
    SystemAlert,
)

# Notification Outbox (Async Delivery)
from ..notifications.outbox import NotificationOutbox

# Moderation models moved to management app
# from management.models.moderation import ModerationRule, ModerationQueueItem

__all__ = [
    # Favorites
    'Favorite',
    'Itinerary',
    'ItineraryItem',
    # Reviews
    'Review',
    'PlaceComment',
    # Reports
    'Report',
    # Follows
    'EstablishmentFollow',
    # Notifications
    'Notification',
    'Notification',
    'NotificationPreference',
    'SystemAlert',
]
