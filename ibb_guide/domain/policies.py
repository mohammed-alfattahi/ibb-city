"""
Domain Policies - Business Rules for Moderation, Notifications, and Content

This module defines policy classes that encapsulate business rules
for content moderation, notifications, and other cross-cutting concerns.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable


# ============================================
# Content Moderation Policy
# ============================================

class ContentType(Enum):
    """Types of content that can be moderated."""
    REVIEW = "review"
    REPLY = "reply"
    ESTABLISHMENT = "establishment"
    ADVERTISEMENT = "advertisement"
    REPORT = "report"


class ModerationAction(Enum):
    """Actions that can be taken during moderation."""
    APPROVE = "approve"
    HIDE = "hide"
    DELETE = "delete"
    WARN = "warn"
    BAN_USER = "ban_user"


@dataclass
class ModerationContext:
    """Context for a moderation decision."""
    content_type: ContentType
    content_id: int
    content_text: str
    author_id: int
    moderator_id: int
    reason: str = ""
    warning_count: int = 0


class ModerationPolicy:
    """
    Domain policy for content moderation.
    
    Encapsulates rules for:
    - Bad word detection
    - Auto-moderation thresholds
    - User warning escalation
    
    Usage:
        policy = ModerationPolicy()
        issues = policy.check_content("some text")
        if issues:
            action = policy.recommend_action(issues, context)
    """
    
    # Bad words dictionary (configurable)
    BAD_WORDS_AR = ['شتيمة', 'قبيح', 'سيء', 'غبي', 'كذب']
    BAD_WORDS_EN = ['badword', 'spam', 'scam']
    
    # Thresholds
    MAX_WARNINGS_BEFORE_BAN = 3
    AUTO_HIDE_REPORT_THRESHOLD = 3  # Hide content after 3 reports
    
    def check_content(self, text: str) -> List[str]:
        """
        Check content for policy violations.
        
        Args:
            text: Content to check
            
        Returns:
            List of issues found
        """
        issues = []
        text_lower = text.lower()
        
        # Check for bad words
        for word in self.BAD_WORDS_AR + self.BAD_WORDS_EN:
            if word in text_lower:
                issues.append(f"محتوى غير لائق: '{word}'")
        
        # Check for spam patterns
        if self._is_spam(text):
            issues.append("نمط إرسال مشبوه")
        
        return issues
    
    def _is_spam(self, text: str) -> bool:
        """Detect spam patterns."""
        # Simple heuristics
        if len(text) < 5:
            return False
        
        # Excessive URLs
        url_count = text.lower().count('http')
        if url_count > 3:
            return True
        
        # Excessive repetition
        words = text.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # Less than 30% unique words
                return True
        
        return False
    
    def recommend_action(self, issues: List[str], context: ModerationContext) -> ModerationAction:
        """
        Recommend an action based on issues and context.
        
        Args:
            issues: List of issues found
            context: Moderation context
            
        Returns:
            Recommended ModerationAction
        """
        if not issues:
            return ModerationAction.APPROVE
        
        # Check user history
        if context.warning_count >= self.MAX_WARNINGS_BEFORE_BAN:
            return ModerationAction.BAN_USER
        
        # Severity-based recommendation
        severe_keywords = ['شتيمة', 'scam', 'spam']
        has_severe = any(any(k in issue for k in severe_keywords) for issue in issues)
        
        if has_severe:
            return ModerationAction.DELETE
        
        return ModerationAction.WARN
    
    def should_auto_hide(self, report_count: int) -> bool:
        """Check if content should be auto-hidden based on report count."""
        return report_count >= self.AUTO_HIDE_REPORT_THRESHOLD
    
    def get_warning_message(self, issues: List[str]) -> str:
        """Generate a warning message for the user."""
        if not issues:
            return ""
        return f"تحذير: تم اكتشاف محتوى غير مناسب. يرجى تعديل المحتوى أو سيتم إخفاؤه."


# ============================================
# Notification Policy
# ============================================

class NotificationChannel(Enum):
    """Available notification channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class NotificationContext:
    """Context for sending notifications."""
    event_type: str
    recipient_id: int
    recipient_role: str  # 'tourist', 'partner', 'admin'
    data: dict = None


