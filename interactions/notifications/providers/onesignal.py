"""
OneSignal Provider Adapter
"""
import logging
import requests
from typing import Optional, Dict, Any
from django.conf import settings

from .base import BaseProvider, ProviderError, SendResult

logger = logging.getLogger(__name__)


class OneSignalProvider(BaseProvider):
    """OneSignal push notification provider."""
    
    provider_name = "onesignal"
    API_URL = "https://onesignal.com/api/v1/notifications"
    TIMEOUT = 10  # seconds
    
    def __init__(self):
        self.app_id = getattr(settings, 'ONESIGNAL_APP_ID', '')
        self.api_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', '')
    
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send push notification via OneSignal.
        
        Args:
            device_token: OneSignal player_id
            title: Notification title
            body: Notification body
            data: Additional data payload
        """
        if not self.app_id or not self.api_key:
            raise ProviderError(
                "OneSignal credentials not configured",
                provider=self.provider_name,
                retriable=False
            )
        
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "app_id": self.app_id,
            "include_player_ids": [device_token],
            "headings": {"en": title},
            "contents": {"en": body},
        }
        
        if data:
            payload["data"] = data
        
        try:
            logger.info(f"Sending OneSignal notification to {device_token[:8]}...")
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self.TIMEOUT
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("id"):
                logger.info(f"OneSignal notification sent: {response_data['id']}")
                return SendResult(
                    success=True,
                    message_id=response_data["id"],
                    raw_response=response_data
                )
            else:
                error_msg = response_data.get("errors", ["Unknown error"])
                logger.error(f"OneSignal error: {error_msg}")
                raise ProviderError(
                    str(error_msg),
                    provider=self.provider_name,
                    retriable=True
                )
                
        except requests.Timeout:
            raise ProviderError(
                "OneSignal request timed out",
                provider=self.provider_name,
                retriable=True
            )
        except requests.RequestException as e:
            raise ProviderError(
                f"OneSignal request failed: {str(e)}",
                provider=self.provider_name,
                retriable=True
            )
