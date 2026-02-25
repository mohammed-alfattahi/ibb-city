from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Avg
from users.models import PartnerProfile
from places.models import Establishment
from .models import Review, Report, Notification, Favorite, PlaceComment, SystemAlert
from .notifications import NotificationService
from management.models import Request, Advertisement
from django.urls import reverse

# ==========================================
# Partner Profile Signals
# ==========================================

@receiver(pre_save, sender=PartnerProfile)
def track_partner_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = PartnerProfile.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except PartnerProfile.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=PartnerProfile)
def notify_partner_status_change(sender, instance, created, **kwargs):
    if created:
        NotificationService.emit_event(
            'NEW_PARTNER_REGISTRATION', 
            {'partner_name': instance.user.username, 'url': reverse('admin:users_partnerprofile_change', args=[instance.pk])},
            {'role': 'staff'},
            priority='medium'
        )
        NotificationService.emit_event(
            'PARTNER_REQUEST_RECEIVED',
            {'url': reverse('partner_dashboard')},
            {'user_id': instance.user.id},
            priority='low'
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        new_status = instance.status
        
        if old_status != new_status:
            # Bug 8 Fix: Skip generic notification for 'approved' status because 
            # ApprovePartnerView sends a specific "Congratulations" notification.
            if new_status == 'approved':
                pass
            else:
                NotificationService.emit_event(
                    'PARTNER_STATUS_CHANGE',
                    {'status': new_status, 'reason': getattr(instance, 'rejection_reason', '') or getattr(instance, 'info_request_message', ''), 'url': reverse('partner_dashboard')},
                    {'user_id': instance.user.id},
                    priority='high'
                )

@receiver(pre_save, sender=Establishment)
def track_establishment_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Establishment.objects.get(pk=instance.pk)
            instance._old_license_status = old_instance.license_status
            instance._old_is_active = old_instance.is_active
            instance._old_pending_updates = old_instance.pending_updates
        except Establishment.DoesNotExist:
            instance._old_license_status = None
            instance._old_is_active = None
            instance._old_pending_updates = {}
    else:
        instance._old_license_status = None
        instance._old_is_active = None
        instance._old_pending_updates = {}

@receiver(post_save, sender=Establishment)
def notify_establishment_changes(sender, instance, created, **kwargs):
    if created:
        NotificationService.emit_event(
            'NEW_ESTABLISHMENT_REQUEST',
            {'place_name': instance.name, 'owner': instance.owner.username, 'url': reverse('admin:places_establishment_change', args=[instance.pk])},
            {'role': 'staff'},
            priority='medium'
        )
        NotificationService.emit_event(
            'ESTABLISHMENT_REQUEST_RECEIVED',
            {'place_name': instance.name, 'url': reverse('partner_establishment_list')},
            {'user_id': instance.owner.id},
            priority='low'
        )
    else:
        # Status/License Change
        old_license = getattr(instance, '_old_license_status', None)
        new_license = instance.license_status
        
        if old_license != new_license:
            NotificationService.emit_event(
                'ESTABLISHMENT_LICENSE_CHANGE',
                {'place_name': instance.name, 'status': new_license, 'url': reverse('partner_place_dashboard', args=[instance.pk])},
                {'user_id': instance.owner.id},
                priority='high'
            )
        
        # Active Status Logic
        old_active = getattr(instance, '_old_is_active', None)
        new_active = instance.is_active
        
        if old_active is not None and old_active != new_active:
            event = 'ESTABLISHMENT_SUSPENDED' if not new_active else 'ESTABLISHMENT_REACTIVATED'
            NotificationService.emit_event(
                event,
                {'place_name': instance.name, 'url': reverse('partner_place_dashboard', args=[instance.pk])},
                {'user_id': instance.owner.id},
                priority='high'
            )
        
        # Pending Updates Logic (Legacy check, usually handled by EstablishmentService now)
        old_updates = getattr(instance, '_old_pending_updates', {})
        new_updates = instance.pending_updates
        
        if not old_updates and new_updates:
            NotificationService.emit_event(
                'REQUEST_UPDATE',
                {'target': instance.name, 'url': reverse('admin:places_establishment_change', args=[instance.pk])},
                {'role': 'staff'}
            )

@receiver(post_save, sender=PlaceComment)
def notify_place_comment(sender, instance, created, **kwargs):
    if not created:
        return

    place = instance.place
    author = instance.user
    place_owner = place.establishment.owner if hasattr(place, 'establishment') else None
    
    # Check for direct reply or review reply
    is_review_reply = bool(instance.review)
    is_comment_reply = bool(instance.parent)
    
    if is_review_reply:
        # Reply to Review -> Notify Reviewer
        target_user = instance.review.user
        if target_user and target_user != author:
            NotificationService.emit_event(
                'REVIEW_REPLY',
                {'place_name': place.name, 'replier': author.username, 'url': reverse('place_detail', args=[place.pk])},
                {'user_id': target_user.id},
                priority='medium'
            )
    elif is_comment_reply:
        # Reply to Comment -> Notify Commenter
        target_user = instance.parent.user
        if target_user and target_user != author:
            NotificationService.emit_event(
                'NEW_COMMENT_REPLY',
                {'place_name': place.name, 'replier': author.username, 'url': reverse('place_detail', args=[place.pk])},
                {'user_id': target_user.id},
                priority='medium'
            )
    else:
        # Top-level Comment -> Notify Place Owner
        if place_owner and place_owner != author:
            NotificationService.emit_event(
                'NEW_COMMENT',
                {'place_name': place.name, 'author': author.username, 'url': reverse('partner_place_dashboard', args=[place.establishment.pk]) if hasattr(place, 'establishment') else reverse('place_detail', args=[place.pk])},
                {'user_id': place_owner.id},
                priority='medium'
            )

@receiver(post_save, sender=Review)
def notify_new_review(sender, instance, created, **kwargs):
    if created:
        NotificationService.emit_event(
            'NEW_REVIEW',
            {'place_name': instance.place.name, 'rating': instance.rating, 'url': reverse('partner_place_dashboard', args=[instance.place.establishment.pk]) if hasattr(instance.place, 'establishment') else reverse('place_detail', args=[instance.place.pk])},
            {'user_id': instance.place.owner.id if hasattr(instance.place, 'owner') else None},
            priority='medium'
        )
    
    # Recalculate Average Rating
    # We can use RatingService or EstablishmentService. 
    # For now, simplistic approach as RatingService handles it too. 
    # But Review is signal source.
    from interactions.services.rating_service import RatingService
    RatingService.update_place_statistics(instance.place)

@receiver(post_delete, sender=Review)
def notify_delete_review(sender, instance, **kwargs):
    """
    Recalculate stats when a review is deleted.
    """
    from interactions.services.rating_service import RatingService
    if instance.place:
        RatingService.update_place_statistics(instance.place)

@receiver(post_save, sender=Report)
def notify_report_events(sender, instance, created, **kwargs):
    if created:
        NotificationService.emit_event(
            'NEW_REPORT',
            {'target': str(instance.content_object), 'url': reverse('admin:interactions_report_change', args=[instance.pk])},
            {'role': 'staff'}
        )
    elif instance.status in ['RESOLVED', 'REJECTED']:
        NotificationService.emit_event(
            'REPORT_UPDATE',
            {'status': instance.status, 'note': instance.admin_note, 'url': reverse('home')}, # No specific report detail page for tourist yet
            {'user_id': instance.user.id},
            priority='medium'
        )

@receiver(pre_save, sender=Advertisement)
def track_ad_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Advertisement.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
            instance._old_receipt = old_instance.receipt_image
        except Advertisement.DoesNotExist:
            instance._old_status = None
            instance._old_receipt = None
    else:
        instance._old_status = None
        instance._old_receipt = None

@receiver(post_save, sender=Advertisement)
def notify_ad_events(sender, instance, created, **kwargs):
    if created:
        NotificationService.emit_event('NEW_AD_REQUEST', {'title': instance.title, 'url': reverse('admin:management_advertisement_change', args=[instance.pk])}, {'role': 'staff'})
        if not instance.receipt_image and instance.owner:
             NotificationService.emit_event('AD_PAYMENT_NEEDED', {'title': instance.title, 'url': f"{reverse('partner_ads')}#ad-{instance.pk}"}, {'user_id': instance.owner.id})
    else:
        if instance.owner:
            old_status = getattr(instance, '_old_status', None)
            new_status = instance.status

            if old_status != new_status:
                NotificationService.emit_event(
                    'AD_STATUS_CHANGE', 
                    {'title': instance.title, 'status': new_status, 'note': getattr(instance, 'admin_notes', ''), 'url': f"{reverse('partner_ads')}#ad-{instance.pk}", 'image': instance.banner_image.url if instance.banner_image else None},
                    {'user_id': instance.owner.id}
                )
                if new_status == 'active':
                    # Notify Favorites logic (skipped for now)
                    pass 
            
            old_receipt = getattr(instance, '_old_receipt', None)
            new_receipt = instance.receipt_image
            # Check if receipt is NEWLY uploaded (was None/empty, now has value)
            if not old_receipt and new_receipt:
                 NotificationService.emit_event('AD_PAYMENT_UPLOADED', {'title': instance.title, 'url': reverse('admin:management_advertisement_change', args=[instance.pk]), 'image': instance.receipt_image.url if instance.receipt_image else None}, {'role': 'staff'})

@receiver(post_save, sender=Request)
def notify_request_events(sender, instance, created, **kwargs):
    if created and instance.request_type == 'UPGRADE_PARTNER':
        NotificationService.emit_event(
            'PARTNER_UPGRADE_REQUEST',
            {'user': instance.user.username, 'url': reverse('admin:management_request_change', args=[instance.pk])},
            {'role': 'staff'}
        )

@receiver(post_save, sender=SystemAlert)
def process_system_alert(sender, instance, created, **kwargs):
    """
    Trigger broadcast when a SystemAlert is created or marked for sending.
    """
    if created or (instance.is_sent and not getattr(instance, '_already_processed', False)):
        # Avoid recursion if we update the instance
        if hasattr(instance, '_handling_signal'):
             return
             
        # Determine Audience Criteria
        criteria = {}
        if instance.target_audience == 'all':
            criteria = {'broadcast': True}
        elif instance.target_audience == 'partners':
            criteria = {'role': 'partner'}
        elif instance.target_audience == 'staff':
            criteria = {'role': 'staff'}
            
        # Emit Event
        NotificationService.emit_event(
            instance.alert_type,
            {'title': instance.title, 'message': instance.message, 'url': reverse('home')},
            criteria,
            priority='high',
            sender=instance.created_by
        )
        
        # Mark as sent if not already
        if not instance.is_sent:
            from django.utils import timezone
            instance._handling_signal = True
            instance.is_sent = True
            instance.sent_at = timezone.now()
            instance.save(update_fields=['is_sent', 'sent_at'])
