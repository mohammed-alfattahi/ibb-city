import csv
import json
from django.http import HttpResponse
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

def export_as_csv(modeladmin, request, queryset):
    """
    Generic CSV export action for Django Admin with Arabic support
    """
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta.object_name}_export_{timezone.now().strftime("%Y%m%d")}.csv'
    
    # Add BOM for Excel compatibility with Arabic
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)
    writer.writerow(field_names)

    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            if hasattr(value, 'strftime'):
                value = value.strftime('%Y-%m-%d %H:%M')
            elif value is None:
                value = ''
            
            # Handle list/dict for CSV
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
                
            row.append(str(value))
        writer.writerow(row)

    return response

export_as_csv.short_description = "📂 تصدير المحدد إلى CSV"


def export_as_json(modeladmin, request, queryset):
    """
    Generic JSON export action
    """
    meta = modeladmin.model._meta
    data = []
    
    for obj in queryset:
        item = {}
        for field in meta.fields:
            value = getattr(obj, field.name)
            if hasattr(value, 'file'):
                value = value.url if value else None
            item[field.name] = value
        data.append(item)
        
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename={meta.object_name}_export_{timezone.now().strftime("%Y%m%d")}.json'
    
    json.dump(data, response, cls=DjangoJSONEncoder, indent=4, ensure_ascii=False)
    return response

export_as_json.short_description = "📄 تصدير المحدد إلى JSON"
