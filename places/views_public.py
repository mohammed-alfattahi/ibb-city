from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import FormMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import translation
from django.core.paginator import Paginator

from django.db import models
from django.db.models import Exists, OuterRef
from .models import Place, Category, Establishment
from .filters import PlaceFilter
from interactions.forms_public import ReviewForm, ReportForm
from interactions.models import Review, Favorite

from django.core.cache import cache
from django.utils import timezone
from management.selectors import get_random_active_ad
from events.models import Event

# Architecture Imports
from places import selectors
from places.services import geo_service
from ibb_guide.services.ml_client import ml_search, ml_nearest

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use Cached Stats
        stats = cache.get('home_stats')
        if not stats:
            stats = {
                'places_count': Place.objects.filter(is_active=True).count(),
                'users_count': 1250, # Mock or real
                'reviews_count': Review.objects.count()
            }
            cache.set('home_stats', stats, 300)
        context['stats'] = stats

        # Featured and Latest Blocks
        featured = cache.get('home_featured_places')
        if featured is None:
            featured = list(selectors.get_public_places(self.request.user).filter(is_featured=True)[:6])
            cache.set('home_featured_places', featured, 60)
        context['featured_places'] = featured

        latest = cache.get('home_latest_places')
        if latest is None:
            latest = list(selectors.get_public_places(self.request.user)[:8])
            cache.set('home_latest_places', latest, 60)
        context['latest_places'] = latest

        context['categories'] = Category.objects.all()
        
        # Recommendations
        context['recommended_places'] = selectors.get_recommended_places(self.request.user)
        
        # Ads (cached random pick)
        context['page_ad'] = get_random_active_ad('banner')
        
        # Events
        context['upcoming_events'] = Event.objects.filter(
            start_datetime__gte=timezone.now(),
            is_featured=True
        ).order_by('start_datetime')[:6]

        return context


class GlobalPlaceSearchView(TemplateView):
    """Instant search for header."""
    template_name = 'places/partials/global_search_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        if query:
            # Try ML smart search first, fallback to DB filter
            ml_results = ml_search(query, top_k=5)
            if ml_results:
                context['ml_results'] = ml_results
            # Always include DB results as fallback / supplement
            context['places'] = selectors.get_public_places().filter(name__icontains=query)[:5]
            context['query'] = query
        
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial template if the request is an HTMX request.
        """
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/global_search_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)


class SmartSearchView(TemplateView):
    """Full-page ML-powered smart search."""
    template_name = 'places/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = (self.request.GET.get('q') or '').strip()
        context['q'] = q
        if q:
            context['results'] = ml_search(q, top_k=20)
        return context


class CategoryPlaceListView(ListView):
    model = Place
    template_name = 'places/category_detail.html'
    context_object_name = 'places'
    paginate_by = 9
    filterset_class = PlaceFilter # Reusing the filter if possible, or build custom

    def get_queryset(self):
        self.category = Category.objects.get(pk=self.kwargs['pk'])
        # Use selector or direct filter
        qs = Place.objects.filter(
            category=self.category,
            is_active=True
        ).filter(
            # Show if it's NOT an establishment (e.g. Landmark) OR if it is an approved establishment
            Q(establishment__isnull=True) | Q(establishment__approval_status='approved')
        ).select_related('category', 'establishment')
        
        if self.request.user.is_authenticated:
            favs = Favorite.objects.filter(user=self.request.user, place=OuterRef('pk'))
            qs = qs.annotate(is_favorited=Exists(favs))
        
        # Apply Filters (Reuse PlaceFilter logic if applicable, or manual)
        # For now, let's minimally support search and rating from the design
        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            qs = qs.filter(avg_rating__gte=float(min_rating))
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['page_config'] = {
            'hero_title': self.category.name,
            'hero_subtitle': f"استكشف {self.category.name} المميزة في إب",
            'hero_image': self.category.icon if self.category.icon else None
        }
        context['categories'] = Category.objects.all() # For filter dropdown
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/place_list_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)

class PlaceListView(ListView):
    model = Place
    template_name = 'place_list.html'
    context_object_name = 'places'
    paginate_by = 9
    filterset_class = PlaceFilter

    def get_queryset(self):
        # Use Selector which already handles basic optimizations
        # Note: selectors.get_public_places already has select_related('category', 'establishment')
        qs = selectors.get_public_places(self.request.user)
        
        # Apply Filters
        self.filterset = self.filterset_class(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.filterset.form
        
        # Optimized category fetching with cache
        from django.core.cache import cache
        from django.conf import settings
        from places.models import Category, Place
        
        cache_key = 'places:categories:all'
        categories = cache.get(cache_key)
        if categories is None:
            categories = list(Category.objects.all())
            cache.set(cache_key, categories, getattr(settings, 'CACHE_TTL_LONG', 3600))
        
        context['categories'] = categories
        context['directorate_choices'] = Place.DIRECTORATE_CHOICES
        context['classification_choices'] = Place.CLASSIFICATION_CHOICES
        context['road_choices'] = Place.ROAD_CHOICES
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Return a partial template if the request is an HTMX request.
        """
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/place_list_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)

