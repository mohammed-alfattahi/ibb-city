
from django.utils import timezone
from interactions.models import PlaceComment
from management.models import AuditLog
from interactions.services.moderation_service import ModerationService
# from interactions.notifications... import NotificationService (assuming it exists or I mock it)

class CommentService:
    """
    Service for managing Threaded Comments.
    """
    
    @staticmethod
    def create_comment(user, place, content, parent_id=None, review=None, ip=None):
        """
        Create a comment or reply.
        """
        # Moderation Check (Pre-submission usually handled in View, but double check here)
        is_safe, status, terms = ModerationService.check_content(user, None, content)
        if status == 'BLOCKED':
            return None, False, f"Content blocked due to banned terms: {', '.join(terms)}"
            
        parent = None
        if parent_id:
            try:
                parent = PlaceComment.objects.get(pk=parent_id)
            except PlaceComment.DoesNotExist:
                return None, False, "Parent comment not found"
        
        # If review is provided, ensure it belongs to place?
        # Assuming caller validates relations, or we rely on DB constraints.
        
        comment = PlaceComment.objects.create(
            user=user,
            place=place,
            review=review,
            parent=parent,
            content=content,
            visibility_state='visible',
            moderation_flags={'matched_terms': terms, 'status': status} if terms else {}
        )
        
        # Determine if we should warn
        msg = "Comment added."
        if status == 'WARNING':
            msg = f"Comment added with warnings: {', '.join(terms)}"
            
        # Notification Logic
        # 1. Notify Place Owner (if not own comment)
        if hasattr(place, 'establishment') and place.establishment.owner != user:
             # Notify owner
             pass
        # 2. Notify Parent Author (if reply)
        if parent and parent.user != user:
             # Notify parent user
             pass
             
        return comment, True, msg

    @staticmethod
    def edit_comment(user, comment_id, new_content):
        try:
            comment = PlaceComment.objects.get(pk=comment_id)
        except PlaceComment.DoesNotExist:
             return False, "Comment not found"
             
        if comment.user != user:
            return False, "Permission denied"
            
        is_safe, status, terms = ModerationService.check_content(user, comment, new_content)
        if status == 'BLOCKED':
            return False, "Content contains banned words and cannot be saved."
            
        comment.content = new_content
        comment.is_edited = True
        comment.edited_at = timezone.now()
        comment.save()
        return True, "Comment updated."

    @staticmethod
    def set_visibility(user, comment_id, visibility, reason=None, model_class=None):
        """
        Set visibility: 'visible', 'partner_hidden', 'admin_hidden'.
        Enforces permissions.
        model_class: Review or PlaceComment (default PlaceComment)
        """
        if model_class is None:
            model_class = PlaceComment
            
        try:
            obj = model_class.objects.get(pk=comment_id)
        except model_class.DoesNotExist:
            return False, "Content not found"
            
        # Check permissions
        is_admin = user.is_staff or user.is_superuser
        
        # Check ownership of the PLACE (not the comment author)
        # Using getattr to handle both Review and PlaceComment relations safely
        place = getattr(obj, 'place', None)
        is_partner_owner = False
        if place and hasattr(place, 'establishment') and place.establishment.owner == user:
            is_partner_owner = True
        
        if visibility == 'admin_hidden':
            if not is_admin:
                return False, "Only admin can use admin_hidden"
        elif visibility == 'partner_hidden':
            if not (is_partner_owner or is_admin):
                return False, "Only partner owner can use partner_hidden"
        elif visibility == 'visible':
            # Unhiding
            # Admin can unhide anything.
            # Partner can unhide 'partner_hidden' BUT NOT 'admin_hidden'.
            if obj.visibility_state == 'admin_hidden' and not is_admin:
                return False, "Partner cannot unhide admin-hidden content."
            if not (is_partner_owner or is_admin):
                 return False, "Permission denied"
                 
        obj.visibility_state = visibility
        if visibility != 'visible':
            obj.hidden_by = user
            obj.hidden_reason = reason
        
        obj.save()
        return True, f"Visibility set to {visibility}"
