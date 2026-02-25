from django import template

from cms.services.ui_builder import get_zone_items

register = template.Library()


@register.inclusion_tag('cms/render_zone.html', takes_context=True)
def render_zone(context, zone_slug: str, stage: str = None):
    """Render all visible components in a given zone.

    - Default stage: published
    - Preview: if ?preview=1 and user is staff -> draft
    - If stage is explicitly provided, draft is only allowed for staff.
    """
    request = context.get('request')
    resolved_stage = stage or 'published'

    if request and getattr(request, 'GET', None) is not None:
        if request.GET.get('preview') == '1' and getattr(getattr(request, 'user', None), 'is_staff', False):
            resolved_stage = 'draft'

    if resolved_stage == 'draft' and not getattr(getattr(request, 'user', None), 'is_staff', False):
        resolved_stage = 'published'

    items = get_zone_items(zone_slug, stage=resolved_stage)
    return {
        'items': items,
        'request': request,
        'stage': resolved_stage,
    }
