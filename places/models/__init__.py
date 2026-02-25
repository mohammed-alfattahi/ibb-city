"""
Places Models Package
وحدة نماذج الأماكن المقسمة

الهيكل:
- base.py: النماذج الأساسية (Category, Amenity, Place, PlaceMedia)
- establishments.py: المنشآت التجارية (Establishment, EstablishmentUnit)
- landmarks.py: المعالم ونقاط الخدمات (Landmark, ServicePoint)
- routes.py: المسارات والتحليلات (TouristRoute, RouteWaypoint, PlaceViewLog)
"""

# Base Models
from .base import (
    Category,
    Amenity,
    Place,
    PlaceMedia,
)

# Establishment Models
from .establishments import (
    Establishment,
    EstablishmentUnit,
)

# Landmark Models
from .landmarks import (
    Landmark,
    ServicePoint,
)

# Route & Analytics Models
from .routes import (
    TouristRoute,
    RouteWaypoint,
    PlaceViewLog,
)

from .drafts import EstablishmentDraft

# Contact Models
from .contacts import (
    EstablishmentContact,
)


__all__ = [
    # Base
    'Category',
    'Amenity',
    'Place',
    'PlaceMedia',
    # Establishments
    'Establishment',
    'EstablishmentUnit',
    # Landmarks
    'Landmark',
    'ServicePoint',
    # Routes
    'TouristRoute',
    'RouteWaypoint',
    'PlaceViewLog',
    # Contacts
    'EstablishmentContact',
    'PlaceDailyView',
]

from .analytics import PlaceDailyView
from .offers import SpecialOffer

__all__.append('SpecialOffer')

