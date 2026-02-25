from management.services.moderation_service import analyze_text, log_moderation_event

class ModerationService:
    """
    Facade for the unified Management Moderation Service.
    Kept for backward compatibility.
    """
    
    @staticmethod
    def check_content(user, content_object, text_content: str) -> tuple[bool, str, list]:
        """
        Check content against banned words using the new engine.
        
        Args:
            user: The author
            content_object: The model instance (can be None)
            text_content: The text found in the content.
            
        Returns:
            tuple: (is_safe: bool, status: str, matched_terms: list)
        """
        if not text_content:
            return True, "SAFE", []
            
        result = analyze_text(text_content, user)
        
        status = "SAFE"
        if result.action == 'block':
            status = "BLOCKED"
        elif result.action == 'warn':
            status = "WARNING"
            
        if status != "SAFE":
           # Log event using new service
           # Note: We don't have request object here for IP, but we can pass None
           # content_object might be None if pre-validation.
           log_moderation_event(user, text_content, result, content_object, ip_address=None)
           
        return (status != "BLOCKED"), status, result.matched

