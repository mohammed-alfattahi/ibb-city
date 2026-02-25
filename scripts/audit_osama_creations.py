import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from management.models import AuditLog
from django.contrib.auth import get_user_model
from places.models import Place, Establishment

User = get_user_model()
try:
    u = User.objects.get(username='osama')
    print(f"DEBUG: Auditing for user: {u.username} (ID: {u.id})")
    
    # 1. Search AuditLog for CREATE actions by osama in places table
    logs = AuditLog.objects.filter(user=u, action__icontains='CREATE', table_name__icontains='place')
    print(f"\nCreation Logs for {u.username} in 'places':")
    for log in logs:
        print(f"{log.timestamp} | {log.action} | {log.table_name} | Record ID:{log.record_id} | Values:{log.new_values}")
        
    # 2. Check if those record IDs still exist
    print("\nVerifying existing records from logs:")
    for log in logs:
        rid = log.record_id
        try:
            p = Place.objects.get(pk=rid)
            is_est = Establishment.objects.filter(pk=rid).exists()
            print(f"ID:{rid} | Exists: Yes | Type:{'Establishment' if is_est else 'Place'} | Name:{p.name}")
        except Place.DoesNotExist:
            print(f"ID:{rid} | Exists: No (DELETED)")

except Exception as e:
    import traceback
    traceback.print_exc()
