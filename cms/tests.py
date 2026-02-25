"""
Tests for CMS/Interface Control System
اختبارات نظام التحكم بالواجهة
"""
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.template import Context, Template

from cms.models import UIZone, UIComponent, ZoneComponent, UIRevision
from cms.services.ui_builder import (
    get_zone_items, snapshot_zone, copy_zone_components, 
    publish_zone, bump_version, revert_to_revision
)

User = get_user_model()


class UIZoneModelTestCase(TestCase):
    """Test UIZone model."""
    
    def setUp(self):
        self.zone = UIZone.objects.create(
            name='الشريط الجانبي',
            slug='sidebar_right',
            description='الشريط الجانبي الأيمن'
        )
    
    def test_zone_creation(self):
        """Zone should be created with correct attributes."""
        self.assertEqual(self.zone.name, 'الشريط الجانبي')
        self.assertEqual(self.zone.slug, 'sidebar_right')
    
    def test_zone_str(self):
        """Zone string representation should be the name."""
        self.assertEqual(str(self.zone), 'الشريط الجانبي')


class UIComponentModelTestCase(TestCase):
    """Test UIComponent model."""
    
    def setUp(self):
        self.component = UIComponent.objects.create(
            name='Weather Widget',
            slug='weather_widget',
            template_path='components/molecules/weather_widget.html',
            default_data={'city': 'Ibb', 'units': 'metric'}
        )
    
    def test_component_creation(self):
        """Component should be created with default_data."""
        self.assertEqual(self.component.slug, 'weather_widget')
        self.assertEqual(self.component.default_data['city'], 'Ibb')
    
    def test_component_str(self):
        """Component string representation should be the name."""
        self.assertEqual(str(self.component), 'Weather Widget')


class ZoneComponentModelTestCase(TestCase):
    """Test ZoneComponent model."""
    
    def setUp(self):
        self.zone = UIZone.objects.create(name='Test Zone', slug='test_zone')
        self.component = UIComponent.objects.create(
            name='Test Component',
            slug='test_component',
            template_path='test.html',
            default_data={'key': 'default_value'}
        )
        self.zone_component = ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component,
            order=1,
            is_visible=True,
            stage='published',
            data_override={'key': 'override_value'}
        )
    
    def test_zone_component_ordering(self):
        """Zone components should be ordered by order field."""
        zc2 = ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component,
            order=0,
            stage='published'
        )
        
        components = list(self.zone.components.all())
        self.assertEqual(components[0], zc2)  # order=0 first
        self.assertEqual(components[1], self.zone_component)  # order=1 second


class UIBuilderServiceTestCase(TransactionTestCase):
    """Test ui_builder service functions."""
    
    def setUp(self):
        cache.clear()
        
        self.user = User.objects.create_superuser(
            username='cms_admin',
            email='cms@test.com',
            password='adminpass123'
        )
        
        self.zone = UIZone.objects.create(name='Homepage', slug='homepage_main')
        self.component1 = UIComponent.objects.create(
            name='Hero Banner',
            slug='hero_banner',
            template_path='components/hero.html'
        )
        self.component2 = UIComponent.objects.create(
            name='Featured Places',
            slug='featured_places',
            template_path='components/featured.html'
        )
        
        # Published components
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component1,
            order=1,
            stage='published',
            is_visible=True
        )
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component2,
            order=2,
            stage='published',
            is_visible=True
        )
    
    def test_get_zone_items_returns_published(self):
        """get_zone_items should return published components."""
        items = get_zone_items('homepage_main', stage='published')
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].component.slug, 'hero_banner')
        self.assertEqual(items[1].component.slug, 'featured_places')
    
    def test_get_zone_items_caches_results(self):
        """Results should be cached."""
        # First call
        items1 = get_zone_items('homepage_main')
        
        # Add new component (shouldn't appear due to cache)
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component1,
            order=3,
            stage='published',
            is_visible=True
        )
        
        # Second call (from cache)
        items2 = get_zone_items('homepage_main')
        
        self.assertEqual(len(items1), len(items2))
    
    def test_bump_version_invalidates_cache(self):
        """bump_version should invalidate cache."""
        # Cache some items
        items1 = get_zone_items('homepage_main')
        
        # Bump version
        bump_version()
        
        # Add new component
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component1,
            order=3,
            stage='published',
            is_visible=True
        )
        
        # New call should reflect changes
        items2 = get_zone_items('homepage_main')
        
        self.assertEqual(len(items2), 3)
    
    def test_snapshot_zone(self):
        """snapshot_zone should capture zone state."""
        snapshot = snapshot_zone(self.zone, 'published')
        
        self.assertEqual(snapshot['zone']['slug'], 'homepage_main')
        self.assertEqual(snapshot['stage'], 'published')
        self.assertEqual(len(snapshot['components']), 2)
    
    def test_copy_zone_components(self):
        """copy_zone_components should duplicate from one stage to another."""
        # Copy published to draft
        copy_zone_components(self.zone, 'published', 'draft', user=self.user)
        
        draft_items = self.zone.components.filter(stage='draft')
        
        self.assertEqual(draft_items.count(), 2)
        
        # Check revision was created
        revision = UIRevision.objects.filter(zone=self.zone).first()
        self.assertIsNotNone(revision)
        self.assertEqual(revision.action, 'copy')
    
    def test_publish_zone(self):
        """publish_zone should copy draft to published."""
        # Create draft components
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component1,
            order=1,
            stage='draft',
            data_override={'new': 'data'}
        )
        
        # Clear published
        self.zone.components.filter(stage='published').delete()
        
        # Publish
        publish_zone(self.zone, user=self.user)
        
        published = self.zone.components.filter(stage='published')
        self.assertEqual(published.count(), 1)
        self.assertEqual(published.first().data_override, {'new': 'data'})
    
    def test_revert_to_revision(self):
        """revert_to_revision should restore a previous state."""
        # Create a revision with snapshot
        revision = UIRevision.objects.create(
            zone=self.zone,
            action='publish',
            from_stage='draft',
            to_stage='published',
            snapshot={
                'zone': {'slug': 'homepage_main', 'name': 'Homepage'},
                'stage': 'published',
                'components': [
                    {
                        'component_slug': 'hero_banner',
                        'component_template': 'components/hero.html',
                        'order': 1,
                        'is_visible': True,
                        'data_override': {'reverted': True}
                    }
                ]
            },
            created_by=self.user
        )
        
        # Change current state
        self.zone.components.filter(stage='published').delete()
        
        # Revert
        success, message = revert_to_revision(revision, user=self.user)
        
        self.assertTrue(success)
        
        # Check restored
        published = self.zone.components.filter(stage='published')
        self.assertEqual(published.count(), 1)
        self.assertEqual(published.first().data_override, {'reverted': True})


class CMSTemplateTagTestCase(TestCase):
    """Test cms_tags template tag."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.zone = UIZone.objects.create(name='Test', slug='test_tag')
        self.component = UIComponent.objects.create(
            name='Test',
            slug='test',
            template_path='components/test.html'
        )
        ZoneComponent.objects.create(
            zone=self.zone,
            component=self.component,
            order=1,
            stage='published',
            is_visible=True
        )
    
    def test_render_zone_tag_loads(self):
        """render_zone tag should load without errors."""
        from cms.templatetags.cms_tags import render_zone
        
        request = self.factory.get('/')
        context = Context({'request': request})
        
        result = render_zone(context, 'test_tag')
        
        self.assertIn('items', result)
        self.assertEqual(result['stage'], 'published')
