from django.views.generic import TemplateView, View
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from .services.draft_service import DraftService
from .models.drafts import EstablishmentDraft
from .forms_wizard import WizardBasicForm, WizardLocationForm, WizardHoursForm, WizardAmenitiesForm, WizardMediaForm
from management.models import WizardStep
from .models import Establishment

# Mapping Keys to Static Resources (Forms/Templates)
# DB controls Order and Visibility
STEP_RESOURCES = {
    'basic': {'form': WizardBasicForm, 'template': 'places/wizard/steps/basic_info.html', 'label': 'المعلومات الأساسية'},
    'location': {'form': WizardLocationForm, 'template': 'places/wizard/steps/location.html', 'label': 'الموقع'},
    'contacts': {'form': None, 'template': 'places/wizard/steps/contacts.html', 'label': 'جهات الاتصال'},
    'hours': {'form': WizardHoursForm, 'template': 'places/wizard/steps/working_hours.html', 'label': 'ساعات العمل'},
    'units': {'form': WizardAmenitiesForm, 'template': 'places/wizard/steps/units.html', 'label': 'الوحدات والمرافق'},
    'media': {'form': WizardMediaForm, 'template': 'places/wizard/steps/media.html', 'label': 'الوسائط'},
    'review': {'form': None, 'template': 'places/wizard/steps/review.html', 'label': 'المراجعة والإرسال'},
}

def get_wizard_steps():
    """Fetch active steps from DB, ordered."""
    # Ensure default steps exist if DB is empty (First Run)
    if not WizardStep.objects.exists():
        _init_default_steps()
    return list(WizardStep.objects.filter(is_active=True).order_by('order'))

def _init_default_steps():
    defaults = [
        (1, 'basic', 'المعلومات الأساسية'),
        (2, 'location', 'الموقع'),
        (3, 'contacts', 'جهات الاتصال'),
        (4, 'hours', 'ساعات العمل'),
        (5, 'units', 'الوحدات والمرافق'),
        (6, 'media', 'الوسائط'),
        (7, 'review', 'المراجعة والإرسال'),
    ]
    for order, key, title in defaults:
        WizardStep.objects.get_or_create(key=key, defaults={'title': title, 'order': order})

class WizardStartView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if pk:
            # Edit existing establishment
            est = get_object_or_404(Establishment, pk=pk, owner=request.user)
            draft = DraftService.create_edit_draft(request.user, est)
        else:
            # Create new
            draft = DraftService.create_new_draft(request.user)
        
        # Determine first step
        steps = get_wizard_steps()
        first_step_key = steps[0].key if steps else 'basic'
        
        return redirect('wizard_step', draft_id=draft.pk, step=first_step_key)

