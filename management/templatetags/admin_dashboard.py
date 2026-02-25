from django import template
from management.admin_dashboard import AdminDashboardService
import json
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def get_dashboard_stats():
    """Returns the KPI stats for the admin dashboard"""
    return AdminDashboardService.get_kpi_stats()


@register.simple_tag
def get_recent_activity(limit=10):
    """Returns recent audit logs"""
    return AdminDashboardService.get_recent_activity(limit)


@register.simple_tag
def get_chart_data():
    """Returns chart data (JSON)"""
    data = AdminDashboardService.get_chart_data()
    return mark_safe(json.dumps(data, default=str))


@register.simple_tag
def get_system_health():
    """Returns system health status"""
    return AdminDashboardService.get_system_health()


@register.simple_tag
def get_admin_modules():
    """Returns admin modules configuration"""
    from management.admin_modules import get_admin_modules as get_modules
    return get_modules()


@register.simple_tag
def get_pending_items():
    """Returns counts of all pending items"""
    return AdminDashboardService.get_pending_items()


@register.simple_tag
def get_top_places(limit=5):
    """Returns top rated places"""
    return AdminDashboardService.get_top_places(limit)


@register.simple_tag
def get_weekly_comparison():
    """Returns weekly comparison data with trends"""
    return AdminDashboardService.get_weekly_comparison()


@register.filter
def trend_class(value):
    """Returns CSS class based on trend value"""
    if value > 0:
        return 'text-success'
    elif value < 0:
        return 'text-danger'
    return 'text-muted'


@register.filter
def trend_icon(value):
    """Returns icon based on trend value"""
    if value > 0:
        return '↑'
    elif value < 0:
        return '↓'
    return '→'


@register.filter
def format_number(value):
    """Formats number with thousands separator"""
    try:
        return '{:,}'.format(int(value))
    except (ValueError, TypeError):
        return value


@register.filter
def format_currency(value):
    """Formats number as currency (Yemeni Riyal)"""
    try:
        return '{:,.0f} ر.ي'.format(float(value))
    except (ValueError, TypeError):
        return value


@register.inclusion_tag('admin/includes/stat_card.html')
def stat_card(title, value, icon='fa-chart-bar', color='primary', trend=None, subtitle=None):
    """Renders a statistics card"""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'trend': trend,
        'subtitle': subtitle,
    }


@register.inclusion_tag('admin/includes/progress_bar.html')
def progress_bar(current, total, label='', color='success'):
    """Renders a progress bar"""
    percentage = (current / total * 100) if total > 0 else 0
    return {
        'current': current,
        'total': total,
        'percentage': round(percentage, 1),
        'label': label,
        'color': color,
    }