class NotificationPolicy:
    """
    Domain policy for notification delivery.
    
    Encapsulates rules for:
    - Which channels to use for each event
    - Priority determination
    - Batching and throttling rules
    
    Usage:
        policy = NotificationPolicy()
        channels = policy.get_channels_for_event("new_review", context)
        priority = policy.get_priority("request_approved")
    """
    
    # Event -> Channels mapping
    EVENT_CHANNELS = {
        # Partner events
        'partner_approved': [NotificationChannel.PUSH, NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        'partner_rejected': [NotificationChannel.PUSH, NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        'request_approved': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        'request_rejected': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        'request_needs_info': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        
        # Tourist events
        'new_review': [NotificationChannel.IN_APP],
        'review_reply': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        'favorite_updated': [NotificationChannel.IN_APP],
        
        # Admin events
        'new_report': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        'new_partner_request': [NotificationChannel.PUSH, NotificationChannel.IN_APP],
        'system_alert': [NotificationChannel.PUSH, NotificationChannel.EMAIL, NotificationChannel.IN_APP],
    }
    
    # Event -> Priority mapping
    EVENT_PRIORITY = {
        'partner_approved': NotificationPriority.HIGH,
        'partner_rejected': NotificationPriority.HIGH,
        'request_approved': NotificationPriority.NORMAL,
        'request_rejected': NotificationPriority.NORMAL,
        'new_review': NotificationPriority.LOW,
        'review_reply': NotificationPriority.NORMAL,
        'new_report': NotificationPriority.HIGH,
        'system_alert': NotificationPriority.URGENT,
    }
    
    # Role-based channel restrictions
    ROLE_CHANNELS = {
        'tourist': [NotificationChannel.IN_APP, NotificationChannel.PUSH],
        'partner': [NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.EMAIL],
        'admin': [NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.EMAIL, NotificationChannel.SMS],
    }
    
    def get_channels_for_event(self, event_type: str, context: NotificationContext) -> List[NotificationChannel]:
        """
        Get appropriate channels for an event.
        
        Args:
            event_type: Type of event
            context: Notification context
            
        Returns:
            List of channels to use
        """
        event_channels = self.EVENT_CHANNELS.get(event_type, [NotificationChannel.IN_APP])
        role_channels = self.ROLE_CHANNELS.get(context.recipient_role, [NotificationChannel.IN_APP])
        
        # Intersection of event channels and role-permitted channels
        return [c for c in event_channels if c in role_channels]
    
    def get_priority(self, event_type: str) -> NotificationPriority:
        """Get priority for an event type."""
        return self.EVENT_PRIORITY.get(event_type, NotificationPriority.NORMAL)
    
    def should_batch(self, event_type: str) -> bool:
        """Determine if notifications for this event should be batched."""
        # Low priority events can be batched
        return self.get_priority(event_type) == NotificationPriority.LOW
    
    def get_throttle_seconds(self, event_type: str) -> int:
        """Get throttle interval in seconds for an event type."""
        priority = self.get_priority(event_type)
        
        throttle_map = {
            NotificationPriority.LOW: 300,      # 5 minutes
            NotificationPriority.NORMAL: 60,    # 1 minute
            NotificationPriority.HIGH: 0,       # No throttle
            NotificationPriority.URGENT: 0,     # No throttle
        }
        
        return throttle_map.get(priority, 60)
    
    def format_notification(self, event_type: str, data: dict) -> dict:
        """
        Format notification content based on event type.
        
        Returns:
            dict with 'title' and 'message' keys
        """
        templates = {
            'partner_approved': {
                'title': 'تمت الموافقة على حسابك',
                'message': 'مرحباً {username}! تمت الموافقة على حساب الشريك الخاص بك.'
            },
            'partner_rejected': {
                'title': 'تم رفض طلب الشراكة',
                'message': 'عذراً، تم رفض طلب الشراكة. السبب: {reason}'
            },
            'request_approved': {
                'title': 'تمت الموافقة على طلبك',
                'message': 'تمت الموافقة على طلبك #{request_id} وتم تطبيق التعديلات.'
            },
            'new_review': {
                'title': 'تقييم جديد',
                'message': 'قام {reviewer} بتقييم {place_name} بـ {rating} نجوم.'
            },
            'review_reply': {
                'title': 'رد على تقييمك',
                'message': 'قام {replier} بالرد على تقييمك في {place_name}.'
            },
        }
        
        template = templates.get(event_type, {
            'title': 'إشعار جديد',
            'message': 'لديك إشعار جديد.'
        })
        
        return {
            'title': template['title'].format(**data) if data else template['title'],
            'message': template['message'].format(**data) if data else template['message']
        }
