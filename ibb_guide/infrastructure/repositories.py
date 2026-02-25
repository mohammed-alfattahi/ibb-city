"""
Repository Layer - Database Access Patterns

This module provides repository classes that encapsulate database access,
following the Repository Pattern for clean separation of concerns.
"""
from typing import List, Optional, Dict, Any
from django.db.models import Q, Avg, Count
from django.core.exceptions import ObjectDoesNotExist


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    model = None
    
    @classmethod
    def get_by_id(cls, pk: int):
        """Get a single object by primary key."""
        try:
            return cls.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return None
    
    @classmethod
    def get_all(cls, limit: int = None):
        """Get all objects, optionally limited."""
        qs = cls.model.objects.all()
        return qs[:limit] if limit else qs
    
    @classmethod
    def create(cls, **kwargs):
        """Create a new object."""
        return cls.model.objects.create(**kwargs)
    
    @classmethod
    def update(cls, pk: int, **kwargs):
        """Update an object by primary key."""
        obj = cls.get_by_id(pk)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            obj.save()
        return obj
    
    @classmethod
    def delete(cls, pk: int) -> bool:
        """Delete an object by primary key."""
        obj = cls.get_by_id(pk)
        if obj:
            obj.delete()
            return True
        return False
    
    @classmethod
    def exists(cls, pk: int) -> bool:
        """Check if an object exists."""
        return cls.model.objects.filter(pk=pk).exists()


class PlaceRepository(BaseRepository):
    """Repository for Place model."""
    
    @classmethod
    def _get_model(cls):
        from places.models import Place
        return Place
    
    @classmethod
    @property
    def model(cls):
        return cls._get_model()
    
    @classmethod
    def get_active(cls, limit: int = None):
        """Get all active places."""
        from places.models import Place
        qs = Place.objects.filter(is_active=True)
        return qs[:limit] if limit else qs
    
    @classmethod
    def search(cls, query: str, category_id: int = None, limit: int = 20):
        """Search places by name or description."""
        from places.models import Place
        qs = Place.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
        
        if category_id:
            qs = qs.filter(category_id=category_id)
        
        return qs.order_by('-avg_rating')[:limit]
    
    @classmethod
    def get_by_category(cls, category_id: int, limit: int = None):
        """Get places by category."""
        from places.models import Place
        qs = Place.objects.filter(category_id=category_id, is_active=True)
        return qs[:limit] if limit else qs
    
    @classmethod
    def get_top_rated(cls, limit: int = 10):
        """Get top-rated places."""
        from places.models import Place
        return Place.objects.filter(is_active=True).order_by('-avg_rating')[:limit]


class ReviewRepository(BaseRepository):
    """Repository for Review model."""
    
    @classmethod
    def _get_model(cls):
        from interactions.models import Review
        return Review
    
    @classmethod
    def get_for_place(cls, place_id: int, include_hidden: bool = False):
        """Get reviews for a place."""
        from interactions.models import Review
        qs = Review.objects.filter(place_id=place_id)
        if not include_hidden:
            qs = qs.filter(visibility_state='visible')
        return qs.select_related('user').prefetch_related('replies').order_by('-created_at')
    
    @classmethod
    def get_by_user(cls, user_id: int):
        """Get reviews by a user."""
        from interactions.models import Review
        return Review.objects.filter(user_id=user_id).order_by('-created_at')
    
    @classmethod
    def get_user_review_for_place(cls, user_id: int, place_id: int):
        """Get a user's review for a specific place (if exists)."""
        from interactions.models import Review
        try:
            return Review.objects.get(user_id=user_id, place_id=place_id)
        except ObjectDoesNotExist:
            return None


class RequestRepository(BaseRepository):
    """Repository for Request model."""
    
    @classmethod
    def _get_model(cls):
        from management.models import Request
        return Request
    
    @classmethod
    def get_pending(cls):
        """Get all pending requests."""
        from management.models import Request
        return Request.objects.filter(status='PENDING').order_by('-created_at')
    
    @classmethod
    def get_by_user(cls, user_id: int):
        """Get requests by a user."""
        from management.models import Request
        return Request.objects.filter(user_id=user_id).order_by('-created_at')
    
    @classmethod
    def get_by_status(cls, status: str):
        """Get requests by status."""
        from management.models import Request
        return Request.objects.filter(status=status).order_by('-created_at')


class EstablishmentRepository(BaseRepository):
    """Repository for Establishment model."""
    
    @classmethod
    def _get_model(cls):
        from places.models import Establishment
        return Establishment
    
    @classmethod
    def get_by_owner(cls, owner_id: int):
        """Get establishments by owner."""
        from places.models import Establishment
        return Establishment.objects.filter(owner_id=owner_id)
    
    @classmethod
    def get_verified(cls, limit: int = None):
        """Get verified establishments."""
        from places.models import Establishment
        qs = Establishment.objects.filter(is_verified=True)
        return qs[:limit] if limit else qs
    
    @classmethod
    def get_pending_approval(cls):
        """Get establishments pending approval."""
        from places.models import Establishment
        return Establishment.objects.filter(is_verified=False)


class AdvertisementRepository(BaseRepository):
    """Repository for Advertisement model."""
    
    @classmethod
    def _get_model(cls):
        from management.models import Advertisement
        return Advertisement
    
    @classmethod
    def get_active(cls):
        """Get active advertisements."""
        from management.models import Advertisement
        from django.utils import timezone
        from django.db.models import Q
        today = timezone.now().date()
        return Advertisement.objects.filter(
            status='active',
            start_date__lte=today
        ).filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True)
        )
    
    @classmethod
    def get_by_owner(cls, owner_id: int):
        """Get advertisements by owner."""
        from management.models import Advertisement
        return Advertisement.objects.filter(owner_id=owner_id).order_by('-created_at')
    
    @classmethod
    def get_pending(cls):
        """Get pending advertisements."""
        from management.models import Advertisement
        return Advertisement.objects.filter(status='pending').order_by('-created_at')
