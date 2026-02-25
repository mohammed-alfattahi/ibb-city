"""
ml_client.py — Django service to call the FastAPI ML service.
"""
import logging
from django.conf import settings

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)

ML_BASE_URL = getattr(settings, "ML_SERVICE_URL", "http://127.0.0.1:8001")
ML_TIMEOUT = getattr(settings, "ML_SERVICE_TIMEOUT", 10)


def _get():
    if httpx is None:
        raise ImportError("Install httpx: pip install httpx")
    return httpx.Client(base_url=ML_BASE_URL, timeout=ML_TIMEOUT)


def ml_search(query: str, top_k: int = 10) -> list[dict]:
    """Smart search via ML service."""
    try:
        with _get() as client:
            r = client.post("/search", json={"query": query, "top_k": top_k})
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"ML search failed: {e}")
        return []


def ml_nearest(lat: float, lon: float, k: int = 10,
               radius_km: float = None, amenity: str = None) -> list[dict]:
    """Nearest POIs via ML service."""
    try:
        body = {"lat": lat, "lon": lon, "k": k}
        if radius_km:
            body["radius_km"] = radius_km
        if amenity:
            body["amenity"] = amenity
        with _get() as client:
            r = client.post("/nearest", json=body)
            r.raise_for_status()
            return r.json().get("results", [])
    except Exception as e:
        logger.warning(f"ML nearest failed: {e}")
        return []


def ml_features(place_index: int) -> dict:
    """POI features for a specific place."""
    try:
        with _get() as client:
            r = client.post("/features", json={"place_index": place_index})
            r.raise_for_status()
            return r.json().get("features", {})
    except Exception as e:
        logger.warning(f"ML features failed: {e}")
        return {}


def ml_reindex() -> bool:
    """Trigger full reindex on ML service."""
    try:
        with _get() as client:
            r = client.post("/reindex")
            r.raise_for_status()
            return True
    except Exception as e:
        logger.warning(f"ML reindex failed: {e}")
        return False


def ml_health() -> dict:
    """Check ML service health."""
    try:
        with _get() as client:
            r = client.get("/health")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"ML health check failed: {e}")
        return {"status": "unavailable", "error": str(e)}
