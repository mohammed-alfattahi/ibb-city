from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from .models import Review, PlaceComment
from .forms import PlaceCommentForm
from places.models import Establishment

class PartnerReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = 'partners/review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        # Get all establishments owned by the user
        user_places = Establishment.objects.filter(owner=self.request.user)
        # Return reviews for these places, ordered by newest first
        return Review.objects.filter(place__in=user_places).order_by('-created_at')

class PartnerReviewReplyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PlaceComment
    form_class = PlaceCommentForm
    template_name = 'partners/review_reply_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.review = get_object_or_404(Review, pk=self.kwargs['review_pk'])

    def test_func(self):
        # Ensure the user owns the place related to the review
        try:
            establishment = self.review.place.establishment
            return establishment.owner == self.request.user
        except Establishment.DoesNotExist:
            return False

    def form_valid(self, form):
        # Create a comment linked to the place and the review
        form.instance.place = self.review.place
        form.instance.user = self.request.user
        form.instance.review = self.review 
        self.object = form.save()
        
        if self.request.headers.get('HX-Request'):
             from django.template.loader import render_to_string
             from django.http import HttpResponse
             content = render_to_string('interactions/partials/review_reply.html', {'reply': self.object})
             # Append to the replies container for this review
             return HttpResponse(f'<div id="review-{self.review.pk}-replies" hx-swap-oob="beforeend">{content}</div>')
             
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('partner_review_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review'] = self.review
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review'] = self.review
        return context
