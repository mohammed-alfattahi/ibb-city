from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from .models import PlaceComment

class PlaceCommentForm(forms.ModelForm):
    class Meta:
        model = PlaceComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'اكتب ردك هنا...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'content',
            Submit('submit', 'نشر الرد', css_class='btn btn-primary mt-2')
        )