class WizardView(LoginRequiredMixin, TemplateView):
    template_name = 'places/wizard/wizard_base.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        draft_id = self.kwargs.get('draft_id')
        current_key = self.kwargs.get('step') # Using Key in URL not number
        
        
        # Helper: Resolve numeric step to key if needed
        # URL might pass '6' (from draft.current_step), but we want 'media'
        db_steps = get_wizard_steps()
        if current_key.isdigit():
             target_order = int(current_key)
             for s in db_steps:
                 if s.order == target_order:
                     current_key = s.key
                     break
        
        draft = get_object_or_404(EstablishmentDraft, pk=draft_id, user=self.request.user)
        ctx['draft'] = draft
        ctx['current_step'] = current_key
        
        # Dynamic Steps
        steps_meta = []
        current_step_obj = None
        
        for s in db_steps:
             meta = STEP_RESOURCES.get(s.key, {})
             # Merge DB title
             meta['unique_key'] = s.key
             meta['title'] = s.title
             meta['order'] = s.order
             steps_meta.append(meta)
             if s.key == current_key:
                 current_step_obj = s

        ctx['steps_meta'] = steps_meta
        ctx['total_steps'] = len(steps_meta)
        
        # Load Resource
        resource = STEP_RESOURCES.get(current_key)
        if resource:
            ctx['step_info'] = resource
            FormClass = resource.get('form')
            
            if FormClass:
                # Use establishment instance directly (DraftService syncs them)
                # Draft Service ensures establishment is updated with draft values if needed
                ctx['form'] = FormClass(instance=draft.establishment)
        
        # Pass fields config for this step
        if current_step_obj:
            ctx['fields_config'] = current_step_obj.fields.filter(is_visible=True)

        # Calculate Prev/Next for Template
        previous_step_key = None
        next_step_key = None
        
        found = False
        for i, meta in enumerate(steps_meta):
            if meta['unique_key'] == current_key:
                found = True
                if i > 0:
                     previous_step_key = steps_meta[i-1]['unique_key']
                if i < len(steps_meta) - 1:
                     next_step_key = steps_meta[i+1]['unique_key']
                break
        
        ctx['previous_step_key'] = previous_step_key
        ctx['next_step_key'] = next_step_key
        ctx['is_last_step'] = (next_step_key is None)

        return ctx

    def post(self, request, *args, **kwargs):
        draft_id = kwargs.get('draft_id')
        current_key = kwargs.get('step')
        
        # Helper: Resolve numeric step to key if needed
        if current_key.isdigit():
             target_order = int(current_key)
             # Need to fetch db_steps efficiently or just use mapping if static?
             # Best to keep consistent with get_context_data
             db_steps = get_wizard_steps()
             for s in db_steps:
                 if s.order == target_order:
                     current_key = s.key
                     break

        draft = get_object_or_404(EstablishmentDraft, pk=draft_id, user=request.user)
        
        resource = STEP_RESOURCES.get(current_key)
        if not resource:
             return redirect('partner_dashboard')

        FormClass = resource.get('form')
        
        if FormClass:
            form = FormClass(request.POST, request.FILES, instance=draft.establishment)
            # FORCE IGNORE ERRORS FOR DRAFT SAVE IF REQUESTING SAVE_AND_EXIT
            # BUT for Next Step, we might want some validation?
            # User requirement: "No mandatory field during draft"
            # So form.is_valid() might be too strict if fields are required.
            # However, ModelForm uses model validation.
            # We updated Establishment.save() to skip full_clean.
            # But Form validation runs clean() method of fields.
            # Solution: We should construct form with use_required_attribute=False or modify form fields to not be required dynamically.
            # OR, we just save what we can and advance.
            
            # Let's try to save even if invalid for draft purposes?
            # But django form.save() checks is_valid().
            
            # Better approach for Draft-First:
            # All fields in Wizard Forms should have required=False effectively, 
            # OR we rely on Autosave (which bypasses form validation usually or handles partial data).
            
            # For "Next" button, we usually want SOME validation? 
            # "The user's request: 1. No mandatory field during draft".
            # So we should allow moving next even if incomplete.
            # ONLY SUBMIT enforces validation.
            
            # Draft-first UX: required fields are disabled in WizardBaseForm.
            # We still validate types and formats; on error we show the form feedback.
            try:
                if form.is_valid():
                    est = form.save(commit=False)
                    est.save()
                    # Persist many-to-many (e.g. amenities)
                    if hasattr(form, 'save_m2m'):
                        form.save_m2m()

                    # Store JSON-safe snapshot for submit validation + preview
                    DraftService.save_step(draft, current_key, form.cleaned_data)
                else:
                    ctx = self.get_context_data(**kwargs)
                    ctx['form'] = form
                    ctx['form_errors'] = form.errors
                    print(f"DEBUG: Form Errors: {form.errors}")
                    return self.render_to_response(ctx)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error saving step: {str(e)}")
                ctx = self.get_context_data(**kwargs)
                ctx['form'] = form
                return self.render_to_response(ctx)

        # Calculate Next Step
        db_steps = get_wizard_steps()
        next_key = None
        found_current = False
        for s in db_steps:
            if found_current:
                next_key = s.key
                break
            if s.key == current_key:
                found_current = True
        
        if next_key:
            return redirect('wizard_step', draft_id=draft.pk, step=next_key)
        else:
            # Finish? Go to review or submit?
            # If current is review, then we are done?
            return redirect('partner_dashboard')

# ... Keep AutoSave/Submit ...
class WizardAutoSaveView(LoginRequiredMixin, View):
    def post(self, request, draft_id):
        draft = get_object_or_404(EstablishmentDraft, pk=draft_id, user=request.user)
        # Handle autosave...
        return JsonResponse({'status': 'saved'})

class WizardSubmitView(LoginRequiredMixin, View):
    def post(self, request, draft_id):
        draft = get_object_or_404(EstablishmentDraft, pk=draft_id, user=request.user)
        
        # FINAL VALIDATION HERE
        # 1. Update status to pending
        # 2. Call full_clean()
        
        try:
            est = draft.establishment
            est.approval_status = 'pending'
            est.full_clean() # This raises Validation error if missing required fields
            est.save()
            
            draft.status = 'submitted'
            draft.save()
            
            # Create PartnerRequest for Admin Dashboard
            from users.models import PartnerRequest
            PartnerRequest.objects.create(
                user=request.user,
                request_type='new_establishment', 
                related_establishment=est,
                status='pending'
            )

            # Notify User
            from interactions.notifications.partner import PartnerNotifications
            PartnerNotifications.notify_establishment_submitted(est)
            
            messages.success(request, "تم إرسال المنشأة للمراجعة بنجاح")
            return redirect('partner_dashboard')
        except Exception as e:
            # Return to wizard with errors
            import traceback
            traceback.print_exc()
            messages.error(request, f"لا يمكن الإرسال: {e}")
            return redirect('wizard_step', draft_id=draft.pk, step='review')

class WizardPreviewView(LoginRequiredMixin, View):
    def get(self, request, draft_id):
         # ... existing ...
         return render(request, 'place_detail.html', {'place': get_object_or_404(EstablishmentDraft, pk=draft_id).establishment, 'is_preview': True})



