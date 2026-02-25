"""
Domain Layer Package - Core Business Logic

This package contains domain entities that encapsulate core business rules
independent of the web framework. These should be framework-agnostic.

Structure:
- workflows.py: ApprovalWorkflow, ModerationWorkflow
- policies.py: ModerationPolicy, NotificationPolicy  
- boundaries.py: Role-based access boundaries (Tourist, Partner, Admin)
"""
