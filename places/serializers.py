from rest_framework import serializers
from .models import Place, PlaceMedia, Establishment, EstablishmentUnit, Amenity, EstablishmentContact

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ('id', 'name', 'icon')

class PlaceMediaSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = PlaceMedia
        fields = ('id', 'media_url', 'media_type', 'is_cover')

    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media_url:
            return request.build_absolute_uri(obj.media_url.url)
        return None

class EstablishmentUnitSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = EstablishmentUnit
        fields = ('id', 'name', 'unit_type', 'price', 'description', 'image')

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

class PlaceListSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    place_type = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ('id', 'name', 'cover_image', 'avg_rating', 'latitude', 'longitude', 'category_name', 'place_type')

    def get_cover_image(self, obj):
        request = self.context.get('request')
        if obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_place_type(self, obj):
        if hasattr(obj, 'establishment'):
            return 'Establishment'
        elif hasattr(obj, 'landmark'):
            return 'Landmark'
        elif hasattr(obj, 'servicepoint'):
            return 'ServicePoint'
        return 'Place'

from interactions.serializers import ReviewSerializer

class EstablishmentContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstablishmentContact
        fields = ('id', 'type', 'carrier', 'label', 'value', 'is_primary', 'display_order')

class PlaceDetailSerializer(PlaceListSerializer):
    # Field 'media' comes from related_name='media' in PlaceMedia
    gallery = PlaceMediaSerializer(source='media', many=True, read_only=True)
    units = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()

    class Meta(PlaceListSerializer.Meta):
        fields = PlaceListSerializer.Meta.fields + ('description', 'contact_info', 'address_text', 'gallery', 'units', 'amenities', 'reviews', 'contacts')

    def get_contacts(self, obj):
        if hasattr(obj, 'establishment'):
            contacts = obj.establishment.contacts.filter(is_visible=True).order_by('display_order')
            return EstablishmentContactSerializer(contacts, many=True).data
        return []

    def get_units(self, obj):
        if hasattr(obj, 'establishment'):
             return EstablishmentUnitSerializer(obj.establishment.units.all(), many=True, context=self.context).data
        return []

    def get_amenities(self, obj):
        if hasattr(obj, 'establishment'):
            return AmenitySerializer(obj.establishment.amenities.all(), many=True, context=self.context).data
        return []
    
    def get_reviews(self, obj):
        # Get latest 5 reviews
        reviews = obj.reviews.all().order_by('-created_at')[:5]
        return ReviewSerializer(reviews, many=True).data
