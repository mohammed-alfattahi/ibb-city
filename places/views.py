from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import PlaceListSerializer, PlaceDetailSerializer
from places import selectors

class PlaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing places.
    Uses selectors for consistent data retrieval.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'avg_rating']
    search_fields = ['name', 'description']

    def get_queryset(self):
        return selectors.get_public_places().select_related(
            'landmark', 'servicepoint'
        ).prefetch_related('media', 'reviews')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlaceDetailSerializer
        return PlaceListSerializer
