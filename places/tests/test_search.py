from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from unittest.mock import patch
from places.models import Place, Category
from places.views_public import GlobalPlaceSearchView

class SearchTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category')
        self.place = Place.objects.create(
            name='Unique Place Name',
            category=self.category,
            is_active=True
        )
        self.url_global = reverse('global_search') # Check if this URL name is correct
        # If 'global_search' is not valid, I might need to check urls.py. 
        # Assuming typical name or I'll fix it after run.
        
    @patch('places.views_public.ml_search')
    def test_global_search_fallback(self, mock_ml):
        """Test global search falls back to DB when ML returns empty."""
        mock_ml.return_value = []
        
        # Searching for "Unique"
        try:
             # Try to reverse, if fails, use a likely path or skip
             url = reverse('global_search')
        except:
             # If url name is different, we might need to find it.
             # Based on previous view reading, GlobalPlaceSearchView is likely mapped.
             # I'll guess '/search/global/' or similar if fail.
             url = '/places/search/global/' 

        response = self.client.get(url, {'q': 'Unique'})
        
        # Check if place is in context['places']
        self.assertIn('places', response.context)
        self.assertIn(self.place, response.context['places'])
        
        # ML results should be empty
        self.assertNotIn('ml_results', response.context)

    @patch('places.views_public.ml_search')
    def test_global_search_ml_priority(self, mock_ml):
        """Test global search includes ML results."""
        mock_ml.return_value = [{'id': 999, 'name': 'ML Result', 'score': 0.9}]
        
        try:
             url = reverse('global_search')
        except:
             url = '/places/search/global/'

        response = self.client.get(url, {'q': 'Unique'})
        
        self.assertIn('ml_results', response.context)
        self.assertEqual(response.context['ml_results'], mock_ml.return_value)
        
        # DB results also included
        self.assertIn('places', response.context)

    @patch('places.views_public.ml_search')
    def test_smart_search_view(self, mock_ml):
        """Test smart search page."""
        mock_ml.return_value = [{'id': 1, 'name': 'Smart Result'}]
        try:
            url = reverse('places_search') 
        except:
            url = '/places/search/'
            
        response = self.client.get(url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)
        self.assertEqual(response.context['results'], mock_ml.return_value)
