from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.urls import reverse_lazy
import csv
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from django.db import models

# Import Models
from users.models import User, PartnerProfile
from places.models import Establishment, Landmark
from interactions.models import Review, Report, SystemAlert, Favorite
from events.models import Event
from .models import Request, Advertisement, WeatherAlert, AuditLog, ModerationQueueItem
from users.mixins import StaffAdminRequiredMixin

# ==========================================
# 1. Admin Dashboard (New Feature)
# ==========================================

class AdminDashboardView(StaffAdminRequiredMixin, TemplateView):
    template_name = 'admin_dashboard/overview.html'
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Quick Stats (KPIs)
        context['total_users'] = User.objects.count()
        context['total_partners'] = PartnerProfile.objects.filter(is_approved=True).count()
        context['total_places'] = Establishment.objects.filter(license_status='Approved', is_active=True).count()
        context['total_revenue'] = 0 
        
        # 2. Action Items (Urgent)
        context['pending_partners'] = PartnerProfile.objects.filter(is_approved=False).count()
        context['pending_requests'] = Request.objects.filter(status='PENDING').count()
        context['flagged_content'] = ModerationQueueItem.objects.filter(status='PENDING').count()
        context['pending_reports'] = Report.objects.filter(status='NEW').count()
        
        # 2.1 Surveys Stats
        from surveys.models import Survey, SurveyResponse
        context['total_surveys'] = Survey.objects.count()
        context['active_surveys'] = Survey.objects.filter(is_active=True).count()
        context['total_responses'] = SurveyResponse.objects.count()
        
        # 3. Recent Activity
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['recent_requests'] = Request.objects.order_by('-created_at')[:5]
        
        # 3.1 Audit Logs
        from management.models import AuditLog
        context['recent_logs'] = AuditLog.objects.select_related('user').order_by('-timestamp')[:8]
        
        # 3.5 Quick Review Lists (New)
        context['pending_partners_list'] = PartnerProfile.objects.filter(is_approved=False, status='pending').order_by('-created_at')[:5]
        context['pending_establishments_list'] = Establishment.objects.filter(approval_status='pending').select_related('owner', 'category')[:5]
        
        # 4. Charts Data
        # A. Partner Status
        partner_stats = PartnerProfile.objects.aggregate(
            active=Count('id', filter=models.Q(status='approved')),
            pending=Count('id', filter=models.Q(status='pending')),
            rejected=Count('id', filter=models.Q(status='rejected')),
            needs_info=Count('id', filter=models.Q(status='needs_info'))
        )
        context['chart_partner_data'] = [
            partner_stats['active'], 
            partner_stats['pending'], 
            partner_stats['rejected'], 
            partner_stats['needs_info']
        ]
        
        # B. Weekly Views (Aggregated from PlaceDailyView)
        from places.models.analytics import PlaceDailyView
        from django.db.models.functions import TruncDate
        
        today = timezone.now().date()
        last_7_days = today - timedelta(days=6)
        
        daily_views = PlaceDailyView.objects.filter(
            date__range=[last_7_days, today]
        ).values('date').annotate(total_views=Sum('views')).order_by('date')
        
        # Fill missing dates with 0
        views_dict = {item['date']: item['total_views'] for item in daily_views}
        labels = []
        data = []
        
        for i in range(7):
            d = last_7_days + timedelta(days=i)
            labels.append(d.strftime('%Y-%m-%d'))
            data.append(views_dict.get(d, 0))
            
        context['chart_daily_labels'] = labels
        context['chart_daily_data'] = data
        
        return context

# ==========================================
# 2. Partner Management
# ==========================================

class PendingPartnersListView(StaffAdminRequiredMixin, ListView):
    model = PartnerProfile
    template_name = 'management/partner_approval_list.html'
    context_object_name = 'pending_partners'
    
    def get_queryset(self):
        qs = PartnerProfile.objects.filter(status='pending').select_related('user')
        
        # Search filter
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(user__username__icontains=q) |
                Q(user__email__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(organization_name__icontains=q)
            )
        
        # Sort
        sort = self.request.GET.get('sort', '-submitted_at')
        if sort in ['submitted_at', '-submitted_at']:
            qs = qs.order_by(sort, '-created_at')
        else:
            qs = qs.order_by('-submitted_at', '-created_at')
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = PartnerProfile.objects.filter(status='pending').count()
        context['recently_approved'] = PartnerProfile.objects.filter(status='approved').order_by('-reviewed_at')[:5]
        context['recently_rejected'] = PartnerProfile.objects.filter(status='rejected').order_by('-reviewed_at')[:5]
        return context

class ApprovePartnerView(StaffAdminRequiredMixin, View):
    def post(self, request, pk):
        partner = get_object_or_404(PartnerProfile, pk=pk)
        
        # Update partner profile
        partner.is_approved = True
        partner.status = 'approved'
        partner.reviewed_by = request.user
        partner.reviewed_at = timezone.now()
        partner.save()
        
        # CRITICAL: Activate user account (Bug 2 fix)
        partner.user.account_status = 'active'
        
        # Bug 7 Fix: Update User Role to 'partner'
        from users.models import Role
        partner_role, _ = Role.objects.get_or_create(name='partner')
        partner.user.role = partner_role
        
        partner.user.save(update_fields=['account_status', 'role'])
        
        # Send notification to partner
        from interactions.notifications.partner import PartnerNotifications
        PartnerNotifications.notify_partner_approved(partner)
        
        messages.success(request, f"تم اعتماد الشريك {partner.user.username} بنجاح.")
        return redirect('admin_pending_partners')

# ==========================================
# 3. Partner Rejection & Info Request (Gap 3 fix)
# ==========================================

