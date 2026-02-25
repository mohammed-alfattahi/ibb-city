"""
Establishment Use Cases
حالات استخدام المنشآت
"""
from .base import UseCaseResult


class SubmitUpdateRequestUseCase:
    """Use case for submitting an establishment update request."""
    
    def __init__(self):
        from ibb_guide.domain.workflows import RequestApprovalWorkflow
        from ibb_guide.domain.policies import NotificationPolicy
        
        self.workflow = RequestApprovalWorkflow()
        self.notification_policy = NotificationPolicy()
    
    def execute(self, user, establishment, changes: dict) -> UseCaseResult:
        from places.models import Establishment
        from places.services.establishment_service import EstablishmentService
        from management.models import Request
        from interactions.notifications import NotificationService
        
        # Step 1: Classify changes
        sensitive, non_sensitive = EstablishmentService.classify_changes(changes)
        
        # Step 2: Apply non-sensitive changes immediately
        immediate_applied = []
        if non_sensitive:
            for field, value in non_sensitive.items():
                setattr(establishment, field, value)
            establishment.save()
            immediate_applied = list(non_sensitive.keys())
        
        # Step 3: Create request for sensitive changes
        request_created = None
        if sensitive:
            request_type = self._determine_request_type(sensitive)
            
            request_created = Request.objects.create(
                user=user,
                request_type=request_type,
                target_content_type_id=Establishment._meta.app_label,
                target_object_id=establishment.id,
                changes=sensitive,
                original_data={k: getattr(establishment, k, None) for k in sensitive.keys()},
                description=f"طلب تعديل: {', '.join(sensitive.keys())}"
            )
            
            NotificationService.notify_group(
                target_group='admins',
                title='طلب تعديل جديد',
                message=f'{user.username} يطلب تعديل {establishment.place.name}',
                url=f'/custom-admin/requests/{request_created.id}/'
            )
        
        return UseCaseResult(
            success=True,
            message=self._build_message(immediate_applied, request_created),
            data={
                'immediate_applied': immediate_applied,
                'request_id': request_created.id if request_created else None
            }
        )
    
    def _determine_request_type(self, changes: dict) -> str:
        if 'name' in changes:
            return 'EDIT_NAME'
        if 'description' in changes:
            return 'EDIT_DESC'
        if 'latitude' in changes or 'longitude' in changes or 'address' in changes:
            return 'EDIT_LOCATION'
        if 'category' in changes:
            return 'EDIT_CATEGORY'
        return 'UPDATE_INFO'
    
    def _build_message(self, immediate: list, request) -> str:
        messages = []
        if immediate:
            messages.append(f"تم تطبيق التعديلات التالية فوراً: {', '.join(immediate)}")
        if request:
            messages.append("تم إنشاء طلب للتعديلات الحساسة وهي قيد المراجعة.")
        return ' | '.join(messages) if messages else "لم يتم إجراء أي تعديلات."


class CreatePlaceUseCase:
    """Use case for creating a new place/establishment."""
    
    def execute(self, user, place_data: dict) -> UseCaseResult:
        from places.models import Place, Establishment, Category
        from management.models import AuditLog
        from ibb_guide.validators import PlaceValidator
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Step 1: Validate data
        errors = PlaceValidator.validate_place_data(place_data)
        if errors:
            return UseCaseResult(success=False, message="فشل التحقق من البيانات", errors=errors)
        
        # Step 2: Extract and validate category
        category_id = place_data.pop('category', None)
        if not category_id:
            return UseCaseResult(success=False, message="يجب تحديد تصنيف المكان")
        
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return UseCaseResult(success=False, message="التصنيف غير موجود")
        
        # Step 3: Create Place
        try:
            place = Place.objects.create(
                name=place_data.get('name'),
                description=place_data.get('description', ''),
                category=category,
                directorate=place_data.get('directorate', ''),
                address=place_data.get('address', ''),
                latitude=place_data.get('latitude'),
                longitude=place_data.get('longitude'),
                is_active=False
            )
            
            establishment = Establishment.objects.create(
                place_ptr=place,
                owner=user,
                phone_number=place_data.get('phone_number', ''),
                website=place_data.get('website', ''),
                establishment_type=place_data.get('establishment_type', 'other')
            )
            
            AuditLog.objects.create(
                user=user,
                action='CREATE_PLACE',
                table_name='Establishment',
                record_id=str(establishment.pk),
                new_values={'name': place.name, 'category': category.name}
            )
            
            from interactions.notifications import NotificationService
            NotificationService.notify_admins(
                title="مكان جديد بانتظار الموافقة",
                message=f"{user.username} أضاف مكان جديد: {place.name}",
                notification_type='new_establishment_request',
                url=f'/custom-admin/establishments/pending/'
            )
            
            return UseCaseResult(
                success=True,
                message="تم إنشاء المكان بنجاح وهو قيد المراجعة",
                data={'place_id': place.id, 'establishment_id': establishment.id}
            )
            
        except Exception as e:
            return UseCaseResult(success=False, message=f"حدث خطأ أثناء إنشاء المكان: {str(e)}")
