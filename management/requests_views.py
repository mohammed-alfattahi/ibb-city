from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Request

class PartnerRequestListView(LoginRequiredMixin, ListView):
    model = Request
    template_name = 'partners/requests/list.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        return Request.objects.filter(user=self.request.user).order_by('-created_at')

class PartnerRequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = 'partners/requests/detail.html'
    context_object_name = 'req'

    def get_queryset(self):
        # Ensure user can only see their own requests
        return Request.objects.filter(user=self.request.user)
