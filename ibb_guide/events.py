"""
Domain Events Module
====================
Provides a clean abstraction for domain events, decoupling "what happened"
from "what to do next". This enables:
- Clean separation of concerns
- Easy addition of new handlers (notifications, analytics, etc.)
- Testable event-driven logic
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Callable, Type
from django.dispatch import Signal

# ============================================================================
# Base Event Classes
# ============================================================================

@dataclass
class DomainEvent:
    """Base class for all domain events."""
    occurred_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def event_name(self) -> str:
        return self.__class__.__name__


# ============================================================================
# Core Domain Events
# ============================================================================

@dataclass
class PlaceApproved(DomainEvent):
    """Fired when a place/establishment is approved by admin."""
    place_id: int = 0
    place_name: str = ""
    owner_id: int = 0
    approved_by_id: int = 0


@dataclass
class PlaceRejected(DomainEvent):
    """Fired when a place/establishment is rejected by admin."""
    place_id: int = 0
    place_name: str = ""
    owner_id: int = 0
    rejected_by_id: int = 0
    reason: str = ""


@dataclass
class ReviewCreated(DomainEvent):
    """Fired when a new review is submitted."""
    review_id: int = 0
    place_id: int = 0
    user_id: int = 0
    rating: int = 0


@dataclass
class ReviewReported(DomainEvent):
    """Fired when a review is reported for inappropriate content."""
    review_id: int = 0
    reported_by_id: int = 0
    reason: str = ""


@dataclass
class PartnerApproved(DomainEvent):
    """Fired when a partner registration is approved."""
    partner_id: int = 0
    user_id: int = 0
    approved_by_id: int = 0


@dataclass
class PartnerSuspended(DomainEvent):
    """Fired when a partner account is suspended."""
    partner_id: int = 0
    user_id: int = 0
    suspended_by_id: int = 0
    reason: str = ""


@dataclass
class RequestStatusChanged(DomainEvent):
    """Fired when any request changes status."""
    request_id: int = 0
    old_status: str = ""
    new_status: str = ""
    changed_by_id: int = 0


@dataclass
class WeatherAlertIssued(DomainEvent):
    """Fired when a weather alert is issued for a location."""
    location_id: int = 0
    alert_type: str = ""
    message: str = ""


# ============================================================================
# Event Bus (simple in-process implementation using Django Signals)
# ============================================================================

class EventBus:
    """
    Simple event bus for publishing and subscribing to domain events.
    Uses Django signals under the hood for synchronous in-process handling.
    Can be extended for async/external message queues in the future.
    """
    _signal = Signal()
    _handlers: Dict[Type[DomainEvent], List[Callable]] = {}
    
    @classmethod
    def publish(cls, event: DomainEvent):
        """Publish an event to all registered handlers."""
        event_type = type(event)
        handlers = cls._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't break the chain
                print(f"[EventBus] Error in handler {handler.__name__}: {e}")
        
        # Also send via Django signal for broader compatibility
        cls._signal.send(sender=event_type, event=event)
    
    @classmethod
    def subscribe(cls, event_type: Type[DomainEvent], handler: Callable):
        """Subscribe a handler to a specific event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
    
    @classmethod
    def clear(cls):
        """Clear all handlers (useful for testing)."""
        cls._handlers.clear()


# ============================================================================
# Decorator for easy handler registration
# ============================================================================

def handles(event_type: Type[DomainEvent]):
    """Decorator to register a function as a handler for an event type."""
    def decorator(func: Callable):
        EventBus.subscribe(event_type, func)
        return func
    return decorator
