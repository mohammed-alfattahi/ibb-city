"""
Moderation Service
Analyzes text against banned keywords and logs moderation events.
"""
import logging
from typing import Dict, Any, List, Tuple
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

from management.models import BannedWord, ModerationEvent
from .normalization import normalize_text

logger = logging.getLogger(__name__)

CACHE_KEY_WORDS = 'banned_words_list'
CACHE_TTL = 3600  # 1 hour


class ModerationResult:
    def __init__(self, action: str, severity: str, message: str, matched: list):
        self.action = action        # allow, warn, block
        self.severity = severity    # none, low, medium, high
        self.message = message      # Warning message for user
        self.matched = matched      # List of terms found


def get_banned_words() -> List[Dict]:
    """Get list of active banned words (cached)."""
    words = cache.get(CACHE_KEY_WORDS)
    if words is None:
        words = list(BannedWord.objects.filter(is_active=True).values('term', 'severity', 'language'))
        # Pre-normalize terms in cache
        for w in words:
            w['term_norm'] = normalize_text(w['term'])
        cache.set(CACHE_KEY_WORDS, words, CACHE_TTL)
    return words


def analyze_text(text: str, user=None) -> ModerationResult:
    """
    Analyze text for banned content.
    Returns ModerationResult.
    """
    if not text:
        return ModerationResult('allow', 'none', '', [])
    
    normalized_input = normalize_text(text)
    words = get_banned_words()
    
    matches = []
    max_severity_val = 0
    severity_map = {'low': 1, 'medium': 2, 'high': 3}
    
    for w in words:
        # Check if term is in text
        # Simple substring match on normalized text
        # For more advanced matching (word boundary), regex is needed.
        # Starting with simple inclusion for robustness against 'word1 word2'.
        if w['term_norm'] in normalized_input:
            matches.append(w)
            val = severity_map.get(w['severity'], 0)
            if val > max_severity_val:
                max_severity_val = val
    
    if not matches:
        return ModerationResult('allow', 'none', '', [])
    
    # Determine Action
    final_severity = 'low'
    if max_severity_val == 3:
        final_severity = 'high'
        action = 'block'
        message = 'Your content contains prohibited language and cannot be posted.'
    elif max_severity_val == 2:
        final_severity = 'medium'
        action = 'block'  # Strict policy: block medium too
        message = 'Your content contains inappropriate language.'
    else:
        final_severity = 'low'
        action = 'warn'
        message = 'Please keep the conversation respectful.'
    
    # Extract terms (only for internal logging, don't return to user in detail? 
    # actually result object is internal, view decides what to show)
    matched_terms = [m['term'] for m in matches]
    
    return ModerationResult(action, final_severity, message, matched_terms)


def log_moderation_event(user, content: str, result: ModerationResult, content_object=None, ip_address: str = None):
    """
    Log a moderation event to the DB.
    """
    if result.severity == 'none':
        return
        
    try:
        event = ModerationEvent(
            user=user if user and user.is_authenticated else None,
            content_snapshot=content[:3000],  # Truncate if too long
            severity=result.severity,
            action_taken='blocked' if result.action == 'block' else 'warned',
            matched_terms=result.matched,
            ip_address=ip_address
        )
        
        if content_object:
            event.content_type = ContentType.objects.get_for_model(content_object)
            event.object_id = content_object.pk
            
        event.save()
        logger.info(f"Moderation event logged: {result.action} for user {user}")
        
    except Exception as e:
        logger.error(f"Failed to log moderation event: {e}")


def invalidate_word_cache():
    """Clear banned word cache."""
    cache.delete(CACHE_KEY_WORDS)
