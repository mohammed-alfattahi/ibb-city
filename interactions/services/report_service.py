from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.contrib.auth import get_user_model
from interactions.models import Report
from django.core.exceptions import ValidationError

User = get_user_model()

class ReportService:
    """
    Domain Service for managing the Report/Ticketing lifecycle.
    Handles:
    1. Anti-Abuse (Rate Limiting & Duplicates)
    2. Smart Routing & Prioritization
    3. SLA & escalation logic (foundations)
    4. Notification orchestration
    """

    # Configuration
    MAX_DAILY_REPORTS = 5
    DUPLICATE_WINDOW_HOURS = 24
    
    # SLA Configuration (Hours to resolve)
    SLA_CONFIG = {
        'SAFETY': 1,      # Critical: 1 hour
        'SPAM': 24,       # Low: 24 hours
        'INACCURATE': 48, # Medium: 48 hours
        'OTHER': 72,      # Low: 72 hours
    }

    @staticmethod
    def create_report(user, content_object, report_type, description, proof_image=None):
        """
        Create a new report with validation and smart routing.
        """
        # 0. Moderation on Description
        from management.services.moderation_service import analyze_text, log_moderation_event
        mod_result = analyze_text(description, user=user)
        if mod_result.action == 'block':
            log_moderation_event(user, description, mod_result, content_object, None) # IP handling needs request context, simplifying
            raise ValidationError(mod_result.message) # Raising ValidationError as View expects it

        # 1. Anti-Abuse Checks
        ReportService._check_rate_limit(user)
        ReportService._check_duplicates(user, content_object, report_type)

        # 2. Smart Routing & Prioritization
        priority = ReportService._determine_priority(report_type)
        
        # 3. SLA Calculation
        sla_hours = ReportService.SLA_CONFIG.get(report_type, 72)
        expected_resolution_at = timezone.now() + timedelta(hours=sla_hours)

        # 4. Create Ticket
        report = Report.objects.create(
            user=user,
            content_object=content_object,
            report_type=report_type,
            description=description,
            proof_image=proof_image,
            priority=priority,
            status='NEW',
            expected_resolution_at=expected_resolution_at
        )
        
        if mod_result.action == 'warn':
             # Maybe flag report?
             pass
        
        # 5. Post-Creation Actions
        ReportService._notify_admins(report)
        
        return report

    @staticmethod
    def _check_rate_limit(user):
        """Ensure user hasn't exceeded daily limit."""
        last_24h = timezone.now() - timedelta(hours=24)
        count = Report.objects.filter(user=user, created_at__gte=last_24h).count()
        if count >= ReportService.MAX_DAILY_REPORTS:
            raise ValidationError("لقد تجاوزت الحد اليومي المسموح به للإبلاغ. يرجى المحاولة لاحقاً.")

    @staticmethod
    def _check_duplicates(user, content_object, report_type):
        """Prevent duplicate reports for same object/type recently."""
        # Check specific duplicates from same user
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(content_object)
        
        exists = Report.objects.filter(
            user=user,
            content_type=content_type,
            object_id=content_object.pk,
            report_type=report_type,
            status__in=['NEW', 'IN_PROGRESS']
        ).exists()
        
        if exists:
            raise ValidationError("لقد قمت بإرسال بلاغ مشابه لهذا المحتوى وهو قيد المعالجة حالياً.")

    @staticmethod
    def _determine_priority(report_type):
        """Smart Routing: Set priority based on type."""
        if report_type in ['SAFETY', 'COPYRIGHT']:
            return 'critical'
        elif report_type in ['INAPPROPRIATE']:
            return 'high'
        elif report_type in ['INACCURATE']:
            return 'medium'
        return 'low'

    @staticmethod
    def _notify_admins(report):
        # Notify staff about a new report/ticket.
        from interactions.notifications.notification_service import NotificationService

        action_url = f"/custom-admin/reports/{report.pk}/action/"
        target = str(report.content_object)

        NotificationService.emit_event(
            event_name='NEW_REPORT',
            payload={'target': target, 'url': action_url},
            audience_criteria={'role': 'staff'},
            priority='high' if report.priority in ('critical', 'high') else 'normal'
        )

    @staticmethod
    def resolve_report(report, resolver, resolution_note):
        """
        Formal resolution process.
        """
        report.resolve(note=resolution_note) # Uses model method we created
        report.assigned_to = resolver
        report.save()
        
        # Log decision logic here if we add a separate DecisionLog model later
        
        return True

    @staticmethod
    def reject_report(report, resolver, rejection_reason):
        """
        Formal rejection process.
        """
        report.reject(note=rejection_reason)
        report.assigned_to = resolver
        report.save()
        return True
