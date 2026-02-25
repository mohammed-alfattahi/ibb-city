from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import Event, Season
from django.db.models import Q

class EventListView(ListView):
    model = Event
    template_name = 'events/list.html'
    context_object_name = 'events'
    ordering = ['start_datetime']

    def get_queryset(self):
        queryset = super().get_queryset()
        now = timezone.now()
        
        # Default: Show future events
        queryset = queryset.filter(end_datetime__gte=now)
        
        # Search Filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Type Filter (e.g., ?type=festival)
        event_type = self.request.GET.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Date Filter
        date_filter = self.request.GET.get('date')
        if date_filter == 'today':
            queryset = queryset.filter(start_datetime__date=now.date())
        elif date_filter == 'week':
            from datetime import timedelta
            week_end = now + timedelta(days=7)
            queryset = queryset.filter(start_datetime__lte=week_end)
        elif date_filter == 'month':
            from datetime import timedelta
            month_end = now + timedelta(days=30)
            queryset = queryset.filter(start_datetime__lte=month_end)
        
        # Featured Filter
        featured = self.request.GET.get('featured')
        if featured:
            queryset = queryset.filter(is_featured=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Defensive: Season table might not exist
        try:
            context['current_season'] = Season.objects.filter(
                start_date__lte=now.date(), 
                end_date__gte=now.date(), 
                is_active=True
            ).first()
        except Exception:
            context['current_season'] = None
        
        context['featured_events'] = Event.objects.filter(
            is_featured=True, 
            end_datetime__gte=now
        ).order_by('start_datetime')[:5]
        
        return context

class EventDetailView(DetailView):
    model = Event
    template_name = 'events/detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Suggest related events in the same season or by type
        context['related_events'] = Event.objects.filter(
            end_datetime__gte=timezone.now()
        ).exclude(pk=self.object.pk)[:3]
        return context

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import EventForm

class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    success_url = reverse_lazy('events:list')

    def form_valid(self, form):
        # Optional: Set owner if Event model had an owner field.
        # Currently Event model doesn't have an owner field in the snippet I saw.
        # Assuming staff/admin or specific permission logic.
        # For now, just save.
        messages.success(self.request, "تم إنشاء الفعالية بنجاح")
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    
    def get_success_url(self):
        return reverse_lazy('events:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "تم تحديث الفعالية بنجاح")
        return super().form_valid(form)

class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/confirm_delete.html'
    success_url = reverse_lazy('events:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "تم حذف الفعالية بنجاح")
        return super().delete(request, *args, **kwargs)

