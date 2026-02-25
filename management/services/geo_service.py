from management.models import GeoZone, UserLocation
from django.db.models import Q
import json

class GeoService:
    """
    Service for Spatial Intelligence.
    Handles Point-in-Polygon checks and Location Tracking.
    """

    @staticmethod
    def update_user_location(user, lat, lon):
        """Update or create user location."""
        loc, created = UserLocation.objects.update_or_create(
            user=user,
            defaults={'latitude': lat, 'longitude': lon}
        )
        # Immediate Safety Check
        GeoService.check_user_safety(user, lat, lon)
        return loc

    @staticmethod
    def check_user_safety(user, lat, lon):
        """
        Check if user is inside any high-risk zone.
        Triggers alerts if true.
        """
        # Fetch active zones - optimization: filter by bounding box first in real PostGIS
        # Here we iterate (assuming low number of zones for MVP)
        zones = GeoZone.objects.filter(is_active=True)
        
        alerts = []
        for zone in zones:
            if GeoService._is_point_in_polygon(lat, lon, zone.polygon):
                alerts.append(zone)
                
        if alerts:
            GeoService._trigger_zone_alerts(user, alerts)
            
        return alerts

    @staticmethod
    def _is_point_in_polygon(lat, lon, polygon):
        """
        Ray Casting Algorithm to check if point (lat, lon) is inside polygon.
        Polygon is list of [lat, lon].
        """
        if not polygon or not isinstance(polygon, list):
            return False
            
        x, y = float(lat), float(lon)
        inside = False
        n = len(polygon)
        p1x, p1y = float(polygon[0][0]), float(polygon[0][1])
        
        for i in range(n + 1):
            p2x, p2y = float(polygon[i % n][0]), float(polygon[i % n][1])
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside

    @staticmethod
    def _trigger_zone_alerts(user, zones):
        """
        Trigger alerts via NotificationSystem.
        """
        # Import inside method to avoid circular import if necessary
        from interactions.notifications.notification_service import NotificationService
        
        for zone in zones:
            priority = 'critical' if zone.risk_level in ['HIGH', 'CRITICAL'] else 'high'
            NotificationService.emit_event(
                event_name='GEO_ALERT',
                payload={
                    'title': f'⚠️ تنبيه منطقة: {zone.name}',
                    'message': f'أنت تدخل منطقة مصنفة كـ {zone.get_zone_type_display()} ({zone.get_risk_level_display()}). يرجى الحذر.',
                    'zone_id': zone.id,
                    'type': zone.zone_type
                },
                audience_criteria={'user_id': user.id},
                priority=priority
            )
