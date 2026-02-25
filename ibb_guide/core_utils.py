"""
Core Utilities Module
مستودع مركزي للدوال المشتركة بين التطبيقات

يحتوي على:
- get_client_ip: استخراج IP العميل
- create_audit_log: إنشاء سجل تدقيق (wrapper لـ AuditService)
"""

import logging

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str | None:
    """
    استخراج IP الحقيقي للعميل من الطلب HTTP.
    
    يتعامل مع الحالات:
    - X-Forwarded-For (خلف proxy/load balancer)
    - REMOTE_ADDR المباشر
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: عنوان IP أو None
    """
    if not request:
        return None
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def create_audit_log(user, action: str, table: str, record_id, 
                     new_vals=None, old_vals=None, 
                     new_val=None, old_val=None,  # Aliases للتوافق
                     reason: str = "", request=None):
    """
    Wrapper مبسط لإنشاء سجل تدقيق.
    
    يستخدم AuditService داخلياً لكنه يوفر واجهة بسيطة
    للاستخدام السريع في Views.
    
    Args:
        user: User instance
        action: نوع الإجراء (CREATE, UPDATE, DELETE)
        table: اسم الجدول/النموذج
        record_id: معرف السجل
        new_vals/new_val: القيم الجديدة (dict)
        old_vals/old_val: القيم القديمة (dict)
        reason: سبب الإجراء (اختياري)
        request: HttpRequest لاستخراج IP (اختياري)
    """
    # دمج الـ aliases للتوافق
    final_new = new_vals or new_val
    final_old = old_vals or old_val
    
    try:
        from management.services.audit_service import AuditService
        AuditService.log(
            actor=user,
            action=action,
            target_model=table,
            target_id=record_id,
            old_data=final_old,
            new_data=final_new,
            reason=reason,
            request=request
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
