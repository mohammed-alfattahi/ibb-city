"""
Cache Tests
Tests for cache functionality and invalidation.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from ibb_guide.services.cache_service import (
    establishment_list_key,
    establishment_detail_key,
    home_key,
    get_cached,
    set_cached,
    delete_cached,
    invalidate_establishment,
    invalidate_home,
    TTL_MEDIUM,
)

User = get_user_model()


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class CacheKeyTest(TestCase):
    """Test cache key generation."""
    
    def test_establishment_list_key_includes_params(self):
        """Test that list key includes category, page, lang."""
        key1 = establishment_list_key(category='hotels', page=1, lang='ar')
        key2 = establishment_list_key(category='hotels', page=2, lang='ar')
        key3 = establishment_list_key(category='restaurants', page=1, lang='ar')
        
        self.assertIn('hotels', key1)
        self.assertNotEqual(key1, key2)  # Different pages
        self.assertNotEqual(key1, key3)  # Different categories
    
    def test_establishment_detail_key(self):
        """Test detail key includes pk and lang."""
        key_ar = establishment_detail_key(pk=123, lang='ar')
        key_en = establishment_detail_key(pk=123, lang='en')
        
        self.assertIn('123', key_ar)
        self.assertNotEqual(key_ar, key_en)
    
    def test_home_key_by_language(self):
        """Test home key varies by language."""
        key_ar = home_key('ar')
        key_en = home_key('en')
        
        self.assertNotEqual(key_ar, key_en)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class CacheOperationsTest(TestCase):
    """Test cache get/set/delete operations."""
    
    def test_set_and_get_cached(self):
        """Test setting and getting cached values."""
        set_cached('test_key', {'data': 'value'}, ttl=60)
        result = get_cached('test_key')
        
        self.assertEqual(result, {'data': 'value'})
    
    def test_get_cached_miss_returns_default(self):
        """Test that cache miss returns default."""
        result = get_cached('nonexistent_key', default='default_value')
        self.assertEqual(result, 'default_value')
    
    def test_delete_cached(self):
        """Test deleting cached values."""
        set_cached('delete_test', 'value')
        delete_cached('delete_test')
        result = get_cached('delete_test')
        
        self.assertIsNone(result)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class CacheInvalidationTest(TestCase):
    """Test cache invalidation."""
    
    def test_invalidate_establishment_clears_detail(self):
        """Test that invalidating establishment clears detail cache."""
        # Set detail cache
        detail_key = establishment_detail_key(pk=1, lang='ar')
        set_cached(detail_key, {'name': 'Test'})
        
        # Invalidate
        invalidate_establishment(pk=1)
        
        # Verify cleared
        result = get_cached(detail_key)
        self.assertIsNone(result)
    
    def test_invalidate_home_clears_home(self):
        """Test that invalidating home clears home cache."""
        home_ar = home_key('ar')
        set_cached(home_ar, {'featured': []})
        
        invalidate_home()
        
        result = get_cached(home_ar)
        self.assertIsNone(result)


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)
class CacheIntegrationTest(TestCase):
    """Integration tests for cache with views."""
    
    def test_repeated_requests_use_cache(self):
        """Test that repeated requests hit cache."""
        # First request populates cache
        key = 'integration_test'
        set_cached(key, 'cached_value', ttl=300)
        
        # Second request should get cached value
        value1 = get_cached(key)
        value2 = get_cached(key)
        
        self.assertEqual(value1, value2)
        self.assertEqual(value1, 'cached_value')
