from django.utils import timezone
from django.db import transaction
from django.db.models import Model
from django.db.models.query import QuerySet
from decimal import Decimal

from places.models import EstablishmentDraft, Establishment, PlaceMedia
from management.models import PendingChange, WizardStep

class DraftService:
    @staticmethod
    def _step_to_order(step) -> int:
        """Normalize wizard step into an integer order.

        URLs use the step key (e.g. 'basic'), while the Draft model stores an int.
        """
        if isinstance(step, int):
            return step

        if isinstance(step, str) and step:
            obj = WizardStep.objects.filter(key=step).first()
            if obj:
                return int(obj.order)

        # Fallback: keep draft progressing, but don't crash
        return 1

    @staticmethod
    def _json_safe(value):
        """Best-effort JSON serialization for draft storage."""
        if value is None:
            return None

        # Django model instance
        if isinstance(value, Model):
            return value.pk

        # QuerySet / M2M selections
        if isinstance(value, QuerySet):
            return [obj.pk for obj in value]

        # Decimals (Lat/Long)
        if isinstance(value, Decimal):
            return str(value)

        # Dates
        if hasattr(value, 'isoformat'):
            try:
                return value.isoformat()
            except Exception:
                pass

        # Files (UploadedFile/ImageFieldFile)
        if hasattr(value, 'name') and not isinstance(value, (str, bytes)):
            return str(value.name)

        if isinstance(value, (list, tuple)):
            return [DraftService._json_safe(v) for v in value]

        if isinstance(value, dict):
            return {k: DraftService._json_safe(v) for k, v in value.items()}

        return value

    
    @staticmethod
    def create_new_draft(user):
        """
        Creates a new draft for a new establishment.
        Ideally creates a placeholder Establishment if image upload is required immediately.
        """
        # Feature: Reuse existing empty drafts to prevent clutter
        # Look for drafts in 'draft' status where the establishment name is "New Establishment" (default)
        # and has no user modifications (checking if updated_at is close to created_at is hard, 
        # so we rely on the name and Draft status).
        
        # 1. Inspect existing drafts for this user
        existing_draft = EstablishmentDraft.objects.filter(
            user=user,
            is_create_mode=True,
            status='draft',
            establishment__name="New Establishment",
            establishment__approval_status='draft'
        ).order_by('-updated_at').first()
        
        if existing_draft:
            return existing_draft

        # 2. Create new if none found
        establishment = Establishment.objects.create(
            owner=user,
            name="New Establishment", # Placeholder
            approval_status='draft',
            is_active=False
        )
        
        draft = EstablishmentDraft.objects.create(
            user=user,
            establishment=establishment,
            is_create_mode=True,
            current_step=1
        )
        return draft

    @staticmethod
    def create_edit_draft(user, establishment):
        """Creates a draft from an existing establishment for editing."""
        # Check if draft already exists?
        existing = EstablishmentDraft.objects.filter(
            user=user, 
            establishment=establishment, 
            status='draft'
        ).first()
        
        if existing:
            return existing

        # Pre-fill data from establishment
        initial_data = {
            'name': establishment.name,
            'description': establishment.description,
            'category': establishment.category.id if establishment.category else None,
            # Add other fields
        }
        
        draft = EstablishmentDraft.objects.create(
            user=user,
            establishment=establishment,
            is_create_mode=False,
            data=initial_data,
            current_step=1
        )
        return draft

    @staticmethod
    def save_step(draft, step, data):
        """Updates draft data for a specific step.

        NOTE: wizard routes pass step *key* (string). We normalize to integer order.
        """
        step_order = DraftService._step_to_order(step)

        # Ensure dict exists
        if not draft.data:
            draft.data = {}

        # JSON-safe storage
        raw_data = data or {}
        safe_data = {k: DraftService._json_safe(v) for k, v in raw_data.items()}
        draft.data.update(safe_data)

        draft.current_step = max(int(draft.current_step or 1), int(step_order))
        
        # If 'create' mode, we might want to sync non-sensitive fields to Establishment immediately
        # to facilitate preview.
        # But 'name' etc should be in Draft JSON until submit? 
        # Actually for 'create' mode (status=draft), we can update Establishment directly for EVERYTHING.
        # PendingChange is only for APPROVED places.
        
        if draft.is_create_mode:
            # Sync to Establishment for preview using RAW values (keeps file fields intact).
            DraftService._sync_to_establishment(draft.establishment, raw_data)
        
        draft.save()
        return draft

    @staticmethod
    def _sync_to_establishment(establishment, data):
        """Helper to update establishment fields from data dict."""
        # Store M2M separately (requires establishment.save() first)
        m2m_payload = {}

        for field, value in (data or {}).items():
            if field == 'amenities':
                m2m_payload['amenities'] = value
                continue

            if not hasattr(establishment, field):
                continue

            # Handle ForeignKeys (store id)
            if field == 'category':
                if isinstance(value, Model):
                    value = value.pk
                setattr(establishment, 'category_id', value or None)
                continue

            setattr(establishment, field, value)

        establishment.save()

        # Apply M2M
        if 'amenities' in m2m_payload:
            try:
                ids = m2m_payload['amenities'] or []
                if isinstance(ids, (int, str)):
                    ids = [ids]
                establishment.amenities.set(list(ids))
            except Exception:
                # Never break wizard because of optional M2M
                pass

    @staticmethod
    def submit_draft(draft):
        """
        Finalizes the draft.
        New: Sets status=pending.
        Edit: Creates PendingChange for sensitive fields.
        """
        if draft.status == 'submitted':
            return False, "Already submitted"

        with transaction.atomic():
            est = draft.establishment
            
            if draft.is_create_mode:
                # Just change status to pending
                est.approval_status = 'pending'
                est.save()
                
                # Notify Office (TODO)
            else:
                # Edit Mode: Check sensitive fields
                sensitive_fields = ['name', 'description']
                for field in sensitive_fields:
                    new_val = draft.data.get(field)
                    old_val = getattr(est, field)
                    if new_val and new_val != old_val:
                        PendingChange.objects.create(
                            establishment=est,
                            field_name=field,
                            old_value=old_val,
                            new_value=new_val,
                            requested_by=draft.user,
                            status='pending'
                        )
                
                # Update non-sensitive fields immediately?
                # Or wait for approval?
                # Prompt says: "name (if sensitive => request via PendingChange)... main photo (allowed immediate)"
                # So we update non-sensitive now.
                # Logic to filter sensitive fields from sync:
                non_sensitive_data = {k:v for k,v in draft.data.items() if k not in sensitive_fields}
                DraftService._sync_to_establishment(est, non_sensitive_data)

            draft.status = 'submitted'
            draft.save()
            return True, "Draft submitted"
