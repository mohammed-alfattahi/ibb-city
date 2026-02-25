from ..models import EventLog
from django.utils import timezone

def log_event(request, place, action, action_value=None, query_text=None):
    """
    Logs a user interaction event.
    
    Args:
        request: The Django request object (to extract user, IP/device info).
        place: The Place instance related to the event (can be None for generic search).
        action: The action type (view, click, search, etc.).
        action_value: Optional numeric value (e.g. rating, time spent).
        query_text: Optional search query text.
    """
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

    # Extract location if provided in GET params
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    try:
        lat = float(lat) if lat else None
        lng = float(lng) if lng else None
    except (ValueError, TypeError):
        lat, lng = None, None

    # device info could be more sophisticated, but User-Agent is a good start
    device = request.META.get("HTTP_USER_AGENT", "")[:120]

    EventLog.objects.create(
        user=user,
        place=place,
        action=action,
        action_value=action_value,
        query_text=query_text,
        device=device,
        lat=lat,
        lng=lng,
    )

def log_view(request, place):
    """Helper to log a 'view' event for a place."""
    log_event(request, place, "view")

def log_search(request, query_text, top_place=None):
    """Helper to log a 'search' event. Optionally links to a top result place."""
    log_event(request, top_place, "search", query_text=query_text)