class RejectPartnerView(StaffAdminRequiredMixin, View):
    """رفض طلب الشريك"""
    def post(self, request, pk):
        partner = get_object_or_404(PartnerProfile, pk=pk)
        reason = request.POST.get('reason', '')
        
        # Update partner profile
        partner.status = 'rejected'
        partner.is_approved = False
        partner.rejection_reason = reason
        partner.reviewed_by = request.user
        partner.reviewed_at = timezone.now()
        partner.save()
        
        # Update user account status
        partner.user.account_status = 'rejected'
        partner.user.save(update_fields=['account_status'])
        
        # Send notification to partner
        from interactions.notifications.partner import PartnerNotifications
        PartnerNotifications.notify_partner_rejected(partner, reason)
        
        messages.info(request, f"تم رفض طلب الشريك {partner.user.username}.")
        return redirect('admin_pending_partners')


class PartnerNeedsInfoView(StaffAdminRequiredMixin, View):
    """طلب معلومات إضافية من الشريك"""
    def post(self, request, pk):
        partner = get_object_or_404(PartnerProfile, pk=pk)
        info_message = request.POST.get('info_message', '')
        
        # Update partner profile
        partner.status = 'needs_info'
        partner.info_request_message = info_message
        partner.reviewed_by = request.user
        partner.reviewed_at = timezone.now()
        partner.save()
        
        # Send notification to partner
        from interactions.notifications.partner import PartnerNotifications
        PartnerNotifications.notify_partner_needs_info(partner, info_message)
        
        messages.info(request, f"تم طلب معلومات إضافية من {partner.user.username}.")
        return redirect('admin_pending_partners')

# ==========================================
# 4. Requests Management
# ==========================================

