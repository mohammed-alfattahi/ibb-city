"""
Moderation Engine - Automatic Content Filtering
محرك الإشراف التلقائي على المحتوى
"""
import re
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from management.models import ModerationRule, ModerationQueueItem
from interactions.notifications.admin import AdminNotifications


class ModerationEngine:
    """
    محرك فلترة المحتوى التلقائي
    يقيّم النصوص ويقرر: ALLOW / FLAG / BLOCK
    """
    
    DECISION_ALLOW = 'ALLOW'
    DECISION_FLAG = 'FLAG'
    DECISION_BLOCK = 'BLOCK'
    
    @classmethod
    def evaluate(cls, text: str) -> tuple:
        """
        Evaluate text against all active moderation rules.
        
        Returns:
            tuple: (decision, matched_rule_name, matched_keyword)
                - decision: ALLOW, FLAG, or BLOCK
                - matched_rule_name: Name of the rule that matched (or None)
                - matched_keyword: The keyword/pattern that matched (or None)
        """
        if not text:
            return (cls.DECISION_ALLOW, None, None)
        
        text_lower = text.lower().strip()
        
        # Get all active rules, ordered by action priority (BLOCK first, then FLAG)
        rules = ModerationRule.objects.filter(is_active=True).order_by(
            # BLOCK has highest priority
            '-action'
        )
        
        for rule in rules:
            matched = cls._check_rule(text_lower, rule)
            if matched:
                return (rule.action, rule.name, matched)
        
        return (cls.DECISION_ALLOW, None, None)
    
    @classmethod
    def _check_rule(cls, text: str, rule: ModerationRule) -> str | None:
        """
        Check if text matches a rule.
        
        Returns:
            str: The matched keyword/pattern, or None if no match
        """
        if rule.is_regex:
            # Treat keywords as regex pattern
            try:
                pattern = rule.keywords.strip()
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
            except re.error:
                # Invalid regex, skip this rule
                pass
        else:
            # Treat keywords as comma-separated list
            keywords = [k.strip().lower() for k in rule.keywords.split(',') if k.strip()]
            for keyword in keywords:
                if keyword in text:
                    return keyword
        
        return None
    
    @classmethod
    def flag_content(cls, content_object, reason: str = '', notify_admins: bool = True):
        """
        Flag content for manual review.
        Creates a ModerationQueueItem and optionally notifies admins.
        
        Args:
            content_object: The Django model instance to flag (Review, Comment, etc.)
            reason: Reason for flagging
            notify_admins: Whether to send notification to admins
            
        Returns:
            ModerationQueueItem: The created queue item
        """
        content_type = ContentType.objects.get_for_model(content_object)
        
        # Create snippet from content
        snippet = cls._get_content_snippet(content_object)
        
        # Check if already flagged and pending
        existing = ModerationQueueItem.objects.filter(
            content_type=content_type,
            object_id=content_object.pk,
            status='PENDING'
        ).first()
        
        if existing:
            # Already in queue, update reason if provided
            if reason:
                existing.flagged_reason = reason
                existing.save(update_fields=['flagged_reason'])
            return existing
        
        # Create new queue item
        queue_item = ModerationQueueItem.objects.create(
            content_type=content_type,
            object_id=content_object.pk,
            content_snippet=snippet,
            flagged_reason=reason,
            status='PENDING'
        )
        
        # Notify admins
        if notify_admins:
            cls._notify_admins(queue_item)
        
        return queue_item
    
    @classmethod
    def _get_content_snippet(cls, obj, max_length: int = 200) -> str:
        """Extract text snippet from content object."""
        # Try common text attributes
        for attr in ['content', 'text', 'comment', 'description', 'body']:
            if hasattr(obj, attr):
                text = getattr(obj, attr) or ''
                return text[:max_length]
        return str(obj)[:max_length]
    
    @classmethod
    def _notify_admins(cls, queue_item: ModerationQueueItem):
        """Send notification to admins about flagged content."""
        try:
            AdminNotifications.notify_content_flagged(
                content_type=str(queue_item.content_type),
                content_snippet=queue_item.content_snippet[:100],
                reason=queue_item.flagged_reason
            )
        except Exception:
            # Don't fail if notification fails
            pass
    
    @classmethod
    def moderate_and_decide(cls, text: str, content_object=None) -> str:
        """
        Convenience method: Evaluate text and auto-flag if needed.
        
        Args:
            text: The text content to evaluate
            content_object: Optional - the content object to flag if decision is FLAG
            
        Returns:
            str: The decision (ALLOW, FLAG, BLOCK)
        """
        decision, rule_name, matched = cls.evaluate(text)
        
        if decision == cls.DECISION_FLAG and content_object:
            reason = f"Matched rule '{rule_name}': {matched}"
            cls.flag_content(content_object, reason=reason)
        
        return decision
