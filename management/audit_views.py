from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import AuditLog

class PartnerAuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'partners/audit_list.html'
    context_object_name = 'logs'
    paginate_by = 20

    def get_queryset(self):
        # Filter logs for actions performed by this user (Partner)
        return AuditLog.objects.filter(user=self.request.user).order_by('-timestamp')
