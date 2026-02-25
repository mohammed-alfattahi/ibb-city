"""
Firebase Cloud Messaging (FCM) Provider Adapter
"""
import logging
import requests
from typing import Optional, Dict, Any
from django.conf import settings

from .base import BaseProvider, ProviderError, SendResult

logger = logging.getLogger(__name__)


class FCMProvider(BaseProvider):
    """Firebase Cloud Messaging provider."""
    
    provider_name = "fcm"
    API_URL = "https://fcm.googleapis.com/fcm/send"
    TIMEOUT = 10  # seconds
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', '')
    
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send push notification via FCM.
        
        Args:
            device_token: FCM registration token
            title: Notification title
            body: Notification body
            data: Additional data payload
        """
        if not self.server_key:
            raise ProviderError(
                "FCM server key not configured",
                provider=self.provider_name,
                retriable=False
            )
        
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
            },
        }
        
        if data:
            payload["data"] = data
        
        try:
            logger.info(f"Sending FCM notification to {device_token[:8]}...")
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self.TIMEOUT
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("success") == 1:
                message_id = response_data.get("results", [{}])[0].get("message_id")
                logger.info(f"FCM notification sent: {message_id}")
                return SendResult(
                    success=True,
                    message_id=message_id,
                    raw_response=response_data
                )
            else:
                error = response_data.get("results", [{}])[0].get("error", "Unknown error")
                logger.error(f"FCM error: {error}")
                
                # Check for non-retriable errors
                non_retriable = ["InvalidRegistration", "NotRegistered", "MismatchSenderId"]
                retriable = error not in non_retriable
                
                raise ProviderError(
                    error,
                    provider=self.provider_name,
                    retriable=retriable
                )
                
        except requests.Timeout:
            raise ProviderError(
                "FCM request timed out",
                provider=self.provider_name,
                retriable=True
            )
        except requests.RequestException as e:
            raise ProviderError(
                f"FCM request failed: {str(e)}",
                provider=self.provider_name,
                retriable=True
            )
