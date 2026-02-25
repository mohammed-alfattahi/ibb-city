from django.views.generic import DetailView, ListView
from .models import StaticPage, GuideCard

class StandardPageView(DetailView):
    """
    Render a static page (About, Terms, Privacy, Transport) from DB.
    """
    model = None # We will use get_object
    template_name = 'pages/dynamic_page.html'
    context_object_name = 'page'
    
    def get_object(self):
        # getting slug from kwargs
        slug = self.kwargs.get('slug')
        obj, created = StaticPage.objects.get_or_create(
            slug=slug,
            defaults={'title': slug.replace('-', ' ').title(), 'content': '<p>Content coming soon.</p>'}
        )
        return obj

class GuideHubView(ListView):
    """
    View for the Main Guides Hub Page.
    Fetches dynamic GuideCards.
    """
    template_name = 'pages/guides.html'
    context_object_name = 'cards'
    
    def get_queryset(self):
        return GuideCard.objects.filter(is_active=True).order_by('order')
