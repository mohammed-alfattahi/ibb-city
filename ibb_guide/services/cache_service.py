"""
Cache Service
Centralized cache key generation and invalidation helpers.
"""
import logging
from typing import Optional, List
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


# ==========================================
# TTL Constants
# ==========================================
TTL_SHORT = getattr(settings, 'CACHE_TTL_SHORT', 60)
TTL_MEDIUM = getattr(settings, 'CACHE_TTL_MEDIUM', 300)
TTL_LONG = getattr(settings, 'CACHE_TTL_LONG', 3600)
TTL_DAY = getattr(settings, 'CACHE_TTL_DAY', 86400)


# ==========================================
# Cache Key Generators
# ==========================================

def home_key(lang: str = 'ar') -> str:
    """Cache key for home page."""
    return f'home:{lang}'


def establishment_list_key(
    category: str = None,
    page: int = 1,
    lang: str = 'ar',
    filters: str = ''
) -> str:
    """Cache key for establishment list."""
    cat = category or 'all'
    return f'estab_list:{cat}:{page}:{lang}:{filters}'


def establishment_detail_key(pk: int, lang: str = 'ar') -> str:
    """Cache key for establishment detail."""
    return f'estab:{pk}:{lang}'


def category_list_key(lang: str = 'ar') -> str:
    """Cache key for categories."""
    return f'categories:{lang}'


def amenities_key(lang: str = 'ar') -> str:
    """Cache key for amenities list."""
    return f'amenities:{lang}'


def landmarks_list_key(page: int = 1, lang: str = 'ar') -> str:
    """Cache key for landmarks."""
    return f'landmarks:{page}:{lang}'


def search_key(query: str, page: int = 1, lang: str = 'ar') -> str:
    """Cache key for search results (short TTL)."""
    import hashlib
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    return f'search:{query_hash}:{page}:{lang}'


# ==========================================
# Cache Get/Set Helpers
# ==========================================

def get_cached(key: str, default=None):
    """Get value from cache with logging."""
    value = cache.get(key)
    if value is not None:
        logger.debug(f"Cache HIT: {key}")
    else:
        logger.debug(f"Cache MISS: {key}")
    return value if value is not None else default


def set_cached(key: str, value, ttl: int = TTL_MEDIUM):
    """Set value in cache."""
    cache.set(key, value, ttl)
    logger.debug(f"Cache SET: {key} (TTL={ttl}s)")


def delete_cached(key: str):
    """Delete key from cache."""
    cache.delete(key)
    logger.debug(f"Cache DELETE: {key}")


def delete_pattern(pattern: str):
    """
    Delete all keys matching pattern.
    Works with django-redis backend.
    """
    try:
        # django-redis supports delete_pattern
        cache.delete_pattern(pattern)
        logger.debug(f"Cache DELETE PATTERN: {pattern}")
    except AttributeError:
        # Fallback for backends that don't support patterns
        logger.warning(f"Cache backend doesn't support delete_pattern: {pattern}")


# ==========================================
# Invalidation Helpers
# ==========================================

def invalidate_establishment(pk: int):
    """Invalidate all caches related to an establishment."""
    # Delete detail in all languages
    for lang in ['ar', 'en']:
        delete_cached(establishment_detail_key(pk, lang))
    
    # Delete list caches (pattern-based)
    delete_pattern('estab_list:*')
    
    # Invalidate home (shows featured establishments)
    invalidate_home()
    
    logger.info(f"Cache invalidated for establishment {pk}")


def invalidate_category(slug: str = None):
    """Invalidate category-related caches."""
    # Delete all list caches
    delete_pattern('estab_list:*')
    delete_pattern('categories:*')
    logger.info(f"Cache invalidated for category {slug or 'all'}")


def invalidate_home():
    """Invalidate home page caches."""
    for lang in ['ar', 'en']:
        delete_cached(home_key(lang))
    logger.info("Cache invalidated for home page")


def invalidate_all():
    """Clear all caches (use with caution)."""
    cache.clear()
    logger.warning("All caches cleared!")


# ==========================================
# Cached Decorator
# ==========================================

def cached_view(key_func, ttl: int = TTL_MEDIUM):
    """
    Decorator for caching view results.
    
    Usage:
        @cached_view(lambda request: f'my_view:{request.LANGUAGE_CODE}', ttl=300)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            cache_key = key_func(request, *args, **kwargs)
            
            # Try cache
            cached_response = get_cached(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Execute view
            response = view_func(request, *args, **kwargs)
            
            # Cache successful responses only
            if hasattr(response, 'status_code') and response.status_code == 200:
                set_cached(cache_key, response, ttl)
            
            return response
        return wrapper
    return decorator


# ==========================================
# Cache Stats (for monitoring)
# ==========================================

def get_cache_stats() -> dict:
    """Get cache statistics (if supported by backend)."""
    try:
        # django-redis supports info
        client = cache.client.get_client()
        info = client.info('stats')
        return {
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'keys': client.dbsize(),
        }
    except Exception as e:
        logger.debug(f"Could not get cache stats: {e}")
        return {'hits': 'N/A', 'misses': 'N/A', 'keys': 'N/A'}
