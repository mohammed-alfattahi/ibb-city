"""
Celery Tasks for Reports - SLA Escalation
مهام Celery للبلاغات - تصعيد SLA
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name='interactions.check_sla_breaches')
def check_sla_breaches():
    """
    Check for reports that have breached their SLA.
    Should be scheduled via Celery Beat every hour.
    
    Schedule in settings.py:
    CELERY_BEAT_SCHEDULE = {
        'check-sla-breaches-hourly': {
            'task': 'interactions.check_sla_breaches',
            'schedule': crontab(minute=0),  # Every hour
        },
    }
    """
    from interactions.models import Report
    from interactions.notifications.notification_service import NotificationService
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    now = timezone.now()
    
    # Find reports that have breached SLA
    breached_reports = Report.objects.filter(
        status__in=['NEW', 'IN_PROGRESS'],
        expected_resolution_at__lt=now
    ).exclude(
        # Don't re-escalate recently escalated
        admin_note__icontains='SLA BREACH'
    )
    
    escalated_count = 0
    for report in breached_reports:
        try:
            # Calculate breach time
            breach_hours = (now - report.expected_resolution_at).total_seconds() / 3600
            
            # Update report with escalation note
            current_note = report.admin_note or ''
            report.admin_note = f"{current_note}\n[SLA BREACH] تجاوز الوقت المتوقع بـ {breach_hours:.1f} ساعة - {now.strftime('%Y-%m-%d %H:%M')}"
            
            # Escalate priority
            if report.priority == 'low':
                report.priority = 'medium'
            elif report.priority == 'medium':
                report.priority = 'high'
            elif report.priority == 'high':
                report.priority = 'critical'
            
            report.save(update_fields=['admin_note', 'priority'])
            escalated_count += 1
            
            # Notify admins about escalation
            NotificationService.emit_event(
                event_name='SLA_BREACH',
                payload={
                    'report_id': report.pk,
                    'report_type': report.report_type,
                    'breach_hours': round(breach_hours, 1),
                    'new_priority': report.priority,
                    'url': f'/custom-admin/reports/{report.pk}/action/'
                },
                audience_criteria={'role': 'staff'},
                priority='high'
            )
            
            logger.warning(
                f"[SLA BREACH] Report #{report.pk} breached by {breach_hours:.1f}h, "
                f"escalated to {report.priority}"
            )
            
        except Exception as e:
            logger.error(f"[SLA] Error processing report {report.pk}: {e}")
    
    logger.info(f"[SLA Check] Escalated {escalated_count} reports")
    return {'status': 'success', 'escalated_count': escalated_count}


@shared_task(name='interactions.send_sla_warnings')
def send_sla_warnings():
    """
    Send warnings for reports approaching SLA deadline.
    Alerts for reports within 1 hour of SLA breach.
    
    Schedule in settings.py:
    CELERY_BEAT_SCHEDULE = {
        'send-sla-warnings': {
            'task': 'interactions.send_sla_warnings',
            'schedule': crontab(minute=30),  # Every hour at :30
        },
    }
    """
    from interactions.models import Report
    from interactions.notifications.notification_service import NotificationService
    from datetime import timedelta
    
    now = timezone.now()
    warning_threshold = now + timedelta(hours=1)
    
    # Find reports approaching SLA
    at_risk_reports = Report.objects.filter(
        status__in=['NEW', 'IN_PROGRESS'],
        expected_resolution_at__gt=now,
        expected_resolution_at__lte=warning_threshold
    )
    
    warned_count = 0
    for report in at_risk_reports:
        try:
            remaining_minutes = (report.expected_resolution_at - now).total_seconds() / 60
            
            # Notify assigned admin or all admins
            audience = {'user_id': report.assigned_to_id} if report.assigned_to else {'role': 'staff'}
            
            NotificationService.emit_event(
                event_name='SLA_WARNING',
                payload={
                    'report_id': report.pk,
                    'report_type': report.report_type,
                    'remaining_minutes': round(remaining_minutes),
                    'url': f'/custom-admin/reports/{report.pk}/action/'
                },
                audience_criteria=audience,
                priority='high'
            )
            warned_count += 1
            
        except Exception as e:
            logger.error(f"[SLA Warning] Error for report {report.pk}: {e}")
    
    logger.info(f"[SLA Warning] Sent {warned_count} warnings")
    return {'status': 'success', 'warned_count': warned_count}


@shared_task(name='interactions.generate_sla_report')
def generate_sla_report():
    """
    Generate weekly SLA compliance report.
    
    Schedule in settings.py:
    CELERY_BEAT_SCHEDULE = {
        'generate-sla-report-weekly': {
            'task': 'interactions.generate_sla_report',
            'schedule': crontab(hour=8, minute=0, day_of_week=0),  # Sunday 8AM
        },
    }
    """
    from interactions.models import Report
    from datetime import timedelta
    from django.db.models import Count, Avg, F
    
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    
    # Get weekly stats
    resolved_reports = Report.objects.filter(
        status='RESOLVED',
        resolved_at__gte=week_ago
    )
    
    total_resolved = resolved_reports.count()
    
    # SLA compliance (resolved before deadline)
    on_time = resolved_reports.filter(
        resolved_at__lte=F('expected_resolution_at')
    ).count()
    
    compliance_rate = (on_time / total_resolved * 100) if total_resolved > 0 else 0
    
    # Average resolution time
    from django.db.models import ExpressionWrapper, DurationField
    avg_resolution = resolved_reports.annotate(
        resolution_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=DurationField()
        )
    ).aggregate(avg=Avg('resolution_time'))
    
    avg_hours = avg_resolution['avg'].total_seconds() / 3600 if avg_resolution['avg'] else 0
    
    # By type
    by_type = resolved_reports.values('report_type').annotate(count=Count('id'))
    
    report_data = {
        'period': f"{week_ago.date()} to {now.date()}",
        'total_resolved': total_resolved,
        'on_time': on_time,
        'compliance_rate': round(compliance_rate, 1),
        'avg_resolution_hours': round(avg_hours, 1),
        'by_type': list(by_type)
    }
    
    logger.info(f"[SLA Report] Weekly: {total_resolved} resolved, {compliance_rate:.1f}% on-time")
    
    return report_data
