"""
Notification Provider Adapters
Base classes and common interfaces
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, provider: str, retriable: bool = True):
        self.message = message
        self.provider = provider
        self.retriable = retriable
        super().__init__(message)


@dataclass
class SendResult:
    """Result of a send operation."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for notification providers."""
    
    provider_name: str = "base"
    
    @abstractmethod
    def send_push(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send a push notification.
        
        Args:
            device_token: Device token or player ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            SendResult with success status
            
        Raises:
            ProviderError on failure
        """
        pass
    
    def send_to_user(
        self,
        user,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SendResult:
        """
        Send notification to a user (looks up their device token).
        
        Args:
            user: User model instance
            title: Notification title
            body: Notification body
            data: Additional data payload
            
        Returns:
            SendResult
        """
        # Get device token from user
        device_token = getattr(user, 'fcm_token', None) or getattr(user, 'device_token', None)
        
        if not device_token:
            logger.warning(f"No device token for user {user.pk}")
            return SendResult(
                success=False,
                error="No device token registered"
            )
        
        return self.send_push(device_token, title, body, data, **kwargs)
