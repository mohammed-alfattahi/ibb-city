class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(label="الاسم الأول", required=False)
    last_name = forms.CharField(label="اسم العائلة", required=False)
    email = forms.EmailField(label="البريد الإلكتروني", required=True)
    phone_number = forms.CharField(label="رقم الهاتف", required=False)
    profile_image = forms.ImageField(label="الصورة الشخصية", required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_image']
        help_texts = {
            'email': 'لن نشارك بريدك الإلكتروني مع أي جهة خارجية.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            'phone_number',
            'profile_image',
            Submit('submit', 'حفظ التغييرات', css_class='btn btn-primary w-100 mt-3 rounded-pill fw-bold')
        )