class NatureListView(ListView):
    template_name = 'places/nature_list.html'
    context_object_name = 'places'
    paginate_by = 9
    
    def get_queryset(self):
        return selectors.get_nature_places(self.request.user)

class LandmarksListView(ListView):
    template_name = 'places/landmarks_list.html'
    context_object_name = 'places'
    paginate_by = 9

    def get_queryset(self):
        return selectors.get_landmarks(self.request.user)

class RestaurantListView(ListView):
    template_name = 'places/category_detail.html'
    context_object_name = 'places'
    paginate_by = 9

    def get_queryset(self):
        qs = selectors.get_restaurants(self.request.user)
        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            qs = qs.filter(avg_rating__gte=float(min_rating))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_config'] = {
            'hero_title': 'المطاعم والمقاهي',
            'hero_subtitle': 'تذوق أشهى المأكولات في أفضل مطاعم ومقاهي إب',
        }
        context['categories'] = Category.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/place_list_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)

class HotelListView(ListView):
    template_name = 'places/category_detail.html'
    context_object_name = 'places'
    paginate_by = 9

    def get_queryset(self):
        qs = selectors.get_hotels(self.request.user)
        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            qs = qs.filter(avg_rating__gte=float(min_rating))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_config'] = {
            'hero_title': 'الفنادق والإقامة',
            'hero_subtitle': 'أفضل خيارات الإقامة لراحة لا تضاهى',
        }
        context['categories'] = Category.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/place_list_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)

class ParkListView(ListView):
    template_name = 'places/category_detail.html'
    context_object_name = 'places'
    paginate_by = 9

    def get_queryset(self):
        qs = selectors.get_parks(self.request.user)
        search_query = self.request.GET.get('search', '')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            qs = qs.filter(avg_rating__gte=float(min_rating))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_config'] = {
            'hero_title': 'المنتزهات والترفيه',
            'hero_subtitle': 'أماكن ترفيهية رائعة لقضاء أوقات ممتعة مع العائلة',
        }
        context['categories'] = Category.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return self.response_class(
                request=self.request,
                template='places/partials/place_list_results.html',
                context=context,
                using=self.template_engine,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)

