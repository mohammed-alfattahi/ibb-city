"""
Notification Providers Package
"""
from .base import BaseProvider, ProviderError, SendResult
from .onesignal import OneSignalProvider
from .fcm import FCMProvider
from .email import EmailProvider

__all__ = [
    'BaseProvider',
    'ProviderError', 
    'SendResult',
    'OneSignalProvider',
    'FCMProvider',
    'EmailProvider',
]


def get_provider(provider_name: str) -> BaseProvider:
    """
    Factory function to get provider instance by name.
    
    Args:
        provider_name: 'onesignal', 'fcm', 'email', etc.
        
    Returns:
        Provider instance
        
    Raises:
        ValueError if provider unknown
    """
    providers = {
        'onesignal': OneSignalProvider,
        'fcm': FCMProvider,
        'email': EmailProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return providers[provider_name]()

