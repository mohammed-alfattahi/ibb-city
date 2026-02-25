"""
Use Cases Package
وحدة حالات الاستخدام المقسمة

الهيكل:
- base.py: فئة النتيجة الأساسية (UseCaseResult)
- establishments.py: حالات استخدام المنشآت
- approvals.py: حالات استخدام الموافقات
- reviews.py: حالات استخدام التقييمات
"""

# Base
from .base import UseCaseResult

# Establishment Use Cases
from .establishments import (
    SubmitUpdateRequestUseCase,
    CreatePlaceUseCase,
)

# Approval Use Cases
from .approvals import (
    ApproveRequestUseCase,
    ApprovePartnerUseCase,
    RejectPartnerUseCase,
)

# Review Use Cases
from .reviews import CreateReviewUseCase


__all__ = [
    'UseCaseResult',
    'SubmitUpdateRequestUseCase',
    'CreatePlaceUseCase',
    'ApproveRequestUseCase',
    'ApprovePartnerUseCase',
    'RejectPartnerUseCase',
    'CreateReviewUseCase',
]
