
# ============================================
# Dynamic Content Pages (Culture & Emergency)
# ============================================
from django.views.generic import TemplateView
from .models import PublicEmergencyContact, SafetyGuideline, CulturalLandmark

class EmergencyPageView(TemplateView):
    template_name = 'pages/emergency.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_contacts = PublicEmergencyContact.objects.filter(is_active=True).order_by('order', 'title')
        
        # Split contacts
        context['primary_contacts'] = all_contacts.filter(is_primary_card=True)
        context['hospitals'] = all_contacts.filter(is_hospital=True)
        
        # Safety guidelines
        context['safety_guidelines'] = SafetyGuideline.objects.filter(is_active=True).order_by('order')
        return context

class CulturePageView(TemplateView):
    template_name = 'pages/culture.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cultural_landmarks'] = CulturalLandmark.objects.filter(is_active=True).order_by('order', '-created_at')
        return context
