from django import forms
from .models import Establishment

class WizardBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional for draft mode
        for field in self.fields.values():
            field.required = False

class WizardBasicForm(WizardBaseForm):
    class Meta:
        model = Establishment
        fields = ['name', 'category', 'description', 'cover_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class WizardLocationForm(WizardBaseForm):
    class Meta:
        model = Establishment
        fields = ['latitude', 'longitude', 'address_text', 'directorate', 'road_condition', 'classification']
        widgets = {
            'address_text': forms.Textarea(attrs={'rows': 3}),
            'directorate': forms.Select(attrs={'class': 'form-select'}),
        }

class WizardHoursForm(WizardBaseForm):
    class Meta:
        model = Establishment
        fields = ['working_hours', 'is_open_now', 'opening_hours_text']
        widgets = {
            'working_hours': forms.Textarea(attrs={'rows': 3, 'class': 'd-none'}), # Hidden, controlled by JS widget
        }

    def clean_working_hours(self):
        data = self.cleaned_data.get('working_hours')
        if not data or data == '':
            return {}
        return data

class WizardAmenitiesForm(WizardBaseForm):
    class Meta:
        model = Establishment
        fields = ['amenities']
        widgets = {
            'amenities': forms.CheckboxSelectMultiple(),
        }

class WizardMediaForm(WizardBaseForm):
    """Media handled separately usually, but for form consistency."""
    # Media usually involves many-to-many or separate Gallery model.
    # If using PlaceMedia model, we might need a formset or AJAX uploader.
    # For now, let's just use cover_image? No, that's in Basic.
    # Maybe additional images?
    # If the step is "Media", it might be an AJAX uploader relying on 'file' input not bound to Establishment directly?
    # Or 'gallery' field?
    
    # User's error was specific about 'WizardMediaForm'.
    # In 'views_wizard.py', mapping says: 'media': {'form': WizardMediaForm, ...}
    # So we need it.
    
    class Meta:
        model = Establishment
        fields = [] # No direct fields on Establishment for gallery?
        # Maybe licenses? 
        fields = ['license_image', 'commercial_registry_image'] 
    
    # If we want a generic file field for gallery uploads not bound to model instance yet?
    # View handles it?
    # `places/views_wizard.py` logic: `form = FormClass(request.POST, request.FILES, instance=draft.establishment)`
    # If we add extra fields here, they won't be saved to establishment unless we handle them.
    
    # Let's add license images here as they are on Establishment model.

