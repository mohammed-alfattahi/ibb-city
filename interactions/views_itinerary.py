"""
Itinerary Views - Operation 6B
جدول الرحلات (خطط السفر)
"""
from django.views.generic import ListView, DetailView, CreateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django import forms

from .models import Itinerary, ItineraryItem
from .services.itinerary_service import ItineraryService
from places.models import Place


class ItineraryForm(forms.ModelForm):
    """Form for creating a new itinerary."""
    class Meta:
        model = Itinerary
        fields = ['title', 'start_date', 'duration_days']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ItineraryListView(ListView):
    """List itineraries — user's own (if logged in) + public ones."""
    model = Itinerary
    template_name = 'interactions/itinerary_list.html'
    context_object_name = 'itineraries'
    
    def get_queryset(self):
        from django.db.models import Q
        if self.request.user.is_authenticated:
            # Show user's own itineraries + public ones from others
            return Itinerary.objects.filter(
                Q(user=self.request.user) | Q(is_public=True)
            ).order_by('-created_at')
        # Anonymous: show only public itineraries
        return Itinerary.objects.filter(is_public=True).order_by('-created_at')


class ItineraryCreateView(LoginRequiredMixin, CreateView):
    """Create a new itinerary."""
    model = Itinerary
    form_class = ItineraryForm
    template_name = 'interactions/itinerary_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, f"تم إنشاء خطة '{form.instance.title}' بنجاح!")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('itinerary_detail', kwargs={'pk': self.object.pk})


