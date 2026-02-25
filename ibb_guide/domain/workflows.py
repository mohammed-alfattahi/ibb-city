"""
Approval Workflow Domain - Core Business Rules for Approvals

This module defines the approval workflow logic independent of Django.
It handles state transitions and business rules for:
- Partner approval
- Request approval
- Advertisement approval
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime


class ApprovalStatus(Enum):
    """Possible states in the approval workflow."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_INFO = "NEEDS_INFO"
    CONDITIONAL = "CONDITIONAL_APPROVAL"


class ApprovalAction(Enum):
    """Actions that can be taken on an approval request."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_INFO = "request_info"
    CONDITIONAL_APPROVE = "conditional_approve"


@dataclass
class ApprovalContext:
    """Context for an approval decision."""
    request_id: int
    request_type: str
    requester_id: int
    reviewer_id: int
    reason: str = ""
    conditions: str = ""
    deadline: Optional[datetime] = None
    
    
class ApprovalWorkflow:
    """
    Domain entity for managing approval workflows.
    
    This class encapsulates the business rules for approvals,
    making them testable and reusable across different contexts.
    
    Usage:
        workflow = ApprovalWorkflow()
        can_approve, reason = workflow.can_transition(current_status, ApprovalAction.APPROVE)
        if can_approve:
            new_status = workflow.get_next_status(ApprovalAction.APPROVE)
    """
    
    # Valid transitions: (current_status, action) -> new_status
    TRANSITIONS = {
        (ApprovalStatus.PENDING, ApprovalAction.APPROVE): ApprovalStatus.APPROVED,
        (ApprovalStatus.PENDING, ApprovalAction.REJECT): ApprovalStatus.REJECTED,
        (ApprovalStatus.PENDING, ApprovalAction.REQUEST_INFO): ApprovalStatus.NEEDS_INFO,
        (ApprovalStatus.PENDING, ApprovalAction.CONDITIONAL_APPROVE): ApprovalStatus.CONDITIONAL,
        (ApprovalStatus.NEEDS_INFO, ApprovalAction.APPROVE): ApprovalStatus.APPROVED,
        (ApprovalStatus.NEEDS_INFO, ApprovalAction.REJECT): ApprovalStatus.REJECTED,
        (ApprovalStatus.CONDITIONAL, ApprovalAction.APPROVE): ApprovalStatus.APPROVED,
        (ApprovalStatus.CONDITIONAL, ApprovalAction.REJECT): ApprovalStatus.REJECTED,
    }
    
    # Required fields for each action
    REQUIRED_FIELDS = {
        ApprovalAction.REJECT: ['reason'],
        ApprovalAction.REQUEST_INFO: ['reason'],
        ApprovalAction.CONDITIONAL_APPROVE: ['conditions'],
    }
    
    def can_transition(self, current_status: ApprovalStatus, action: ApprovalAction) -> tuple[bool, str]:
        """
        Check if a transition is valid.
        
        Args:
            current_status: Current approval status
            action: Requested action
            
        Returns:
            tuple: (is_valid, reason_if_invalid)
        """
        if (current_status, action) not in self.TRANSITIONS:
            return False, f"لا يمكن تنفيذ '{action.value}' من الحالة '{current_status.value}'"
        return True, ""
    
    def get_next_status(self, action: ApprovalAction, current_status: ApprovalStatus = ApprovalStatus.PENDING) -> ApprovalStatus:
        """
        Get the next status after an action.
        
        Args:
            action: The action being taken
            current_status: Current status (default PENDING)
            
        Returns:
            New ApprovalStatus
        """
        return self.TRANSITIONS.get((current_status, action), current_status)
    
    def validate_action(self, action: ApprovalAction, context: ApprovalContext) -> tuple[bool, str]:
        """
        Validate that an action has all required fields.
        
        Args:
            action: The action to validate
            context: The approval context
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required = self.REQUIRED_FIELDS.get(action, [])
        
        for field in required:
            value = getattr(context, field, None)
            if not value:
                return False, f"الحقل '{field}' مطلوب لهذا الإجراء"
        
        return True, ""
    
    def execute(self, current_status: str, action: str, context: ApprovalContext) -> tuple[bool, str, str]:
        """
        Execute an approval action.
        
        Args:
            current_status: Current status as string
            action: Action as string
            context: ApprovalContext
            
        Returns:
            tuple: (success, new_status, message)
        """
        try:
            status_enum = ApprovalStatus(current_status)
            action_enum = ApprovalAction(action)
        except ValueError as e:
            return False, current_status, f"قيمة غير صالحة: {str(e)}"
        
        # Check transition validity
        can_transition, reason = self.can_transition(status_enum, action_enum)
        if not can_transition:
            return False, current_status, reason
        
        # Validate required fields
        is_valid, error = self.validate_action(action_enum, context)
        if not is_valid:
            return False, current_status, error
        
        # Get new status
        new_status = self.get_next_status(action_enum, status_enum)
        
        return True, new_status.value, "تم تنفيذ الإجراء بنجاح"


class PartnerApprovalWorkflow(ApprovalWorkflow):
    """Specialized workflow for partner approvals."""
    
    def get_notification_message(self, action: ApprovalAction, context: ApprovalContext) -> str:
        """Get appropriate notification message for the action."""
        messages = {
            ApprovalAction.APPROVE: "تهانينا! تمت الموافقة على حساب الشريك الخاص بك.",
            ApprovalAction.REJECT: f"عذراً، تم رفض طلب الشراكة. السبب: {context.reason}",
            ApprovalAction.REQUEST_INFO: f"مطلوب معلومات إضافية: {context.reason}",
            ApprovalAction.CONDITIONAL_APPROVE: f"تمت الموافقة المشروطة. الشروط: {context.conditions}",
        }
        return messages.get(action, "تم تحديث حالة طلبك.")


class RequestApprovalWorkflow(ApprovalWorkflow):
    """Specialized workflow for update requests."""
    
    def should_apply_changes(self, action: ApprovalAction) -> bool:
        """Determine if changes should be applied to the target object."""
        return action == ApprovalAction.APPROVE


class AdApprovalWorkflow(ApprovalWorkflow):
    """Specialized workflow for advertisement approvals."""
    
    # Additional ad-specific statuses
    AD_TRANSITIONS = {
        (ApprovalStatus.APPROVED, ApprovalAction.REJECT): ApprovalStatus.REJECTED,  # Can revoke approval
    }
    
    def __init__(self):
        super().__init__()
        self.TRANSITIONS.update(self.AD_TRANSITIONS)
