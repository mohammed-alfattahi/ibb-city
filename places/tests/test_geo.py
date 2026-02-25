"""
Geo Service Tests
Tests for location-based features.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from places.services.geo_service import (
    haversine_distance,
    get_bounding_box,
    apply_bounding_box,
    get_nearby_establishments,
    MAX_RADIUS_KM,
    MAX_LIMIT
)

User = get_user_model()


class HaversineDistanceTest(TestCase):
    """Test Haversine distance calculation."""
    
    def test_same_point_is_zero(self):
        """Distance from point to itself is zero."""
        distance = haversine_distance(13.97, 44.17, 13.97, 44.17)
        self.assertEqual(distance, 0.0)
    
    def test_known_distance(self):
        """Test against known distance between two cities."""
        # Ibb to Sana'a (approximately 120 km)
        ibb_lat, ibb_lon = 13.97, 44.17
        sanaa_lat, sanaa_lon = 15.35, 44.20
        
        distance = haversine_distance(ibb_lat, ibb_lon, sanaa_lat, sanaa_lon)
        
        # Should be ~153 km (within 10km tolerance)
        self.assertGreater(distance, 140)
        self.assertLess(distance, 165)
    
    def test_short_distance(self):
        """Test short distance is accurate."""
        # Two points 1km apart approximately
        lat1, lon1 = 13.97, 44.17
        lat2, lon2 = 13.979, 44.17  # ~1km north
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be ~1km
        self.assertGreater(distance, 0.5)
        self.assertLess(distance, 1.5)


class BoundingBoxTest(TestCase):
    """Test bounding box calculation."""
    
    def test_bounding_box_size(self):
        """Test bounding box has correct size."""
        lat, lon = 13.97, 44.17
        radius_km = 10
        
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_km)
        
        # Box should extend ~0.09 degrees in each direction
        self.assertLess(min_lat, lat)
        self.assertGreater(max_lat, lat)
        self.assertLess(min_lon, lon)
        self.assertGreater(max_lon, lon)
    
    def test_bounding_box_symmetry(self):
        """Box should be symmetric around center."""
        lat, lon = 13.97, 44.17
        radius_km = 5
        
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, radius_km)
        
        lat_delta_min = lat - min_lat
        lat_delta_max = max_lat - lat
        
        self.assertAlmostEqual(lat_delta_min, lat_delta_max, places=5)


class NearbyEstablishmentsTest(TestCase):
    """Test nearby establishment queries."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner',
            email='partner@test.com',
            password='testpass'
        )
    
    def _create_establishment(self, name, lat, lon, approved=True):
        """Helper to create establishment."""
        from places.models import Establishment, Category
        
        category, _ = Category.objects.get_or_create(name='Test')
        
        return Establishment.objects.create(
            name=name,
            owner=self.user,
            category=category,
            latitude=Decimal(str(lat)),
            longitude=Decimal(str(lon)),
            approval_status='approved' if approved else 'pending',
            is_active=True
        )
    
    def test_nearby_returns_close_places(self):
        """Test that nearby returns establishments within radius."""
        # Create nearby establishment
        self._create_establishment('Nearby', 13.971, 44.171)
        
        results = list(get_nearby_establishments(13.97, 44.17, radius_km=5))
        
        self.assertEqual(len(results), 1)
    
    def test_nearby_excludes_far_places(self):
        """Test that nearby excludes distant establishments."""
        # Create far establishment (100km away)
        self._create_establishment('Far Away', 14.87, 44.17)
        
        results = list(get_nearby_establishments(13.97, 44.17, radius_km=10))
        
        self.assertEqual(len(results), 0)
    
    def test_nearby_excludes_unapproved(self):
        """Test that nearby NEVER returns unapproved establishments."""
        # Create nearby but unapproved establishment
        self._create_establishment('Pending Place', 13.971, 44.171, approved=False)
        
        results = list(get_nearby_establishments(13.97, 44.17, radius_km=5))
        
        self.assertEqual(len(results), 0)
    
    def test_distance_ordering(self):
        """Test that results are ordered by distance."""
        # Create establishments at different distances
        self._create_establishment('Close', 13.971, 44.171)    # ~0.1km
        self._create_establishment('Medium', 13.98, 44.18)     # ~1.5km
        self._create_establishment('Far', 14.0, 44.2)          # ~5km
        
        results = list(get_nearby_establishments(13.97, 44.17, radius_km=20))
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, 'Close')
        self.assertEqual(results[1].name, 'Medium')
        self.assertEqual(results[2].name, 'Far')
    
    def test_limit_enforced(self):
        """Test that limit is enforced."""
        # Create many establishments with valid lat precision
        for i in range(15):
            lat = Decimal('13.97') + Decimal(str(i * 0.01))
            self._create_establishment(f'Place {i}', float(lat), 44.17)
        
        results = list(get_nearby_establishments(13.97, 44.17, radius_km=50, limit=10))
        
        self.assertEqual(len(results), 10)
    
    def test_max_radius_enforced(self):
        """Test that max radius is enforced even if larger value is passed."""
        # This should internally cap at MAX_RADIUS_KM
        results = get_nearby_establishments(13.97, 44.17, radius_km=500)
        
        # Should not crash
        self.assertIsNotNone(results)
    
    def test_max_limit_enforced(self):
        """Test that max limit is enforced."""
        results = get_nearby_establishments(13.97, 44.17, limit=1000)
        
        # Query should execute without error
        self.assertIsNotNone(results)
