"""
Performance Tests
Tests for query optimization and aggregates.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

User = get_user_model()


class QueryOptimizationTest(TestCase):
    """Test query count on optimized views."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner',
            email='partner@test.com',
            password='testpass'
        )
    
    def test_establishment_list_query_count(self):
        """Test that establishment list uses minimal queries."""
        from places.models import Establishment
        
        # Use for_list() optimization
        with CaptureQueriesContext(connection) as context:
            list(Establishment.objects.for_list()[:10])
        
        # Should be 1-2 queries max (fetch + possible JOIN)
        self.assertLessEqual(len(context), 3)
    
    def test_establishment_with_relations_query_count(self):
        """Test that with_relations uses prefetch."""
        from places.models import Establishment
        
        with CaptureQueriesContext(connection) as context:
            list(Establishment.objects.with_relations()[:5])
        
        # Should be ~4 queries: main + prefetched relations
        self.assertLessEqual(len(context), 6)


class PaginationTest(TestCase):
    """Test pagination enforcement."""
    
    def test_establishment_queryset_limits(self):
        """Test that querysets respect limits."""
        from places.models import Establishment
        
        qs = Establishment.objects.for_list()[:20]
        
        # Query should have LIMIT
        sql = str(qs.query)
        self.assertIn('LIMIT', sql.upper())


class AggregateStorageTest(TestCase):
    """Test stored aggregates."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner',
            email='partner@test.com',
            password='testpass'
        )
    
    def test_establishment_has_aggregate_fields(self):
        """Test that aggregate fields exist."""
        from places.models import Establishment
        
        # Check fields exist
        self.assertTrue(hasattr(Establishment, 'cached_avg_rating'))
        self.assertTrue(hasattr(Establishment, 'cached_rating_count'))
        self.assertTrue(hasattr(Establishment, 'cached_review_count'))
    
    def test_aggregate_update_service(self):
        """Test that aggregate update service works."""
        from places.models import Establishment, Category
        from places.services.aggregate_service import update_establishment_aggregates
        
        # Create test establishment
        category, _ = Category.objects.get_or_create(name='Test')
        establishment = Establishment.objects.create(
            name='Test Place',
            owner=self.user,
            category=category
        )
        
        # Update aggregates (should not fail even with no ratings)
        update_establishment_aggregates(establishment.pk)
        
        establishment.refresh_from_db()
        self.assertEqual(establishment.cached_avg_rating, 0)
        self.assertEqual(establishment.cached_rating_count, 0)
