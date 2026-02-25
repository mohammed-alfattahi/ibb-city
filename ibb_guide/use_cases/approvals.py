"""
Approval Use Cases
حالات استخدام الموافقات
"""
from .base import UseCaseResult


class ApproveRequestUseCase:
    """Use case for approving a request."""
    
    def __init__(self):
        from ibb_guide.domain.workflows import ApprovalWorkflow
        self.workflow = ApprovalWorkflow()
    
    def execute(self, request_id: int, reviewer, action: str, 
                reason: str = "", conditions: str = "") -> UseCaseResult:
        from ibb_guide.domain.workflows import ApprovalContext
        from management.models import Request, ApprovalDecision
        from management.utils import RequestManager
        from interactions.notifications import NotificationService
        
        try:
            req = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            return UseCaseResult(success=False, message="الطلب غير موجود")
        
        context = ApprovalContext(
            request_id=request_id,
            request_type=req.request_type,
            requester_id=req.user_id,
            reviewer_id=reviewer.id,
            reason=reason,
            conditions=conditions
        )
        
        success, new_status, message = self.workflow.execute(req.status, action, context)
        
        if not success:
            return UseCaseResult(success=False, message=message)
        
        if action == 'approve':
            success, msg = RequestManager.approve_request(request_id, reviewer, reason)
        elif action == 'reject':
            success, msg = RequestManager.reject_request(request_id, reviewer, reason)
        elif action == 'request_info':
            success, msg = RequestManager.request_info(request_id, reviewer, reason)
        elif action == 'conditional_approve':
            success, msg = RequestManager.conditional_approve(request_id, reviewer, conditions, reason=reason)
        else:
            return UseCaseResult(success=False, message="إجراء غير معروف")
        
        if not success:
            return UseCaseResult(success=False, message=msg)
        
        decision_map = {
            'approve': 'APPROVE', 'reject': 'REJECT',
            'request_info': 'REQUEST_INFO', 'conditional_approve': 'CONDITIONAL'
        }
        
        ApprovalDecision.record_decision(
            request=req, user=reviewer,
            decision=decision_map.get(action, 'APPROVE'),
            reason=reason, conditions=conditions
        )
        
        NotificationService.notify_user(
            user=req.user,
            title=f'تحديث حالة الطلب #{request_id}',
            message=req.get_status_message(),
            url=f'/partner/requests/{request_id}/'
        )
        
        return UseCaseResult(success=True, message=msg, data={'new_status': new_status})


class ApprovePartnerUseCase:
    """Use case for approving a partner registration."""
    
    def execute(self, admin_user, partner_profile_id: int) -> UseCaseResult:
        from users.models import PartnerProfile
        from management.services.approval_service import PartnerApprovalService
        
        try:
            profile = PartnerProfile.objects.select_related('user').get(pk=partner_profile_id)
        except PartnerProfile.DoesNotExist:
            return UseCaseResult(success=False, message="ملف الشريك غير موجود")
        
        if profile.is_approved:
            return UseCaseResult(success=False, message="الشريك موافق عليه بالفعل")
        
        success, message = PartnerApprovalService.approve(profile, admin_user)
        
        if not success:
            return UseCaseResult(success=False, message=message)
        
        return UseCaseResult(
            success=True, message=message,
            data={'partner_username': profile.user.username}
        )


class RejectPartnerUseCase:
    """Use case for rejecting a partner registration."""
    
    def execute(self, admin_user, partner_profile_id: int, reason: str = "") -> UseCaseResult:
        from users.models import PartnerProfile
        from management.services.approval_service import PartnerApprovalService
        
        try:
            profile = PartnerProfile.objects.select_related('user').get(pk=partner_profile_id)
        except PartnerProfile.DoesNotExist:
            return UseCaseResult(success=False, message="ملف الشريك غير موجود")
        
        username = profile.user.username
        success, message = PartnerApprovalService.reject(profile, admin_user, reason)
        
        if not success:
            return UseCaseResult(success=False, message=message)
        
        return UseCaseResult(
            success=True, message=message,
            data={'partner_username': username, 'reason': reason}
        )