class AdminRequestListView(StaffAdminRequiredMixin, ListView):
    model = Request
    template_name = 'management/admin_request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        qs = super().get_queryset().select_related('user')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(user__username__icontains=q) |
                Q(request_type__icontains=q) |
                Q(description__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from management.models.requests import RequestStatusLog
        
        # Stats
        context['pending_count'] = Request.objects.filter(status='PENDING').count()
        context['total_requests'] = Request.objects.count()
        
        # Recent Activity for Sidebar
        context['recent_activity'] = RequestStatusLog.objects.select_related('request', 'changed_by', 'request__user').order_by('-created_at')[:10]
        
        return context

class AdminRequestDetailView(StaffAdminRequiredMixin, DetailView):
    model = Request
    template_name = 'management/admin_request_detail.html'  # Step 3.2.6 fix
    context_object_name = 'req'

class AdminRequestActionView(StaffAdminRequiredMixin, View):
    def post(self, request, pk):
        req_obj = get_object_or_404(Request, pk=pk)
        action = request.POST.get('action')
        # Bug 2.2 fix: Read correct POST fields from template
        reason = request.POST.get('admin_response', '')
        conditions = request.POST.get('conditions', '')
        deadline_str = request.POST.get('deadline')
        deadline = None
        if deadline_str:
            from django.utils.dateparse import parse_datetime
            deadline = parse_datetime(deadline_str)
        decision_doc = request.FILES.get('decision_doc')
        
        from management.services.approval_service import ApprovalService
        
        try:
            if action == 'approve':
                ApprovalService.process_decision(req_obj, request.user, 'APPROVE', reason)
                messages.success(request, "تمت الموافقة على الطلب بنجاح.")
            elif action == 'reject':
                ApprovalService.process_decision(req_obj, request.user, 'REJECT', reason)
                messages.warning(request, "تم رفض الطلب.")
            elif action == 'needs_info':
                ApprovalService.process_decision(req_obj, request.user, 'REQUEST_INFO', reason)
                messages.info(request, "تم طلب معلومات إضافية.")
            elif action == 'conditional_approve':
                ApprovalService.process_decision(
                    req_obj, request.user, 'CONDITIONAL', reason,
                    conditions=conditions, deadline=deadline, document=decision_doc
                )
                messages.info(request, "تمت الموافقة المشروطة.")
        except Exception as e:
            messages.error(request, f"خطأ في معالجة الطلب: {str(e)}")
            
        return redirect('admin_request_list')

# ==========================================
# 4. Weather Alerts
# ==========================================

class WeatherAlertListView(StaffAdminRequiredMixin, ListView):
    model = WeatherAlert
    template_name = 'admin_dashboard/weather_list.html'
    context_object_name = 'alerts'

class WeatherAlertCreateView(StaffAdminRequiredMixin, CreateView):
    model = WeatherAlert
    fields = ['title', 'description', 'severity', 'expires_at']
    template_name = 'admin_dashboard/weather_form.html'
    success_url = reverse_lazy('admin_weather_alerts')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Send in-app notification to all active users
        from interactions.notifications.notification_service import NotificationService
        
        alert = self.object
        severity_ar = {
            'YELLOW': 'تحذير أصفر',
            'ORANGE': 'تحذير برتقالي',
            'RED': 'تحذير أحمر',
        }
        severity_text = severity_ar.get(alert.severity, 'تنبيه')
        
        NotificationService.emit_event(
            'WEATHER_ALERT',
            {
                'title': f"⚠️ {severity_text} - {alert.title}",
                'message': alert.description[:200] if len(alert.description) > 200 else alert.description,
                'severity': alert.severity,
                'alert_id': alert.pk,
            },
            {'role': 'all'},
            priority='high'
        )
        
        return response

class AdminWeatherDeleteView(StaffAdminRequiredMixin, DeleteView):
    model = WeatherAlert
    success_url = reverse_lazy('admin_weather_alerts')
    template_name = 'admin_dashboard/confirm_delete.html'

class CreateSystemAlertView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """عرض إنشاء تنبيه جديد (بث عام)"""
    model = SystemAlert
    fields = ['title', 'message', 'alert_type', 'target_audience']
    template_name = 'admin_dashboard/system_alert_form.html'
    success_url = reverse_lazy('custom_admin_dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Signal 'post_save' handles notification dispatch and marking as sent.
        messages.success(self.request, f"تم إرسال التنبيه '{form.instance.title}' بنجاح.")
        return response

    def test_func(self):
        return self.request.user.is_superuser # Only superusers or specific permission for broadcast

class AdminExportView(StaffAdminRequiredMixin, View):
    """
    تصدير البيانات إلى CSV
    يدعم النماذج: users, partners, establishments
    """
    def get(self, request, model_type=None, *args, **kwargs):
        # Support both URL param and GET param
        model_name = model_type or request.GET.get('model')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        # Fix: Write BOM for Excel compatibility with Arabic
        import codecs
        response.write(codecs.BOM_UTF8)
        
        writer = csv.writer(response)
        
        timestamp = timezone.now().strftime("%Y%m%d_%H%M")
        
        if model_name == 'users':
            response['Content-Disposition'] = f'attachment; filename="users_export_{timestamp}.csv"'
            writer.writerow(['ID', 'Username', 'Email', 'Role', 'Date Joined', 'Active'])
            users = User.objects.all().values_list('id', 'username', 'email', 'role__name', 'date_joined', 'is_active')
            for user in users:
                writer.writerow(user)
                
        elif model_name == 'partners':
            response['Content-Disposition'] = f'attachment; filename="partners_export_{timestamp}.csv"'
            writer.writerow(['ID', 'Organization', 'User', 'Status', 'Phone', 'Created At'])
            partners = PartnerProfile.objects.select_related('user').all()
            for p in partners:
                writer.writerow([
                    p.id, 
                    p.organization_name, 
                    p.user.username, 
                    p.get_status_display(), 
                    p.phone_number, 
                    p.created_at
                ])
                
        elif model_name == 'establishments':
            response['Content-Disposition'] = f'attachment; filename="establishments_export_{timestamp}.csv"'
            writer.writerow(['ID', 'Name', 'Category', 'Owner', 'Status', 'Views', 'Created At'])
            places = Establishment.objects.select_related('category', 'owner').all()
            for p in places:
                writer.writerow([
                    p.id, 
                    p.name, 
                    p.category.name if p.category else '-', 
                    p.owner.username, 
                    p.approval_status, 
                    p.views, 
                    p.created_at
                ])
        else:
            return HttpResponse("Invalid Model", status=400)
            
        return response

# ==========================================
# 5. Ad Management
# ==========================================

class AdRequestListView(StaffAdminRequiredMixin, ListView):
    model = Advertisement
    template_name = 'admin_dashboard/ad_list.html'
    context_object_name = 'ads'
    ordering = ['-created_at']
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        
        qs = Advertisement.objects.select_related('place', 'owner').order_by('-created_at')
        
        # Status filter
        status = self.request.GET.get('status', 'pending')
        if status and status != 'all':
            qs = qs.filter(status=status)
        
        # Search filter
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(place__name__icontains=q) |
                Q(owner__username__icontains=q)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats Summary
        all_ads = Advertisement.objects.all()
        context['stats'] = {
            'pending': all_ads.filter(status='pending').count(),
            'active': all_ads.filter(status='active').count(),
            'paused': all_ads.filter(status='paused').count(),
            'rejected': all_ads.filter(status='rejected').count(),
            'expired': all_ads.filter(status='expired').count(),
            'draft': all_ads.filter(status='draft').count(),
            'payment_issue': all_ads.filter(status='payment_issue').count(),
            'total': all_ads.count(),
        }
        
        # Current filter
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Revenue stats
        from django.db.models import Sum
        context['total_revenue'] = Advertisement.objects.filter(
            status='active'
        ).aggregate(total=Sum('price'))['total'] or 0
        
        return context

class ApproveAdView(StaffAdminRequiredMixin, View):
    def post(self, request, pk):
        # Step 8-ج: Use AdService for Approval
        from .services.ad_service import AdService
        ad = get_object_or_404(Advertisement, pk=pk)
        
        try:
            AdService.process_approval(ad, request.user, approved=True)
            messages.success(request, "تم اعتماد الإعلان بنجاح وتفعيل الفاتورة كمدفوعة.")
        except Exception as e:
            messages.error(request, f"حدث خطأ: {str(e)}")
            
        return redirect('admin_ad_list')

class RejectAdView(StaffAdminRequiredMixin, View):
    def post(self, request, pk):
        # Step 8-ج: Use AdService for Rejection/Payment Issue
        from .services.ad_service import AdService
        ad = get_object_or_404(Advertisement, pk=pk)

        reason = request.POST.get('reason', '')
        action = request.POST.get('action', 'reject')
        
        try:
            if action == 'payment_issue':
                # Special status for payment issues (not full reject)
                ad.status = 'payment_issue'
                ad.admin_notes = reason
                ad.save()
                messages.warning(request, "تم إعادة الطلب للشريك لوجود مشكلة في الدفع.")
            else:
                # Full rejection
                AdService.process_approval(
                    ad, request.user, approved=False, rejection_reason=reason
                )
                messages.error(request, "تم رفض الإعلان.")
        except Exception as e:
             messages.error(request, f"حدث خطأ: {str(e)}")
             
        return redirect('admin_ad_list')


class PauseAdView(StaffAdminRequiredMixin, View):
    """إيقاف إعلان نشط مؤقتاً"""
    def post(self, request, pk):
        from .services.ad_service import AdService
        ad = get_object_or_404(Advertisement, pk=pk)
        
        try:
            success, message = AdService.pause_ad(ad)
            if success:
                messages.success(request, "تم إيقاف الإعلان مؤقتاً.")
            else:
                messages.error(request, message)
        except Exception as e:
            messages.error(request, f"حدث خطأ: {str(e)}")
            
        return redirect('admin_ad_list')


class ResumeAdView(StaffAdminRequiredMixin, View):
    """استئناف إعلان متوقف"""
    def post(self, request, pk):
        from .services.ad_service import AdService
        ad = get_object_or_404(Advertisement, pk=pk)
        
        try:
            success, message = AdService.resume_ad(ad)
            if success:
                messages.success(request, "تم استئناف الإعلان.")
            else:
                messages.error(request, message)
        except Exception as e:
            messages.error(request, f"حدث خطأ: {str(e)}")
            
        return redirect('admin_ad_list')

# ==========================================
# 6. Establishment Management
# ==========================================

class AdminEstablishmentListView(StaffAdminRequiredMixin, ListView):
    model = Establishment
    template_name = 'admin_dashboard/establishment_list.html'
    context_object_name = 'places'
    ordering = ['-created_at']
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q, Avg, Count
        
        qs = Establishment.objects.select_related('owner', 'category').annotate(
            reviews_count=Count('reviews'),
            live_avg_rating=Avg('reviews__rating')
        ).order_by('-created_at')
        
        # Status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            qs = qs.filter(is_active=True, is_suspended=False)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'suspended':
            qs = qs.filter(is_suspended=True)
        elif status == 'pending':
            qs = qs.filter(approval_status='pending')
        
        # Category filter
        category = self.request.GET.get('category', '')
        if category:
            qs = qs.filter(category_id=category)
        
        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(owner__username__icontains=q) |
                Q(city__icontains=q)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        from places.models import Category
        
        context = super().get_context_data(**kwargs)
        
        # Stats
        all_establishments = Establishment.objects.all()
        context['stats'] = {
            'total': all_establishments.count(),
            'active': all_establishments.filter(is_active=True, is_suspended=False).count(),
            'inactive': all_establishments.filter(is_active=False).count(),
            'suspended': all_establishments.filter(is_suspended=True).count(),
            'pending': all_establishments.filter(approval_status='pending').count(),
        }
        
        # Categories for filter
        context['categories'] = Category.objects.all()
        
        # Current filters
        context['current_status'] = self.request.GET.get('status', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context

class SuspendEstablishmentView(StaffAdminRequiredMixin, View):
    def post(self, request, pk):
        place = get_object_or_404(Establishment, pk=pk)
        action = request.POST.get('action') # 'suspend' or 'unsuspend'
        reason = request.POST.get('reason', '')
        
        from interactions.notifications.partner import PartnerNotifications
        
        if action == 'suspend':
            place.is_suspended = True
            place.suspension_reason = reason
            place.save(update_fields=['is_suspended', 'suspension_reason'])
            PartnerNotifications.notify_establishment_suspended(place, reason)
            messages.warning(request, f"تم تعليق المنشأة {place.name}.")
            
        elif action == 'unsuspend':
            place.is_suspended = False
            place.suspension_reason = ''
            # Ensure it's active as well
            if not place.is_active:
                place.is_active = True
                place.save(update_fields=['is_suspended', 'suspension_reason', 'is_active'])
            else:
                place.save(update_fields=['is_suspended', 'suspension_reason'])
                
            PartnerNotifications.notify_establishment_reactivated(place)
            messages.success(request, f"تم تفعيل المنشأة {place.name}.")
            
        return redirect('admin_establishment_list')

class AdminEstablishmentBulkActionView(StaffAdminRequiredMixin, View):
    def post(self, request):
        action = request.POST.get('action')
        place_ids = request.POST.getlist('place_ids')
        
        if not place_ids:
            messages.error(request, "لم يتم تحديد أي منشآت.")
            return redirect('admin_establishment_list')
            
        qs = Establishment.objects.filter(pk__in=place_ids)
        count = qs.count()
        
        from interactions.notifications.partner import PartnerNotifications
        
        if action == 'activate':
            updated_count = 0
            for place in qs:
                # Approve if pending
                if place.approval_status == 'pending':
                    place.approve(request.user)
                
                # Ensure active and unsuspended
                place.is_suspended = False
                place.is_active = True
                place.suspension_reason = ''
                place.save(update_fields=['is_suspended', 'is_active', 'suspension_reason'])
                updated_count += 1
            
            messages.success(request, f"تم تفعيل/اعتماد {updated_count} منشأة بنجاح.")
            
        elif action == 'suspend':
            updated = qs.update(is_suspended=True, suspension_reason='تعليق جماعي من الإدارة')
            for place in qs:
                PartnerNotifications.notify_establishment_suspended(place, 'تعليق جماعي من الإدارة')
            messages.warning(request, f"تم تعليق {updated} منشأة.")
            
        return redirect('admin_establishment_list')

# ==========================================
# 7. Reports Management
# ==========================================

class AdminReportsListView(StaffAdminRequiredMixin, ListView):
    model = Report
    template_name = 'admin_dashboard/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q
        from django.utils import timezone
        
        qs = Report.objects.select_related('user', 'assigned_to').prefetch_related('content_object').order_by('-created_at')
        
        # Status filter
        status = self.request.GET.get('status', 'pending')
        if status == 'pending':
            qs = qs.filter(status__in=['new', 'pending'])
        elif status != 'all':
            qs = qs.filter(status=status)
        
        # Priority filter
        priority = self.request.GET.get('priority', '')
        if priority:
            qs = qs.filter(priority=priority)
        
        # Reason filter
        reason = self.request.GET.get('reason', '')
        if reason:
            qs = qs.filter(reason=reason)
        
        # SLA Breach filter
        sla_breach = self.request.GET.get('sla_breach', '')
        if sla_breach == 'yes':
            # Reports older than 48 hours and still pending
            threshold = timezone.now() - timezone.timedelta(hours=48)
            qs = qs.filter(status__in=['new', 'pending'], created_at__lt=threshold)
        
        return qs
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        
        # Stats
        all_reports = Report.objects.all()
        pending = all_reports.filter(status__in=['new', 'pending'])
        
        # SLA breach count (pending > 48h)
        threshold = timezone.now() - timezone.timedelta(hours=48)
        sla_breach_count = pending.filter(created_at__lt=threshold).count()
        
        context['stats'] = {
            'pending': pending.count(),
            'reviewed': all_reports.filter(status='reviewed').count(),
            'resolved': all_reports.filter(status='resolved').count(),
            'rejected': all_reports.filter(status='rejected').count(),
            'total': all_reports.count(),
            'sla_breach': sla_breach_count,
        }
        
        # Priority choices
        context['priority_choices'] = [
            ('low', 'منخفضة'),
            ('medium', 'متوسطة'),
            ('high', 'عالية'),
            ('critical', 'حرجة'),
        ]
        
        # Reason choices from model
        context['reason_choices'] = Report.REPORT_TYPES
        
        # Staff users for assignment
        context['staff_users'] = User.objects.filter(is_staff=True).order_by('first_name')
        
        # Current filters
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_reason'] = self.request.GET.get('reason', '')
        context['sla_threshold'] = timezone.now() - timezone.timedelta(hours=48)
        
        return context


class AdminReportActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk):
        from django.utils import timezone
        
        report = get_object_or_404(Report, pk=pk)
        action = request.POST.get('action')
        
        if action == 'reviewed':
            report.status = 'IN_PROGRESS' # Was 'reviewed'
            report.assigned_to = request.user # Was reviewed_by
            report.save(update_fields=['status', 'assigned_to'])
            messages.info(request, "تم تغيير حالة البلاغ إلى قيد المعالجة")
            
        elif action == 'resolve':
            report.resolve(note=f"Resolved by {request.user.username}")
            messages.success(request, "تم حل البلاغ")
            
        elif action == 'reject':
            report.reject(note=f"Rejected by {request.user.username}")
            messages.warning(request, "تم رفض البلاغ")
            
        elif action == 'assign':
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                # Assuming there's logic for assignment, for now just assign to self
                # The original code assigned based on assigned_to_id, let's keep that logic
                # but use the assign_to method if it exists and takes a user object.
                # For now, we'll assume assign_to takes a user object.
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    assigned_user = User.objects.get(pk=assigned_to_id)
                    report.assign_to(assigned_user)
                    messages.success(request, f"تم إسناد البلاغ إلى {assigned_user.username}")
                except User.DoesNotExist:
                    messages.error(request, "المستخدم المحدد غير موجود.")
            else:
                # If no specific user is selected, assign to the current user (admin)
                report.assign_to(request.user)
                messages.success(request, f"تم إسناد البلاغ إليك")
        elif action == 'set_priority':
            priority = request.POST.get('priority')
            if priority and hasattr(report, 'priority'):
                report.priority = priority
                
        report.save()
        messages.success(request, "تم تحديث البلاغ")
        return redirect('admin_reports_list')

    def test_func(self):
        return self.request.user.is_staff
# ==========================================
# 8. User Management
# ==========================================

class AdminUsersListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'admin_dashboard/user_list.html'
    context_object_name = 'users'
    paginate_by = 30
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        from django.db.models import Q, Count
        from users.models import PartnerProfile
        
        qs = User.objects.annotate(
            reviews_count=Count('reviews', distinct=True),
            favorites_count=Count('favorites', distinct=True),
        ).order_by('-date_joined')
        
        # Type filter
        user_type = self.request.GET.get('type', 'all')
        if user_type == 'partners':
            partner_users = PartnerProfile.objects.filter(status='approved').values_list('user_id', flat=True)
            qs = qs.filter(pk__in=partner_users)
        elif user_type == 'tourists':
            partner_users = PartnerProfile.objects.values_list('user_id', flat=True)
            qs = qs.filter(is_staff=False, is_superuser=False).exclude(pk__in=partner_users)
        elif user_type == 'staff':
            qs = qs.filter(is_staff=True)
        elif user_type == 'inactive':
            qs = qs.filter(is_active=False)
        
        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(phone_number__icontains=q)
            )

        # Date Range Filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(date_joined__date__gte=date_from)
        if date_to:
            qs = qs.filter(date_joined__date__lte=date_to)
        
        return qs
    
    def get_context_data(self, **kwargs):
        from users.models import PartnerProfile
        from django.utils import timezone
        from datetime import timedelta
        
        context = super().get_context_data(**kwargs)
        
        all_users = User.objects.all()
        partner_users = PartnerProfile.objects.filter(status='approved').values_list('user_id', flat=True)
        
        # Stats
        context['stats'] = {
            'total': all_users.count(),
            'partners': len(partner_users),
            'tourists': all_users.filter(is_staff=False, is_superuser=False).exclude(pk__in=partner_users).count(),
            'staff': all_users.filter(is_staff=True).count(),
            'inactive': all_users.filter(is_active=False).count(),
            'new_this_week': all_users.filter(date_joined__gte=timezone.now() - timedelta(days=7)).count(),
        }
        
        # Current filters
        context['current_type'] = self.request.GET.get('type', 'all')
        context['search_query'] = self.request.GET.get('q', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        return context


class AdminUserToggleActiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, "لا يمكنك تعديل حساب المسؤول")
            return redirect('admin_users_list')
            
        user.is_active = not user.is_active
        user.save()
        
        if request.headers.get('HX-Request'):
            # Return updated button only
            from django.template.loader import render_to_string
            context = {'user': user}
            # We'll render a small partial for the button
            return render(request, 'management/partials/user_toggle_button.html', context)
        
        action = "تفعيل" if user.is_active else "تعطيل"
        messages.success(request, f"تم {action} حساب {user.username}")
        return redirect('admin_users_list')
        
    def test_func(self):
        return self.request.user.is_staff

# ==========================================
# 9. System Health & Landmarks (Placeholders)
# ==========================================

class SystemHealthView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_dashboard/health.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        import os
        import sys
        import django
        from django.db import connection
        from django.core.cache import cache
        from django.conf import settings
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        # System Info
        context['system_info'] = {
            'python_version': sys.version.split()[0],
            'django_version': django.get_version(),
            'debug_mode': settings.DEBUG,
            'timezone': str(settings.TIME_ZONE),
            'language': settings.LANGUAGE_CODE,
        }
        
        # Database Health
        db_status = {'status': 'healthy', 'message': 'متصل'}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            # Get table count
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                else:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = DATABASE()
                    """)
                db_status['tables'] = cursor.fetchone()[0]
        except Exception as e:
            db_status = {'status': 'error', 'message': str(e)}
        context['db_status'] = db_status
        
        # Cache Health
        cache_status = {'status': 'healthy', 'message': 'يعمل'}
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                cache_status = {'status': 'warning', 'message': 'تحذير في القراءة'}
            cache.delete('health_check')
        except Exception as e:
            cache_status = {'status': 'error', 'message': str(e)}
        context['cache_status'] = cache_status
        
        # Celery Status (check if any workers are running)
        celery_status = {'status': 'unknown', 'message': 'غير محدد'}
        try:
            from management.tasks import check_ad_expirations
            # We can't easily check celery without actually pinging workers
            celery_status = {'status': 'healthy', 'message': 'تم تكوين المهام'}
        except Exception as e:
            celery_status = {'status': 'warning', 'message': 'غير متاح'}
        context['celery_status'] = celery_status
        
        # Disk Usage
        import shutil
        import platform
        try:
            path = "C:\\" if platform.system() == "Windows" else "/"
            total, used, free = shutil.disk_usage(path)
            disk_percent = (used / total) * 100
            context['disk_usage'] = {
                'total_gb': round(total / (1024**3), 1),
                'used_gb': round(used / (1024**3), 1),
                'free_gb': round(free / (1024**3), 1),
                'percent': round(disk_percent, 1),
                'status': 'healthy' if disk_percent < 80 else 'warning' if disk_percent < 90 else 'error'
            }
        except:
            context['disk_usage'] = {'status': 'unknown', 'percent': 0}
        
        # Model Counts
        from users.models import User
        from places.models import Establishment
        from interactions.models import Review, Report, Favorite
        from management.models import Advertisement
        
        context['model_counts'] = {
            'users': User.objects.count(),
            'establishments': Establishment.objects.count(),
            'reviews': Review.objects.count(),
            'reports': Report.objects.count(),
            'favorites': Favorite.objects.count(),
            'ads': Advertisement.objects.count(),
        }
        
        # Recent Activity
        from management.models import AuditLog
        context['recent_logs'] = AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
        
        # Timestamp
        context['check_time'] = timezone.now()
        
        return context

class TourismOfficeLandmarkListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Landmark
    template_name = 'admin_dashboard/landmark_list.html'
    
    def test_func(self):
        return self.request.user.is_staff

class TourismOfficeLandmarkDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Landmark
    template_name = 'admin_dashboard/landmark_detail.html'
    
    def test_func(self):
        return self.request.user.is_staff

class TourismOfficeVerifyLandmarkView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk):
        return redirect('tourism_landmark_list')
        
    def test_func(self):
        return self.request.user.is_staff

class TourismOfficeLandmarkEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Landmark
    fields = ['name', 'description']
    template_name = 'admin_dashboard/landmark_form.html'
    
    def test_func(self):
        return self.request.user.is_staff

# ==========================================
# 10. Reporting
# ==========================================

from .services.reporting_service import ReportingService
from django.http import HttpResponse

class AdminExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, report_type):
        timestamp = timezone.now().strftime('%Y%m%d_%H%M')
        
        if report_type == 'users':
            csv_content = ReportingService.export_users_csv()
            filename = f"users_{timestamp}.csv"
        elif report_type == 'partners':
            csv_content = ReportingService.export_partners_csv()
            filename = f"partners_{timestamp}.csv"
        elif report_type == 'places':
            csv_content = ReportingService.export_places_csv()
            filename = f"places_{timestamp}.csv"
        else:
            messages.error(request, "Invalid report type")
            return redirect('custom_admin_dashboard')
            
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    def test_func(self):
        return self.request.user.is_staff


# ==========================================
# 11. Pending Changes (Field-Level Approval)
# ==========================================

from .models import PendingChange
from .services.pending_change_service import PendingChangeService
from ibb_guide.core_utils import get_client_ip


class PendingChangeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all pending field changes for admin review."""
    model = PendingChange
    template_name = 'management/pending_changes_list.html'
    context_object_name = 'pending_changes'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        qs = PendingChange.objects.filter(status='pending').select_related(
            'establishment', 'requested_by'
        )
        
        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(establishment__name__icontains=q) |
                Q(requested_by__username__icontains=q) |
                Q(field_name__icontains=q)
            )
            
        # Sort
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['created_at', '-created_at']:
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by('-created_at')
            
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stats
        context['total_pending'] = PendingChange.objects.filter(status='pending').count()
        
        # Recent Activity for Sidebar
        context['recent_activity'] = PendingChange.objects.exclude(status='pending').select_related(
            'establishment', 'requested_by'
        ).order_by('-reviewed_at')[:10]
        
        return context


class PendingChangeActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Process approve/reject actions on pending changes."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        pending_change = get_object_or_404(PendingChange, pk=pk)
        action = request.POST.get('action')
        note = request.POST.get('note', '')
        ip = get_client_ip(request)
        
        if action == 'approve':
            success, message = PendingChangeService.approve_change(
                admin_user=request.user,
                pending_change=pending_change,
                ip=ip
            )
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        elif action == 'reject':
            success, message = PendingChangeService.reject_change(
                admin_user=request.user,
                pending_change=pending_change,
                note=note,
                ip=ip
            )
            if success:
                messages.warning(request, message)
            else:
                messages.error(request, message)
        else:
            messages.error(request, "إجراء غير صالح")
        
        return redirect('admin_pending_changes')


class PendingChangeDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View details of a single pending change."""
    model = PendingChange
    template_name = 'management/pending_change_detail.html'
    context_object_name = 'pending_change'
    
    def test_func(self):
        return self.request.user.is_staff


# ==========================================
# Establishment Approval Workflow
# ==========================================

class EstablishmentApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Office dashboard for reviewing pending establishment approvals.
    Fast UI for approve/reject with quick preview.
    """
    model = Establishment
    template_name = 'management/establishment_approval_list.html'
    context_object_name = 'pending_establishments'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        qs = Establishment.objects.filter(
            approval_status='pending'
        ).select_related('owner', 'category')
        
        # Search
        q = self.request.GET.get('q', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(owner__username__icontains=q) |
                Q(city__icontains=q)
            )
            
        # Sort
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['created_at', '-created_at']:
            qs = qs.order_by(sort)
        else:
            qs = qs.order_by('-created_at')
            
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recently approved/rejected for reference
        context['recently_approved'] = Establishment.objects.filter(
            approval_status='approved'
        ).select_related('owner', 'approved_by').order_by('-approved_at')[:5]
        
        context['recently_rejected'] = Establishment.objects.filter(
            approval_status='rejected'
        ).select_related('owner').order_by('-updated_at')[:5]
        
        context['pending_count'] = Establishment.objects.filter(approval_status='pending').count()
        
        return context


class EstablishmentApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """One-click approve establishment."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        from ibb_guide.core_utils import get_client_ip
        
        establishment = get_object_or_404(Establishment, pk=pk)
        
        if establishment.approval_status != 'pending':
            messages.warning(request, f"المنشأة '{establishment.name}' ليست في حالة انتظار")
            return redirect('admin_establishment_approval')
        
        success, message = establishment.approve(
            by_admin=request.user,
            ip=get_client_ip(request)
        )
        
        if success:
            messages.success(request, f"✓ تمت الموافقة على '{establishment.name}'")
        else:
            messages.error(request, message)
        
        return redirect('admin_establishment_approval')


class EstablishmentRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Reject establishment with reason."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        from ibb_guide.core_utils import get_client_ip
        
        establishment = get_object_or_404(Establishment, pk=pk)
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, "يجب إدخال سبب الرفض")
            return redirect('admin_establishment_approval')
        
        if establishment.approval_status != 'pending':
            messages.warning(request, f"المنشأة '{establishment.name}' ليست في حالة انتظار")
            return redirect('admin_establishment_approval')
        
        success, message = establishment.reject(
            by_admin=request.user,
            reason=reason,
            ip=get_client_ip(request)
        )
        
        if success:
            messages.success(request, f"✗ تم رفض '{establishment.name}'")
        else:
            messages.error(request, message)
        
        return redirect('admin_establishment_approval')


# ==========================================
# Partner Approval Workflow (Fast UX)
# ==========================================

class PartnerApprovalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Office dashboard for reviewing pending partner upgrade requests.
    Fast UI for approve/reject with quick data preview.
    """
    model = PartnerProfile
    template_name = 'management/partner_approval_list.html'
    context_object_name = 'pending_partners'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return PartnerProfile.objects.filter(
            status='pending'
        ).select_related('user').order_by('-submitted_at', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = PartnerProfile.objects.filter(status='pending').count()
        context['recently_approved'] = PartnerProfile.objects.filter(
            status='approved'
        ).select_related('user', 'reviewed_by').order_by('-reviewed_at')[:5]
        context['recently_rejected'] = PartnerProfile.objects.filter(
            status='rejected'
        ).select_related('user').order_by('-reviewed_at')[:5]
        return context


class PartnerApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """One-click approve partner request. Sets role to Partner."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        from users.models import Role
        
        profile = get_object_or_404(PartnerProfile, pk=pk)
        
        if profile.status != 'pending':
            messages.warning(request, "الطلب ليس في حالة انتظار")
            return redirect('admin_partner_approval')
        
        # Set profile to approved
        profile.status = 'approved'
        profile.is_approved = True
        profile.reviewed_by = request.user
        profile.reviewed_at = timezone.now()
        profile.save()
        
        # Assign Partner role to user
        partner_role, _ = Role.objects.get_or_create(name='Partner')
        profile.user.role = partner_role
        profile.user.account_status = 'active'
        profile.user.is_email_verified = True  # Auto-verify email on approval
        profile.user.save()
        
        # Notify partner
        try:
            from interactions.notifications.partner import PartnerNotifications
            PartnerNotifications.notify_partner_approved(profile)
        except Exception:
            pass
        
        # Audit log
        try:
            AuditLog.objects.create(
                actor=request.user,
                action='partner_approved',
                entity_type='PartnerProfile',
                entity_id=str(profile.pk),
                changes={'status': {'before': 'pending', 'after': 'approved'}},
            )
        except Exception:
            pass
        
        messages.success(request, f"✓ تمت الموافقة على '{profile.user.get_full_name() or profile.user.username}'")
        return redirect('admin_partner_approval')


class PartnerRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Reject partner request with reason."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        profile = get_object_or_404(PartnerProfile, pk=pk)
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, "يجب إدخال سبب الرفض")
            return redirect('admin_partner_approval')
        
        if profile.status != 'pending':
            messages.warning(request, "الطلب ليس في حالة انتظار")
            return redirect('admin_partner_approval')
        
        # Set profile to rejected
        profile.status = 'rejected'
        profile.is_approved = False
        profile.rejection_reason = reason
        profile.reviewed_by = request.user
        profile.reviewed_at = timezone.now()
        profile.save()
        
        # Notify partner
        try:
            from interactions.notifications.partner import PartnerNotifications
            PartnerNotifications.notify_partner_rejected(profile, reason)
        except Exception:
            pass
        
        # Audit log
        try:
            AuditLog.objects.create(
                actor=request.user,
                action='partner_rejected',
                entity_type='PartnerProfile',
                entity_id=str(profile.pk),
                changes={
                    'status': {'before': 'pending', 'after': 'rejected'},
                    'rejection_reason': reason
                },
            )
        except Exception:
            pass
        
        messages.success(request, f"✗ تم رفض '{profile.user.get_full_name() or profile.user.username}'")
        return redirect('admin_partner_approval')


# ==========================================
# 12. Events Management
# ==========================================

class AdminEventListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Event
    template_name = 'admin_dashboard/event_list.html'
    context_object_name = 'events'
    ordering = ['-start_datetime']
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        now = timezone.now()
        context['total_events'] = Event.objects.count()
        context['active_events'] = Event.objects.filter(end_datetime__gte=now).count()
        context['featured_events'] = Event.objects.filter(is_featured=True).count()
        return context


class AdminEventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    fields = ['title', 'description', 'location', 'start_datetime', 'end_datetime', 'price', 'event_type', 'is_featured', 'cover_image']
    template_name = 'admin_dashboard/event_form.html'
    success_url = reverse_lazy('admin_event_list')
    
    def test_func(self):
        return self.request.user.is_staff

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Accept datetime-local HTML5 input format (YYYY-MM-DDTHH:MM)
        for field_name in ['start_datetime', 'end_datetime']:
            form.fields[field_name].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        return form

class AdminEventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    fields = ['title', 'description', 'location', 'start_datetime', 'end_datetime', 'price', 'event_type', 'is_featured', 'cover_image']
    template_name = 'admin_dashboard/event_form.html'
    success_url = reverse_lazy('admin_event_list')
    
    def test_func(self):
        return self.request.user.is_staff

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Accept datetime-local HTML5 input format (YYYY-MM-DDTHH:MM)
        for field_name in ['start_datetime', 'end_datetime']:
            form.fields[field_name].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
        return form

class AdminEventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'admin_dashboard/confirm_delete.html'
    success_url = reverse_lazy('admin_event_list')
    
    def test_func(self):
        return self.request.user.is_staff



# ==========================================
# 13. Secure File View
# ==========================================
import os
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponseForbidden

def secure_file_view(request, file_path):
    """
    Serve protected files only to staff members.
    Used for sensitive documents like ID cards and Commercial Registers.
    """
    if not request.user.is_staff:
        return HttpResponseForbidden("Permission Denied")
    
    # Construct full path and normalize
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_path))
    
    # Security Check: Ensure path is within MEDIA_ROOT
    if not full_path.startswith(str(settings.MEDIA_ROOT)):
        raise Http404("File not found")
        
    if not os.path.exists(full_path):
        # Graceful fallback for local dev or missing files
        if settings.DEBUG:
            # Return an SVG placeholder
            svg = f"""<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8f9fa"/>
            <rect width="100%" height="100%" fill="none" stroke="#dee2e6" stroke-width="4"/>
            <text x="50%" y="45%" font-family="sans-serif" font-size="24" fill="#6c757d" text-anchor="middle" font-weight="bold">File Not Found</text>
            <text x="50%" y="60%" font-family="sans-serif" font-size="14" fill="#adb5bd" text-anchor="middle">{os.path.basename(file_path)}</text>
            <text x="50%" y="70%" font-family="sans-serif" font-size="12" fill="#adb5bd" text-anchor="middle">(Local Development)</text>
            </svg>"""
            return HttpResponse(svg, content_type="image/svg+xml")

        raise Http404("File not found")
        
    return FileResponse(open(full_path, 'rb'))


# ==========================================
# 14. Data Export View
# ==========================================
import csv
from django.http import HttpResponse

class AdminExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, model_type):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_type}_export.csv"'
        response.write(u'\ufeff'.encode('utf8')) # BOM (optional, for Excel compatibility)
        
        writer = csv.writer(response)
        
        if model_type == 'places':
            writer.writerow(['ID', 'Name', 'Category', 'Owner', 'City', 'Status', 'Created At'])
            places = Establishment.objects.all().select_related('category', 'owner')
            for place in places:
                writer.writerow([
                    place.pk, 
                    place.name, 
                    place.category.name if place.category else '', 
                    place.owner.get_full_name() or place.owner.username,
                    place.get_directorate_display(),
                    place.approval_status,
                    place.created_at.strftime('%Y-%m-%d')
                ])
                
        elif model_type == 'users':
             writer.writerow(['ID', 'Username', 'Email', 'Full Name', 'Role', 'Date Joined'])
             users = User.objects.all().select_related('role')
             for user in users:
                 writer.writerow([
                     user.pk,
                     user.username,
                     user.email,
                     user.get_full_name(),
                     user.role.name if user.role else 'User',
                     user.date_joined.strftime('%Y-%m-%d')
                 ])

        return response


# ==========================================
# 10. Global Search
# ==========================================

class AdminGlobalSearchView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_dashboard/search_results.html'
    
    def test_func(self):
        return self.request.user.is_staff
        
    def get_context_data(self, **kwargs):
        from django.db.models import Q
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        
        if query:
            # 1. Search Users
            context['users'] = User.objects.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(phone_number__icontains=query)
            )[:10]
            
            # 2. Search Establishments
            context['establishments'] = Establishment.objects.filter(
                Q(name__icontains=query) |
                Q(license_number__icontains=query)
            ).select_related('owner')[:10]
            
        return context

# ==========================================
# 17. Dynamic System Settings
# ==========================================

class AdminSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Manage system settings dynamically.
    Displays a form with all settings and handles updates.
    """
    template_name = 'management/settings/list.html'

    def test_func(self):
        return self.request.user.is_superuser # Limit to superusers for safety

    def get(self, request):
        from management.models import SystemSetting
        settings = SystemSetting.objects.all().order_by('key')
        return render(request, self.template_name, {'settings': settings})

    def post(self, request):
        from management.models import SystemSetting
        from management.services.settings_service import SettingsService

        # Iterate over all settings and update them
        settings = SystemSetting.objects.all()
        
        for setting in settings:
            # Check if value is in POST
            val = request.POST.get(f'setting_{setting.key}')
            
            # Handle checkboxes (boolean)
            if setting.data_type == 'boolean':
                val = 'true' if val else 'false'
            
            # Only update if changed (optional optimization, but Service handles cache)
            if val is not None:
                SettingsService.set(setting.key, val, setting.data_type, setting.description)
        
        messages.success(request, "تم تحديث الإعدادات بنجاح.")
        return redirect('admin_settings')
# ==========================================
# 15. Favorites Management (System-wide)
# ==========================================

class AdminFavoriteListView(StaffAdminRequiredMixin, ListView):
    model = Favorite
    template_name = 'management/admin_favorite_list.html'
    context_object_name = 'favorites_list'
    paginate_by = 50

    def get_queryset(self):
        from django.db.models import Q
        
        qs = Favorite.objects.select_related('user', 'place', 'place__category').order_by('-created_at')
        
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(user__username__icontains=q) |
                Q(place__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_favorites'] = Favorite.objects.count()
        return context

class AdminBulkDeleteFavoritesView(StaffAdminRequiredMixin, View):
    def post(self, request):
        favorite_pks = request.POST.getlist('favorite_pks')
        if favorite_pks:
            count, _ = Favorite.objects.filter(pk__in=favorite_pks).delete()
            messages.success(request, f"تم حذف {count} من المفضلات بنجاح.")
        else:
            messages.warning(request, "لم يتم تحديد أي عناصر للحذف.")
        return redirect('admin_favorite_list')