class PlaceDetailView(FormMixin, DetailView):
    model = Place
    template_name = 'place_detail.html'
    context_object_name = 'place'
    form_class = ReviewForm

    def get_success_url(self):
        return reverse('place_detail', kwargs={'pk': self.object.pk})
    
    # ============================
    # Helper Methods for Context
    # ============================
    
    def _get_favorite_status(self):
        """Check if current user has favorited this place."""
        if self.request.user.is_authenticated:
            return Favorite.objects.filter(
                user=self.request.user, place=self.object
            ).exists()
        return False
    
    def _get_active_offers(self):
        """Get active special offers for establishment."""
        if hasattr(self.object, 'establishment'):
            from places.models import SpecialOffer
            now = timezone.now()
            return SpecialOffer.objects.filter(
                establishment=self.object.establishment,
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        return []
    
    def _check_management_rights(self):
        """Check if user has owner/staff rights."""
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_staff:
            return True
        try:
            est = self.object.establishment
            return est.owner == self.request.user
        except Exception:
            return False
    
    def _get_reviews_and_comments(self, has_management_rights):
        """Get reviews and comments with visibility filtering."""
        from django.db.models import Prefetch
        from interactions.models import PlaceComment
        
        reviews_qs = self.object.reviews.select_related('user')
        replies_qs = PlaceComment.objects.select_related('user').order_by('created_at')
        
        if not has_management_rights:
            reviews_qs = reviews_qs.filter(visibility_state='visible')
            replies_qs = replies_qs.filter(visibility_state='visible')
        
        reviews = reviews_qs.order_by('-created_at').prefetch_related(
            Prefetch('replies', queryset=replies_qs)
        )
        
        # Standalone comments
        comments_qs = self.object.comments.filter(
            review__isnull=True, parent__isnull=True
        ).select_related('user')
        
        if not has_management_rights:
            comments_qs = comments_qs.filter(visibility_state='visible')
        
        comments = comments_qs.order_by('-created_at').prefetch_related(
            Prefetch('replies', queryset=replies_qs)
        )
        
        return reviews, comments
    
    def _get_grouped_contacts(self):
        """Get contacts from Establishment model OR Place.contact_info JSON."""
        grouped = {'phones': [], 'messaging': [], 'social': [], 'links': []}

        # 1. Try Establishment Contacts (Model)
        if hasattr(self.object, 'establishment'):
            contacts = self.object.establishment.contacts.filter(is_visible=True).order_by('display_order')
            for c in contacts:
                target_list = 'links'
                if c.type == 'phone': target_list = 'phones'
                elif c.type in ['whatsapp', 'telegram']: target_list = 'messaging'
                elif c.type in ['facebook', 'instagram', 'tiktok', 'snapchat', 'youtube']: target_list = 'social'
                grouped[target_list].append(c)

        # 2. Try Place JSON (Fallback/Merge)
        # Structure expected: {'phone': '...', 'whatsapp': '...', 'facebook': '...'}
        if self.object.contact_info:
            for key, value in self.object.contact_info.items():
                if not value: continue
                
                # Generate Action URL
                action_url = value
                if key in ['phone', 'mobile']:
                    action_url = f"tel:{value}"
                elif key == 'whatsapp':
                    # Clean number
                    clean_num = ''.join(filter(str.isdigit, str(value)))
                    action_url = f"https://wa.me/{clean_num}"
                elif key == 'email':
                    action_url = f"mailto:{value}"
                elif key in ['facebook', 'instagram', 'twitter', 'tiktok', 'website', 'maps']:
                    if not str(value).startswith(('http://', 'https://')):
                        action_url = f"https://{value}"

                # Create mock object compatible with template
                mock_contact = {
                    'type': key, 
                    'value': value, 
                    'get_type_display': key.title(),
                    'action_url': action_url,
                    # Icon mapping if needed, though template uses conditional classes based on type
                    'icon_class': self._get_icon_class(key) 
                }
                
                if key in ['phone', 'mobile']:
                    grouped['phones'].append(mock_contact)
                elif key in ['whatsapp', 'telegram']:
                    grouped['messaging'].append(mock_contact)
                elif key in ['facebook', 'instagram', 'twitter', 'tiktok', 'snapchat', 'youtube']:
                    grouped['social'].append(mock_contact)
                elif key in ['website', 'email', 'maps']:
                    grouped['links'].append(mock_contact)

        return grouped

    def _get_icon_class(self, type_name):
        icons = {
            'phone': 'fas fa-phone', 'mobile': 'fas fa-mobile-alt',
            'whatsapp': 'fab fa-whatsapp', 'telegram': 'fab fa-telegram-plane',
            'facebook': 'fab fa-facebook-f', 'instagram': 'fab fa-instagram',
            'twitter': 'fab fa-twitter', 'tiktok': 'fab fa-tiktok',
            'youtube': 'fab fa-youtube', 'snapchat': 'fab fa-snapchat-ghost',
            'website': 'fas fa-globe', 'email': 'fas fa-envelope',
            'maps': 'fas fa-map-marker-alt'
        }
        return icons.get(type_name, 'fas fa-link')

        return grouped
    
    def _get_related_places(self):
        """Get related places by location or category."""
        if self.object.latitude and self.object.longitude:
            return geo_service.get_nearby_places(
                lat=float(self.object.latitude),
                lon=float(self.object.longitude),
                limit=3,
                radius_km=50,
                exclude_ids=[self.object.id]
            )
        return Place.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:3]
    
    def _get_closing_status(self):
        """Parse opening hours and determine closing status."""
        hours_text = self.object.opening_hours_text
        status = {'state': 'unknown', 'minutes': 0}
        
        if not hours_text or '-' not in hours_text:
            return status
        
        try:
            from datetime import datetime, timedelta
            parts = hours_text.split('-')
            if len(parts) != 2:
                return status
            
            start_str, end_str = parts[0].strip(), parts[1].strip()
            now = timezone.localtime(timezone.now())
            current_time = now.time()
            
            start_dt = datetime.strptime(start_str, "%H:%M").time()
            end_dt = datetime.strptime(end_str, "%H:%M").time()
            
            # Check if open
            is_open = False
            if start_dt <= end_dt:
                is_open = start_dt <= current_time <= end_dt
            else:  # Crosses midnight
                is_open = current_time >= start_dt or current_time <= end_dt
            
            if not is_open:
                return {'state': 'closed', 'minutes': 0}
            
            # Check closing soon (within 30 min)
            close_dt = now.replace(hour=end_dt.hour, minute=end_dt.minute, second=0)
            if end_dt < start_dt and current_time > start_dt:
                close_dt += timedelta(days=1)
            
            diff = (close_dt - now).total_seconds() / 60
            if 0 < diff <= 30:
                return {'state': 'closing_soon', 'minutes': int(diff)}
            return {'state': 'open', 'minutes': 0}
            
        except ValueError:
            return status
    
    def _track_view(self):
        """Track page view and daily analytics."""
        try:
            from places.models import PlaceDailyView
            
            # Increment total views
            Place.objects.filter(pk=self.object.pk).update(
                view_count=models.F('view_count') + 1
            )
            
            # Increment daily views
            today = timezone.now().date()
            daily_view, _ = PlaceDailyView.objects.get_or_create(
                place=self.object, date=today
            )
            PlaceDailyView.objects.filter(pk=daily_view.pk).update(
                views=models.F('views') + 1
            )
        except Exception:
            pass  # Don't break page for analytics

    def _get_rating_stats(self):
        """Calculate rating distribution and total count."""
        from django.db.models import Count
        reviews = self.object.reviews.filter(visibility_state='visible')
        total = reviews.count()
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        
        # Optimize: aggregation
        stats = reviews.values('rating').annotate(count=Count('rating'))
        for item in stats:
            distribution[item['rating']] = item['count']
            
        # Add percentage
        final_dist = []
        for star in range(5, 0, -1):
            count = distribution.get(star, 0)
            percent = (count / total * 100) if total > 0 else 0
            final_dist.append({
                'star': star,
                'count': count,
                'percent': percent
            })
            
        return {
            'total_reviews': total,
            'distribution': final_dist
        }

    # ============================
    # Main Context Builder
    # ============================

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use helper methods
        context['is_favorited'] = self._get_favorite_status()
        context['active_offers'] = self._get_active_offers()
        
        has_management_rights = self._check_management_rights()
        context['has_management_rights'] = has_management_rights
        
        reviews, comments = self._get_reviews_and_comments(has_management_rights)
        context['reviews'] = reviews
        context['place_comments'] = comments
        
        context['review_form'] = self.get_form()
        context['report_form'] = ReportForm()
        
        context['grouped_contacts'] = self._get_grouped_contacts()
        context['related_places'] = self._get_related_places()
        context['closing_status'] = self._get_closing_status()
        
        # ML: Nearest POIs within 3 km
        place = self.object
        if place.latitude and place.longitude:
            context['nearest_pois'] = ml_nearest(
                lat=float(place.latitude),
                lon=float(place.longitude),
                k=5, radius_km=3,
            )
            
        # Rating Stats
        context['rating_stats'] = self._get_rating_stats()
        
        # Track view (non-blocking)
        self._track_view()

        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        review = form.save(commit=False)
        review.place = self.object
        review.user = self.request.user
        review.save()
        messages.success(self.request, "تم إضافة تقييمك بنجاح")
        return super().form_valid(form)



