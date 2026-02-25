from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.apps import apps
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

@staff_member_required
@require_POST
def toggle_boolean_field(request):
    """
    Generic view to toggle a boolean field on any model.
    """
    app_label = request.POST.get('app_label')
    model_name = request.POST.get('model_name')
    object_id = request.POST.get('object_id')
    field_name = request.POST.get('field_name')
    value = request.POST.get('value') # 'true' or 'false'

    if not all([app_label, model_name, object_id, field_name]):
        return JsonResponse({'success': False, 'error': 'Missing parameters'})

    try:
        model = apps.get_model(app_label, model_name)
        obj = model.objects.get(pk=object_id)
        
        # Check permissions (basic check)
        # Ideally check has_change_permission on the ModelAdmin
        if not request.user.has_perm(f'{app_label}.change_{model_name}'):
             raise PermissionDenied
             
        # Verify the field is boolean
        field = model._meta.get_field(field_name)
        if field.get_internal_type() not in ('BooleanField', 'NullBooleanField'):
            return JsonResponse({'success': False, 'error': 'Not a boolean field'})
            
        # Update
        new_value = (value == 'true')
        setattr(obj, field_name, new_value)
        obj.save(update_fields=[field_name])
        
        return JsonResponse({'success': True, 'new_value': new_value})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
