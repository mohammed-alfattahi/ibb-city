from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import Establishment, EstablishmentUnit

class EstablishmentUnitForm(forms.ModelForm):
    class Meta:
        model = EstablishmentUnit
        fields = ['name', 'unit_type', 'price', 'description', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_price(self):
        """Gap 4.B.2 fix: Validate price is non-negative."""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("السعر لا يمكن أن يكون سالباً")
        return price

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('unit_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'price',
            'description',
            'image',
            Submit('submit', 'Save Unit', css_class='btn btn-primary mt-3')
        )


from .models import Establishment, EstablishmentUnit, PlaceMedia

class PlaceMediaForm(forms.ModelForm):
    class Meta:
        model = PlaceMedia
        fields = ['media_url', 'is_cover']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'media_url',
            'is_cover',
            Submit('submit', 'Upload Image', css_class='btn btn-success')
        )


class EstablishmentForm(forms.ModelForm):
    class Meta:
        model = Establishment
        # Bug 3.2 fix: is_active removed - partner cannot self-activate
        fields = [
            'name', 'category', 'description',
            'cover_image', 'latitude', 'longitude', 
            'license_image', 'commercial_registry_image',
            'contact_info', 'working_hours', 'amenities',
            'operational_status', 'status_note', 'is_open_now',
            'opening_hours_text'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'contact_info': forms.HiddenInput(),
            'working_hours': forms.Textarea(attrs={'rows': 3, 'placeholder': '{"open": "..."}'}),
            'amenities': forms.CheckboxSelectMultiple(),
            'license_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'commercial_registry_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'operational_status': forms.Select(attrs={'class': 'form-select'}),
            'status_note': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional note about the status (e.g., specific closure dates)'}),
        }
    
    new_amenities = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Add new features separated by commas (e.g., Free WiFi, Parking)'}),
        label="Add New Features"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Gap 2.4 fix: Make license docs required for new establishments
        if not self.instance.pk:  # Only on create
            if 'license_image' in self.fields:
                self.fields['license_image'].required = True
            if 'commercial_registry_image' in self.fields:
                self.fields['commercial_registry_image'].required = True
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('latitude', css_class='form-group col-md-6 mb-0'),
                Column('longitude', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            HTML("<p class='text-muted small'>حدد موقع منشأتك على الخريطة أو أدخل الإحداثيات يدوياً.</p>"),
            HTML('<div id="map-picker"></div>'),
            
            HTML("<div class='section-header mt-4'>المستندات الرسمية (مطلوبة)</div>"),
            Row(
                Column('license_image', css_class='form-group col-md-6'),
                Column('commercial_registry_image', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            
            'cover_image',
            
            # Custom UI for Contact Info
            HTML("""
                <div class="mb-3">
                    <label class="form-label">Phone Numbers & Contact Methods</label>
                    <div id="contact-info-container">
                        <!-- JS will inject rows here -->
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-secondary mt-2" id="add-phone-btn">
                        <i class="fas fa-plus"></i> Add Number
                    </button>
                </div>
            """),
            'contact_info', # This is now hidden
            
            'working_hours',
            'amenities',
            
            HTML("<div class='section-header mt-4'>Operational Status</div>"),
            Row(
                Column('is_open_now', css_class='form-group col-md-4'),
                Column('operational_status', css_class='form-group col-md-4'),
                css_class='form-row align-items-center'
            ),
            'status_note',
            
            Submit('submit', 'Save Establishment', css_class='btn btn-primary mt-3')
        )

from .models import SpecialOffer

class SpecialOfferForm(forms.ModelForm):
    class Meta:
        model = SpecialOffer
        fields = ['title', 'description', 'old_price', 'new_price', 'image', 'start_date', 'end_date', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        new_p = cleaned_data.get('new_price')
        old_p = cleaned_data.get('old_price')

        if start and end and start >= end:
            raise forms.ValidationError("تاريخ النهاية يجب أن يكون بعد تاريخ البداية.")
            
        if old_p and new_p and new_p >= old_p:
             raise forms.ValidationError("سعر العرض يجب أن يكون أقل من السعر القديم.")
             
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            Row(
                Column('old_price', css_class='form-group col-md-6 mb-0'),
                Column('new_price', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'image',
            'is_active',
            Submit('submit', 'حفظ العرض', css_class='btn btn-primary mt-3')
        )