# ============================================
# Nearby Places Search (Geographic Search)
# ============================================
class NearbyPlacesView(TemplateView):
    """
    Find nearby places using GeoService.
    """
    template_name = "places/nearby_results.html"

    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('current_lon') or request.GET.get('lon') or request.GET.get('lng'))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Invalid coordinates'}, status=400)

        # Use GeoService to get generic places (Landmarks + Establishments if possible, or just Establishments)
        # Using get_nearby_establishments per previous implementation, but get_nearby_places might be better for general results.
        # Let's use get_nearby_establishments for "Services".
        places = geo_service.get_nearby_establishments(
            lat=lat,
            lon=lon,
            radius_km=20,
            limit=8  # Show 8 results via AJAX
        )
        
        # Calculate exact distances
        results = geo_service.calculate_distances_for_results(list(places), lat, lon)

        # JSON Response for API/Map
        if request.GET.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
            data = []
            for p in results:
                data.append({
                    'id': p.id,
                    'name': p.name,
                    'distance_km': round(p.exact_distance_km, 2) if p.exact_distance_km else 0,
                    'image': p.cover_image.url if p.cover_image else None,
                    'url': p.get_absolute_url(),
                    'category': p.category.name if p.category else ''
                })
            return JsonResponse({'status': 'success', 'places': data})
            
        # HTML Response for Partial (AJAX Injection)
        context = self.get_context_data()
        context['nearby_places'] = results
        return self.render_to_response(context)


