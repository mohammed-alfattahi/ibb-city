from management.services.audit_service import AuditService
from django.forms.models import model_to_dict

class AuditMixin:
    """
    Mixin to automatically log model changes.
    Requires the view/context to set `_current_user` on the instance before saving,
    OR use a middleware to set a global user (not recommended for simple apps).
    
    Usage:
        obj._current_user = request.user
        obj.save()
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store initial state
        if self.pk:
            self._initial_state = self._get_state_dict()
        else:
            self._initial_state = {}

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Call standard save
        super().save(*args, **kwargs)
        
        # Log Logic
        user = getattr(self, '_current_user', None)
        reason = getattr(self, '_audit_reason', "")
        
        if user:
            new_state = self._get_state_dict()
            action = 'CREATE' if is_new else 'UPDATE'
            
            AuditService.log(
                actor=user,
                action=action,
                target_model=self,
                target_id=self.pk,
                old_data=self._initial_state if not is_new else None,
                new_data=new_state,
                reason=reason
            )
            
            # Update initial state for next save
            self._initial_state = new_state

    def delete(self, *args, **kwargs):
        user = getattr(self, '_current_user', None)
        reason = getattr(self, '_audit_reason', "")
        old_state = self._get_state_dict()
        pk = self.pk
        
        super().delete(*args, **kwargs)
        
        if user:
            AuditService.log(
                actor=user,
                action='DELETE',
                target_model=self,
                target_id=pk,
                old_data=old_state,
                new_data=None,
                reason=reason
            )

    def _get_state_dict(self):
        """Helper to serialize model state."""
        # Simple serialization
        try:
            return model_to_dict(self)
        except Exception:
            return {}
