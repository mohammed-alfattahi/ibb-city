from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_datetime', 'end_datetime', 'cover_image', 'event_type', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الفعالية'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'وصف تفصيلي للفعالية'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الموقع'}),
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'السعر (0 = مجاني)'}),
        }
        labels = {
            'title': 'عنوان الفعالية',
            'description': 'الوصف',
            'location': 'المكان',
            'start_datetime': 'تبدأ في',
            'end_datetime': 'تنتهي في',
            'cover_image': 'صورة الغلاف',
            'event_type': 'نوع الفعالية',
            'price': 'سعر التذكرة',
        }
