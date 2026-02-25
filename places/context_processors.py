"""
Partner Context Processors

Provides common data for partner templates, including the selected establishment
for dynamic sidebar navigation.
"""
from places.models import Establishment


def partner_context(request):
    """
    Provide common partner data to all templates.
    
    - selected_establishment: The establishment being viewed/edited, or the first one if none selected
    """
    context = {}
    
    if not request.user.is_authenticated:
        return context
    
    # Check if we're on a partner page with an establishment
    # Try to get establishment from URL kwargs or session
    establishment_pk = None
    
    # Check URL patterns for establishment pk
    if hasattr(request, 'resolver_match') and request.resolver_match:
        # Different URL patterns use different kwarg names
        establishment_pk = (
            request.resolver_match.kwargs.get('pk') or
            request.resolver_match.kwargs.get('place_pk')
        )
    
    try:
        if establishment_pk:
            # Verify ownership and get establishment
            establishment = Establishment.objects.filter(
                pk=establishment_pk,
                owner=request.user
            ).first()
            if establishment:
                context['selected_establishment'] = establishment
                # Store in session for persistence
                request.session['selected_establishment_pk'] = establishment.pk
        else:
            # Try session fallback
            session_pk = request.session.get('selected_establishment_pk')
            if session_pk:
                establishment = Establishment.objects.filter(
                    pk=session_pk,
                    owner=request.user
                ).first()
                if establishment:
                    context['selected_establishment'] = establishment
    except Exception:
        # Silently fail - don't break the page
        pass
    
    return context
