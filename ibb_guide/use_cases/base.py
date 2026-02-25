"""
Base Use Case Classes
فئات حالات الاستخدام الأساسية
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class UseCaseResult:
    """Standard result from use case execution."""
    success: bool
    message: str
    data: Any = None
    errors: list = None