class ItineraryDetailView(DetailView):
    """View itinerary details with items grouped by day."""
    model = Itinerary
    template_name = 'interactions/itinerary_detail.html'
    context_object_name = 'itinerary'
    
    def get_queryset(self):
        from django.db.models import Q
        # Owner sees their own; anyone can view public itineraries
        if self.request.user.is_authenticated:
            return Itinerary.objects.filter(
                Q(user=self.request.user) | Q(is_public=True)
            )
        return Itinerary.objects.filter(is_public=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.object.items.select_related('place').all()
        
        # Group items by day — ensure ALL days are represented (even empty ones)
        from collections import defaultdict
        days = defaultdict(list)
        # Pre-populate all days so the template always renders day cards with "Add Place" buttons
        for d in range(1, self.object.duration_days + 1):
            days[d]  # Touch key to ensure it exists
        for item in items:
            days[item.day_number].append(item)
        
        # Convert to sorted list of tuples
        context['days'] = sorted(days.items())
        context['all_places'] = Place.objects.filter(is_active=True)[:50]  # For add modal
        context['is_owner'] = (
            self.request.user.is_authenticated and self.object.user == self.request.user
        )
        return context


class ItineraryPlaceSearchView(LoginRequiredMixin, View):
    """Search places for itinerary modal."""
    
    def get(self, request):
        query = request.GET.get('q', '')
        itinerary_pk = request.GET.get('itinerary_pk')
        
        places = Place.objects.filter(is_active=True)
        if query:
            places = places.filter(name__icontains=query)
        
        places = places[:20] # Limit results
        
        context = {'places': places}
        
        # Pass itinerary for URL generation in template
        if itinerary_pk:
            try:
                context['itinerary'] = Itinerary.objects.get(pk=itinerary_pk, user=request.user)
            except (Itinerary.DoesNotExist, ValueError):
                # If ID is invalid or not found, we just don't pass the itinerary
                # The template will hide the "Add" button
                pass
        
        from django.shortcuts import render
        return render(request, 'interactions/partials/itinerary_place_results.html', context)


class ItineraryAddItemView(LoginRequiredMixin, View):
    """Add a place to an itinerary day."""
    
    def post(self, request, pk, place_pk):
        itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
        place = get_object_or_404(Place, pk=place_pk)
        
        day_number = int(request.POST.get('day_number', 1))
        notes = request.POST.get('notes', '')
        
        if day_number < 1 or day_number > itinerary.duration_days:
            if request.headers.get('HX-Request'):
                 return JsonResponse({'error': 'Invalid day'}, status=400)
            messages.error(request, "رقم اليوم غير صحيح.")
            return redirect('itinerary_detail', pk=pk)
        
        ItineraryService.add_place_to_day(itinerary, place, day_number, notes=notes)
        
        if request.headers.get('HX-Request'):
            from django.shortcuts import render
            # Re-fetch items for this day to render the updated list/card
            items = itinerary.items.filter(day_number=day_number).select_related('place').order_by('order')
            
            # We return the specific day's list OOB
            from django.template.loader import render_to_string
            content = render_to_string('interactions/partials/itinerary_day_body.html', {
                'items': items,
                'is_owner': True
            })
            
            from django.http import HttpResponse
            return HttpResponse(f'<div id="day-{day_number}-body" hx-swap-oob="innerHTML">{content}</div>')

        messages.success(request, f"تمت إضافة '{place.name}' لليوم {day_number}")
        return redirect('itinerary_detail', pk=pk)


class ItineraryItemDeleteView(LoginRequiredMixin, View):
    """Delete an item from itinerary."""
    
    def post(self, request, item_pk):
        item = get_object_or_404(ItineraryItem, pk=item_pk, itinerary__user=request.user)
        itinerary_pk = item.itinerary.pk
        place_name = item.place.name
        item.delete()
        if request.headers.get('HX-Request'):
            from django.http import HttpResponse
            # Return 200 OK to trigger DOM removal
            return HttpResponse("")

        messages.success(request, f"تم حذف '{place_name}' من الخطة.")
        return redirect('itinerary_detail', pk=itinerary_pk)


class ItineraryTogglePublicView(LoginRequiredMixin, View):
    """Toggle public visibility of itinerary."""
    
    def post(self, request, pk):
        itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
        itinerary.is_public = not itinerary.is_public
        itinerary.save(update_fields=['is_public'])
        
        if request.headers.get('HX-Request'):
            from django.shortcuts import render
            return render(request, 'interactions/partials/itinerary_public_toggle.html', {
                'itinerary': itinerary
            })

        status = "عامة" if itinerary.is_public else "خاصة"
        messages.success(request, f"الخطة الآن {status}.")
        return redirect('itinerary_detail', pk=pk)


class ItineraryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an entire itinerary."""
    model = Itinerary
    template_name = 'interactions/itinerary_confirm_delete.html'
    success_url = reverse_lazy('itinerary_list')
    
    def get_queryset(self):
        return Itinerary.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "تم حذف الخطة بنجاح.")
        return super().delete(request, *args, **kwargs)


class PublicItineraryView(DetailView):
    """Public view of a shared itinerary (no login required)."""
    model = Itinerary
    template_name = 'interactions/itinerary_public.html'
    context_object_name = 'itinerary'
    
    def get_queryset(self):
        return Itinerary.objects.filter(is_public=True)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.object.items.select_related('place').all()
        
        from collections import defaultdict
        days = defaultdict(list)
        for item in items:
            days[item.day_number].append(item)
        
        context['days'] = sorted(days.items())
        return context


class ItineraryReorderItemsView(LoginRequiredMixin, View):
    """Reorder itinerary items via AJAX."""
    
    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            item_ids = data.get('item_ids', [])
            
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No items provided'}, status=400)

            # verify ownership implicitly by filtering
            items = ItineraryItem.objects.filter(
                pk__in=item_ids, 
                itinerary__user=request.user
            )
            
            # Create a map for O(1) lookup
            item_map = {str(item.pk): item for item in items}
            
            # Update order
            for index, item_id in enumerate(item_ids, start=1):
                if str(item_id) in item_map:
                    item = item_map[str(item_id)]
                    item.order = index
                    # Note: saving in loop is not ideal for large lists, but fine for small itineraries
                    item.save(update_fields=['order'])
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
