import django_filters
from django import forms
from django.db.models import Q
from .models import Place, Category, Amenity

class PlaceFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_search',
        label='البحث',
        widget=forms.TextInput
    )
    
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        empty_label="كل التصنيفات",
        widget=forms.Select
    )
    
    city = django_filters.ChoiceFilter(
        field_name='directorate',
        choices=Place.DIRECTORATE_CHOICES, 
        widget=forms.Select,
        label='المدينة/المديرية',
        empty_label="كل المديريات"
    )
    
    sort = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'latest'),
            ('avg_rating', 'top_rated'),
            ('view_count', 'most_viewed'),
        ),
        field_labels={
            'latest': 'الأحدث',
            'top_rated': 'الأعلى تقييماً',
            'most_viewed': 'الأكثر مشاهدة',
        },
        widget=forms.Select
    )

    price_min = django_filters.NumberFilter(method='filter_price_min', label='أقل سعر')
    price_max = django_filters.NumberFilter(method='filter_price_max', label='أعلى سعر')
    min_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='gte', label='أقل تقييم')
    
    amenities = django_filters.ModelMultipleChoiceFilter(
        queryset=Amenity.objects.all(),
        field_name='establishment__amenities',
        label='الخدمات',
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply consistent styling to widgets
        if 'q' in self.form.fields:
            self.form.fields['q'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'البحث عن اسم أو وصف...'
            })
        for field_name in ('category', 'city', 'sort'):
            field = self.form.fields.get(field_name)
            if field:
                field.widget.attrs.update({'class': 'form-select'})
        amenities_field = self.form.fields.get('amenities')
        if amenities_field:
            amenities_field.widget.attrs.update({'class': 'form-check-input'})

    class Meta:
        model = Place
        # amenities must NOT be here if it's not a model field on Place
        fields = ['category', 'classification', 'road_condition', 'price_range']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

    def filter_price_min(self, queryset, name, value):
        return queryset.filter(
            Q(establishment__units__price__gte=value) | Q(price_range='high', establishment__units__isnull=True)
        ).distinct()

    def filter_price_max(self, queryset, name, value):
        return queryset.filter(
            Q(establishment__units__price__lte=value) | (Q(price_range='low') & Q(establishment__units__isnull=True))
        ).distinct()
