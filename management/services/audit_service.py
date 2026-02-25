from management.models import AuditLog
from django.core.serializers.json import DjangoJSONEncoder
import json

class AuditService:
    """
    Central Service for Audit Logging.
    Captures actions and computes data diffs.
    """

    @staticmethod
    def log(actor, action, target_model, target_id, old_data=None, new_data=None, reason="", request=None):
        """
        Log an action to the database.
        
        Args:
            actor: User instance performing the action
            action: Str (CREATE, UPDATE, DELETE, etc.)
            target_model: Str (Model Name) or Model Class
            target_id: PK of target
            old_data: Dict of values before format
            new_data: Dict of values after format
            reason: Optional justification
            request: Optional Django Request object to extract IP/UA
        """
        
        diff = AuditService._compute_diff(old_data, new_data)
        
        ip = AuditService._get_client_ip(request) if request else None
        ua = request.META.get('HTTP_USER_AGENT', '')[:200] if request else ''

        AuditLog.objects.create(
            user=actor,
            action=action,
            table_name=str(target_model._meta.verbose_name) if hasattr(target_model, '_meta') else str(target_model),
            record_id=str(target_id),
            diff=diff,
            old_values=old_data,
            new_values=new_data,
            reason=reason,
            ip_address=ip,
            user_agent=ua
        )

    @staticmethod
    def _compute_diff(old, new):
        """Calculate simplified diff: {field: {old: x, new: y}}"""
        if not old or not new:
            return {}
        
        diff = {}
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            val_old = old.get(key)
            val_new = new.get(key)
            if val_old != val_new:
                diff[key] = {'old': val_old, 'new': val_new}
        return diff

    @staticmethod
    def _get_client_ip(request):
        if not request: return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
