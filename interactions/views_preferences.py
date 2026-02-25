"""
Notification Preferences API Endpoints
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
import json


@login_required
@require_http_methods(["GET"])
def get_preferences(request):
    """
    GET /notifications/api/preferences/
    Returns the user's notification preferences.
    """
    from interactions.models import NotificationPreference
    
    prefs = NotificationPreference.get_or_create_for_user(request.user)
    
    return JsonResponse({
        'enable_all': prefs.enable_all,
        'enable_push': prefs.enable_push,
        'enable_email': prefs.enable_email,
        'enable_sms': prefs.enable_sms,
        'disabled_categories': prefs.disabled_categories,
        'disabled_types': prefs.disabled_types,
        'quiet_hours': {
            'enabled': prefs.quiet_hours_enabled,
            'start': prefs.quiet_start.strftime('%H:%M') if prefs.quiet_start else None,
            'end': prefs.quiet_end.strftime('%H:%M') if prefs.quiet_end else None,
        },
        'categories': [
            {'key': key, 'label': label} 
            for key, label in NotificationPreference.CATEGORY_CHOICES
        ]
    })


@login_required
@csrf_protect
@require_http_methods(["POST", "PATCH"])
def update_preferences(request):
    """
    PATCH /notifications/api/preferences/
    Updates the user's notification preferences.
    
    Body (JSON):
    {
        "enable_all": true,
        "enable_push": true,
        "enable_email": false,
        "disabled_categories": ["ads", "promotions"],
        "quiet_hours": {"enabled": true, "start": "22:00", "end": "08:00"}
    }
    """
    from interactions.models import NotificationPreference
    from datetime import datetime
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    prefs = NotificationPreference.get_or_create_for_user(request.user)
    
    def parse_bool(v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'on', 'yes')
        return bool(v)

    # Update boolean fields
    if 'enable_all' in data:
        prefs.enable_all = parse_bool(data['enable_all'])
    if 'enable_push' in data:
        prefs.enable_push = parse_bool(data['enable_push'])
    if 'enable_email' in data:
        prefs.enable_email = parse_bool(data['enable_email'])
    if 'enable_sms' in data:
        prefs.enable_sms = parse_bool(data['enable_sms'])
    
    # Update JSON fields
    if 'disabled_categories' in data:
        vals = data['disabled_categories']
        if isinstance(vals, str): # Handle form data list if passed as string (unlikely but possible)
            try:
                vals = json.loads(vals)
            except:
                pass 
        if isinstance(vals, (list, dict)):
            prefs.disabled_categories = vals

    if 'disabled_types' in data:
        vals = data['disabled_types']
        if isinstance(vals, (list, dict)):
            prefs.disabled_types = vals
    
    # Update quiet hours
    # (JSON logic kept, adapting for form data only if keys are flattened like quiet_hours.enabled)
    # For now, simplistic handling or assume JSON for complex objects.
    if 'quiet_hours' in data and isinstance(data['quiet_hours'], dict):
        qh = data['quiet_hours']
        prefs.quiet_hours_enabled = bool(qh.get('enabled', False))
        if qh.get('start'):
            try:
                prefs.quiet_start = datetime.strptime(qh['start'], '%H:%M').time()
            except ValueError:
                pass
        if qh.get('end'):
            try:
                prefs.quiet_end = datetime.strptime(qh['end'], '%H:%M').time()
            except ValueError:
                pass
    
    prefs.save()
    
    if request.headers.get('HX-Request'):
        # Return a toast message via OOB or simple script
        # Assuming we have a toast container or just use alert for now?
        # Better: use a small invisible div with hx-swap-oob to a message container.
        # But for switches, we don't need much feedback other than it stayed switched.
        # Maybe a small "Saved" toast?
        from django.contrib import messages
        messages.success(request, 'تم حفظ التفضيلات')
        # Render a toast partial if possible. 
        # For now, return empty 200, but adding a header for client side toast if implemented.
        response = JsonResponse({'status': 'ok', 'message': 'Saved'})
        response['HX-Trigger'] = 'showToast' # Example trigger
        return response

    return JsonResponse({'status': 'ok', 'message': 'تم حفظ التفضيلات'})
