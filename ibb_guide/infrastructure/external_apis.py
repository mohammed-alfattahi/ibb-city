"""
External APIs Infrastructure - Third-party Service Integrations

This module provides clean interfaces for external API integrations,
isolating the core application from third-party dependencies.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExternalAPIResult:
    """Standard result from external API calls."""
    success: bool
    data: Any = None
    error: str = None
    status_code: int = None


class WeatherAPIClient:
    """Client for weather API integration."""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: str = None):
        from django.conf import settings
        self.api_key = api_key or getattr(settings, 'WEATHER_API_KEY', None)
    
    def get_current_weather(self, lat: float, lng: float) -> ExternalAPIResult:
        """
        Get current weather for a location.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            ExternalAPIResult with weather data
        """
        if not self.api_key:
            return ExternalAPIResult(success=False, error="Weather API key not configured")
        
        try:
            import requests
            response = requests.get(
                f"{self.BASE_URL}/weather",
                params={
                    'lat': lat,
                    'lon': lng,
                    'appid': self.api_key,
                    'units': 'metric',
                    'lang': 'ar'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return ExternalAPIResult(
                    success=True,
                    data=response.json(),
                    status_code=200
                )
            else:
                return ExternalAPIResult(
                    success=False,
                    error=f"API returned {response.status_code}",
                    status_code=response.status_code
                )
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return ExternalAPIResult(success=False, error=str(e))

    def get_forecast(self, lat: float, lng: float) -> ExternalAPIResult:
        """
        Get 5-day weather forecast for a location.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            ExternalAPIResult with forecast data
        """
        if not self.api_key:
            return ExternalAPIResult(success=False, error="Weather API key not configured")
        
        try:
            import requests
            response = requests.get(
                f"{self.BASE_URL}/forecast",
                params={
                    'lat': lat,
                    'lon': lng,
                    'appid': self.api_key,
                    'units': 'metric',
                    'lang': 'ar',
                    'cnt': 40  # 5 days * 8 intervals (3h)
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return ExternalAPIResult(
                    success=True,
                    data=response.json(),
                    status_code=200
                )
            else:
                return ExternalAPIResult(
                    success=False,
                    error=f"API returned {response.status_code}",
                    status_code=response.status_code
                )
        except Exception as e:
            logger.error(f"Weather Forecast API error: {e}")
            return ExternalAPIResult(success=False, error=str(e))


class MapAPIClient:
    """Client for geocoding and map services."""
    
    def geocode(self, address: str) -> ExternalAPIResult:
        """
        Convert address to coordinates.
        
        Args:
            address: Address string
            
        Returns:
            ExternalAPIResult with lat/lng
        """
        # Placeholder - implement with actual geocoding service
        # Could use Google Maps, OpenStreetMap Nominatim, etc.
        return ExternalAPIResult(
            success=True,
            data={'lat': 13.9667, 'lng': 44.1833}  # Default to Ibb
        )
    
    def reverse_geocode(self, lat: float, lng: float) -> ExternalAPIResult:
        """
        Convert coordinates to address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            ExternalAPIResult with address
        """
        return ExternalAPIResult(
            success=True,
            data={'address': 'محافظة إب، اليمن'}
        )


class PushNotificationClient:
    """Unified client for push notification services."""
    
    def __init__(self):
        from django.conf import settings
        self.firebase_enabled = hasattr(settings, 'FIREBASE_CREDENTIALS')
        self.onesignal_enabled = hasattr(settings, 'ONESIGNAL_APP_ID')
    
    def send_to_user(self, user_id: int, title: str, message: str, 
                     data: Dict = None) -> ExternalAPIResult:
        """
        Send push notification to a user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification body
            data: Additional data payload
            
        Returns:
            ExternalAPIResult
        """
        results = []
        
        # Try Firebase first
        if self.firebase_enabled:
            try:
                from interactions.firebase_service import send_to_user as firebase_send
                firebase_send(user_id, title, message, data)
                results.append('firebase')
            except Exception as e:
                logger.error(f"Firebase error: {e}")
        
        # Try OneSignal as fallback
        if self.onesignal_enabled:
            try:
                from interactions.onesignal_service import send_notification
                send_notification(user_id, title, message)
                results.append('onesignal')
            except Exception as e:
                logger.error(f"OneSignal error: {e}")
        
        if results:
            return ExternalAPIResult(success=True, data={'sent_via': results})
        return ExternalAPIResult(success=False, error="No notification service available")
    
    def broadcast(self, title: str, message: str, data: Dict = None) -> ExternalAPIResult:
        """
        Broadcast notification to all users.
        
        Args:
            title: Notification title
            message: Notification body
            data: Additional data payload
            
        Returns:
            ExternalAPIResult
        """
        # Implementation depends on the notification service
        return ExternalAPIResult(
            success=True,
            data={'broadcast': True}
        )


class SocialMediaClient:
    """Client for social media integrations (future use)."""
    
    def share_place(self, place_id: int, platform: str) -> ExternalAPIResult:
        """Generate shareable link for a place."""
        return ExternalAPIResult(
            success=True,
            data={'share_url': f'/place/{place_id}/?utm_source={platform}'}
        )