class MapDataView(TemplateView):
    """
    API endpoint for Map Data using GeoService/Selectors.
    """
    def get(self, request):
        # Filtering
        category_id = request.GET.get('category')
        
        # Use Selector or direct filter
        qs = selectors.get_public_places_for_map()
        
        if category_id:
            qs = qs.filter(category_id=category_id)
            
        places = qs
        
        features = []
        for place in places:
            if place.latitude and place.longitude:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(place.longitude), float(place.latitude)]
                    },
                    "properties": {
                        "id": place.id,
                        "title": place.name,
                        "category": place.category.name if place.category else "Uncategorized",
                        "url": place.get_absolute_url(),
                        "image": place.cover_image.url if place.cover_image else None
                    }
                })
        
        return JsonResponse({
            "type": "FeatureCollection",
            "features": features
        })

class PlaceWeatherView(TemplateView):
    """
    API View to get weather forecast for a location.
    caching: 15 minutes
    """
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon') or request.GET.get('lng'))
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid coordinates'}, status=400)

        # Cache Key (rounded to 3 decimals ~100m)
        cache_key = f"weather_forecast_{round(lat, 3)}_{round(lon, 3)}"
        cached_data = cache.get(cache_key)

        
        if cached_data:
            return JsonResponse(cached_data)

        # Call External API
        try:
            from ibb_guide.infrastructure.external_apis import WeatherAPIClient
            client = WeatherAPIClient()
            result = client.get_forecast(lat, lon)
        except Exception as e:
            # Fallback will handle this
            print(f"Weather API Error: {e}")
            result = type('obj', (object,), {'success': False})
        
        if result.success:
            # Structure the data for the frontend
            data = result.data
            # Extract current (first item usually in forecast lists or separate call, 
            # but WeatherAPI forecast usually gives list. OpenWeatherMap 5 day/3 hour forecast returns list)
            # We'll parse the list to get daily max/min roughly
            
            parsed_data = {
                'success': True,
                'current': {
                    'temp': round(data['list'][0]['main']['temp']),
                    'condition': data['list'][0]['weather'][0]['description'],
                    'icon': data['list'][0]['weather'][0]['icon']
                },
                'forecast': []
            }
            
            # Simple aggregation for next days (taking noon point roughly)
            seen_dates = set()
            for item in data['list']:
                date_txt = item['dt_txt'].split(' ')[0]
                if date_txt not in seen_dates:
                    parsed_data['forecast'].append({
                        'date': date_txt,
                        'temp': round(item['main']['temp']),
                        'condition': item['weather'][0]['main'],
                        'icon': item['weather'][0]['icon']
                    })
                    seen_dates.add(date_txt)
                    if len(seen_dates) >= 5:
                        break
            
            # Set Cache
            cache.set(cache_key, parsed_data, timeout=60 * 15)  # 15 minutes
            
            return JsonResponse(parsed_data)
        else:
             # MOCK FALLBACK for Demo/Dev (if API key missing or erratic)
            import random
            from datetime import timedelta
            
            print(" ! Weather API failed, using Mock Data")
            mock_current = {
                'temp': random.randint(18, 26),
                'condition': 'مشمس غائم',
                'icon': '02d'
            }
            mock_forecast = []
            today = timezone.now().date()
            for i in range(5):
                d = today + timedelta(days=i)
                mock_forecast.append({
                    'date': d.strftime('%Y-%m-%d'),
                    'temp': random.randint(15, 28),
                    'condition': random.choice(['مشمس', 'غائم جزئياً', 'ممطر']),
                    'icon': random.choice(['01d', '02d', '09d'])
                })
            
            mock_data = {
                'success': True,
                'current': mock_current,
                'forecast': mock_forecast,
                'is_mock': True
            }
            return JsonResponse(mock_data)

class WeatherPageView(TemplateView):
    """
    User-facing Weather Page for Ibb City.
    """
    template_name = "places/weather.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Default Ibb City Coordinates
        context['default_lat'] = 13.9667
        context['default_lon'] = 44.1833
        return context
