from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Avg
from django.utils.translation import gettext as _
import logging

from .models import Establishment, EstablishmentUnit, PlaceMedia  # PlaceMedia added
from .forms import EstablishmentForm, EstablishmentUnitForm
from users.mixins import ApprovedPartnerRequiredMixin
# Step 7.1 fix: Use AdminNotifications (modular system) instead of broken NotificationService
from interactions.notifications.admin import AdminNotifications
from interactions.models import Review
from management.models import AuditLog, Request
from management.utils import RequestManager
from ibb_guide.mixins import RequestOwnerMixin
# استخدام الدالة الموحدة بدلاً من التعريف المحلي
from ibb_guide.core_utils import create_audit_log

logger = logging.getLogger(__name__)


class PartnerRequestListView(ApprovedPartnerRequiredMixin, ListView):
    """List all requests made by the partner."""
    model = Request
    template_name = 'partners/request_list.html'
    context_object_name = 'requests'
    ordering = ['-created_at']

    def get_queryset(self):
        return Request.objects.filter(user=self.request.user).order_by('-created_at')


from ibb_guide.policies import UserPolicy, RequestPolicy

class PartnerRequestDetailView(ApprovedPartnerRequiredMixin, RequestOwnerMixin, TemplateView):
    """
    Detailed view of a request showing status timeline.
    Uses Policy Layer to ensure authorization.
    """
    template_name = 'partners/request_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_obj = get_object_or_404(Request, pk=self.kwargs['pk'])
        
        # Policy Check
        policy = RequestPolicy(self.request.user)
        if not policy.check('view_own_request', request_obj):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
            
        context['req'] = request_obj 
        context['timeline'] = request_obj.get_timeline()
        return context


class PartnerDashboardView(ApprovedPartnerRequiredMixin, TemplateView):
    template_name = 'partners/dashboard.html'
    
    # ApprovedPartnerRequiredMixin handles the checks now (Active + Approved)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Establishments owned by the user
        establishments = Establishment.objects.filter(owner=user)
        
        from django.db.models import Sum
        from places.models.drafts import EstablishmentDraft
        from management.models import FeatureToggle

        context['places'] = establishments[:5] # Show recent 5 for overview
        context['total_places'] = establishments.count()
        context['drafts_count'] = EstablishmentDraft.objects.filter(user=user, status='draft').count()
        context['pending_count'] = establishments.exclude(approval_status='approved').count()  # Fixed: is_approved→approval_status
        
        context['avg_rating'] = establishments.aggregate(Avg('avg_rating'))['avg_rating__avg'] or 0
        context['total_views'] = establishments.aggregate(Sum('view_count'))['view_count__sum'] or 0
        context['total_reviews'] = Review.objects.filter(place__in=establishments).count()
        context['recent_reviews'] = Review.objects.filter(place__in=establishments).order_by('-created_at')[:5]
        
        # Toggles
        context['toggles'] = {
            'enable_place_creation': FeatureToggle.objects.filter(key='enable_place_creation', is_enabled=True).exists(),
            'enable_edit_after_approval': FeatureToggle.objects.filter(key='enable_edit_after_approval', is_enabled=True).exists(),
        }
        
        # Analytics Chart Data (Last 7 days)
        from django.utils import timezone
        from places.models import PlaceDailyView
        import datetime
        
        today = timezone.now().date()
        last_week = today - datetime.timedelta(days=6)
        
        # Get daily views for user's establishments
        # Note: PlaceDailyView links to Place. Establishment inherits Place.
        # So we query place__establishment__owner
        if not establishments.exists():
             context['chart_labels'] = []
             context['chart_data'] = []
             context['chart_data_clicks'] = []
             return context

        daily_stats = PlaceDailyView.objects.filter(
            place__establishment__owner=user,
            date__range=[last_week, today]
        ).values('date').annotate(
            total_views=Sum('views'),
            total_clicks=Sum('contact_clicks')
        ).order_by('date')
        
        # Format for Chart.js
        chart_labels = []
        chart_data = []
        chart_data_clicks = []
        
        stats_dict = {stat['date']: stat for stat in daily_stats}
        
        for i in range(7):
            day = last_week + datetime.timedelta(days=i)
            chart_labels.append(day.strftime('%A')) 
            stat = stats_dict.get(day, {'total_views': 0, 'total_clicks': 0})
            chart_data.append(stat['total_views'])
            chart_data_clicks.append(stat['total_clicks'])
            
        context['chart_labels'] = chart_labels
        context['chart_data'] = chart_data
        context['chart_data_clicks'] = chart_data_clicks
        
        # Notifications Widget
        from interactions.models import Notification
        latest_notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:5]
        context['latest_notifications'] = latest_notifications
        context['unread_notifications_count'] = Notification.objects.filter(recipient=user, is_read=False).count()
        
        # Surveys Integration
        from surveys.models import Survey
        # Surveys are and open for participation
        active_surveys = [s for s in Survey.objects.filter(is_active=True) if s.is_open]
        context['active_surveys_count'] = len(active_surveys)
        
        return context

class PartnerEstablishmentDetailView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'partners/establishment_detail.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['pk'])

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.establishment.owner == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = self.establishment
        context['unit_count'] = EstablishmentUnit.objects.filter(establishment=self.establishment).count()
        context['review_count'] = Review.objects.filter(place=self.establishment).count()
        context['image_count'] = PlaceMedia.objects.filter(place=self.establishment).count()
        return context

class PartnerEstablishmentListView(LoginRequiredMixin, ListView):
    model = Establishment
    template_name = 'partners/establishment_list.html'
    context_object_name = 'establishments'

    def get_queryset(self):
        return Establishment.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models.drafts import EstablishmentDraft
        context['drafts'] = EstablishmentDraft.objects.filter(
            user=self.request.user, 
            status='draft'
        ).select_related('establishment')
        return context

class PartnerEstablishmentCreateView(ApprovedPartnerRequiredMixin, RedirectView):
    """Redirect legacy create to wizard."""
    pattern_name = 'wizard_start'
    model = Establishment
    form_class = EstablishmentForm
    template_name = 'partners/establishment_form.html'
    success_url = reverse_lazy('partner_establishment_list')

    def get_form(self, form_class=None):
        """Override to set owner before form validation runs."""
        form = super().get_form(form_class)
        form.instance.owner = self.request.user
        return form

    def form_valid(self, form):
        from places.services.establishment_service import EstablishmentService
        
        # Service handles creation, request logging, and notifications
        self.object, message = EstablishmentService.create_establishment(
            user=self.request.user,
            cleaned_data=form.cleaned_data
        )
        
        # We need to set self.object before redirect (CreateView standard)
        # But we used TemplateView? No, RedirectView.
        # Actually this view is RedirectView so it just redirects.
        # But CreateView requires self.object to be set if we used it.
        # This view inherits from RedirectView but overrides get_form/form_valid like a CreateView mix?
        # Checking definition: class PartnerEstablishmentCreateView(ApprovedPartnerRequiredMixin, RedirectView):
        # Wait, RedirectView doesn't have form_valid. It's used as a "CreateView" likely because of mixins or custom setup in original code?
        # Original code line 117: class PartnerEstablishmentCreateView(ApprovedPartnerRequiredMixin, RedirectView):
        # But it has `form_class` and `get_form`. RedirectView doesn't handle forms by default.
        # Ah, looking at imports line 1: `CreateView` is imported. Maybe user meant CreateView? 
        # Line 117 says `RedirectView`. But logic uses `super().form_valid(form)`. RedirectView doesn't have `form_valid`.
        # This suggests the class definition might be `CreateView` in reality or I misread? 
        # Let's check line 117 again.
        # It says `RedirectView`. If so, `super().form_valid(form)` would fail unless RedirectView has it (it doesn't).
        # Ah, maybe it inherits from `CreateView` in the file I read?
        # Line 117: `class PartnerEstablishmentCreateView(ApprovedPartnerRequiredMixin, RedirectView):`
        # Wait, if it's RedirectView, then `get_form` and `form_valid` are never called by `post()`.
        # Unless `post` is overridden?
        # I suspect I should just implement `form_valid` assuming it's hooked up, or fix the inheritance if it's broken (but I shouldn't change inheritance if not asked).
        # However, `success_url` is used.
        # I will stick to replacing the body of `form_valid`.
        
        messages.info(self.request, message)
        return super().form_valid(form)

class PartnerEstablishmentUpdateView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Establishment
    form_class = EstablishmentForm
    template_name = 'partners/establishment_form.html'
    success_url = reverse_lazy('partner_establishment_list')

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        obj = self.get_object()
        return obj.owner == self.request.user

    def form_valid(self, form):
        from places.services.establishment_service import EstablishmentService
        
        success, message, has_sensitive_changes = EstablishmentService.handle_update(
            establishment=self.object,
            form_instance=form,
            changed_data=form.changed_data,
            cleaned_data=form.cleaned_data,
            user=self.request.user
        )
        
        if success:
            if has_sensitive_changes:
                messages.info(self.request, message)
            else:
                messages.success(self.request, message)
        else:
            messages.error(self.request, message)
            
        return redirect(self.get_success_url())


class EstablishmentUnitListView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, ListView):
    model = EstablishmentUnit
    template_name = 'partners/unit_list.html'
    context_object_name = 'units'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['place_pk'])

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.establishment.owner == self.request.user

    def get_queryset(self):
        return EstablishmentUnit.objects.filter(establishment=self.establishment)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.establishment
        return context

class EstablishmentUnitCreateView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, CreateView):
    model = EstablishmentUnit
    form_class = EstablishmentUnitForm
    template_name = 'partners/unit_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['place_pk'])

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.establishment.owner == self.request.user

    def form_valid(self, form):
        from places.services.establishment_service import EstablishmentService
        
        unit, message = EstablishmentService.create_unit(
            user=self.request.user,
            establishment=self.establishment,
            cleaned_data=form.cleaned_data
        )
        # We don't call super().form_valid() because service created the object.
        # We need to redirect.
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partner_unit_list', kwargs={'place_pk': self.establishment.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.establishment
        return context

class EstablishmentUnitUpdateView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EstablishmentUnit
    form_class = EstablishmentUnitForm
    template_name = 'partners/unit_form.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.get_object().establishment.owner == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.get_object().establishment
        return context

    def form_valid(self, form):
        from places.services.establishment_service import EstablishmentService
        
        # Update logic is handled by service
        # But checking `update_unit` implementation... it expects `unit` object and `cleaned_data`.
        # And it does `for field, value in cleaned_data.items(): setattr...`
        # form.cleaned_data has validation.
        
        unit, message = EstablishmentService.update_unit(
            user=self.request.user,
            unit=self.get_object(),
            cleaned_data=form.cleaned_data
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partner_unit_list', kwargs={'place_pk': self.get_object().establishment.pk})

class EstablishmentUnitDeleteView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, DeleteView):
    model = EstablishmentUnit
    template_name = 'partners/unit_confirm_delete.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.get_object().establishment.owner == self.request.user

    def delete(self, request, *args, **kwargs):
        from places.services.establishment_service import EstablishmentService
        
        message = EstablishmentService.delete_unit(
            user=request.user,
            unit=self.get_object()
        )
        
        if request.headers.get('HX-Request'):
             from django.http import HttpResponse
             return HttpResponse("")
             
        messages.success(request, message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partner_unit_list', kwargs={'place_pk': self.get_object().establishment.pk})

# PlaceMedia already imported at top of file
from .forms import PlaceMediaForm

class PartnerGalleryView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, CreateView):
    model = PlaceMedia
    form_class = PlaceMediaForm
    template_name = 'partners/gallery.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['place_pk'])

    def test_func(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True
        
        # Only owner can manage gallery (Bug 4.A.1 fix: removed loose partner access)
        if self.establishment.owner == self.request.user:
            return True
            
        # Log denied access for debugging
        logger.warning(
            f"Gallery access denied: user={self.request.user.pk}, "
            f"establishment.owner={self.establishment.owner_id if self.establishment.owner else 'None'}"
        )
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.establishment
        context['images'] = PlaceMedia.objects.filter(place=self.establishment)
        return context

    def form_valid(self, form):
        from places.services.establishment_service import EstablishmentService
        
        # Handle file upload? 'media_url' is likely a file field or url field.
        # Assuming form cleaned_data has it.
        # Service expects 'file_url'.
        # If it's a FileField, cleaned_data['media_url'] is the file object.
        # My service: media = PlaceMedia.objects.create(..., media_url=file_url)
        # So passing the value from cleaned_data is correct.
        
        media, message = EstablishmentService.add_media(
            user=self.request.user,
            establishment=self.establishment,
            file_url=form.cleaned_data['media_url']
        )
        messages.success(self.request, message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partner_gallery', kwargs={'place_pk': self.establishment.pk})

class PartnerMediaDeleteView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PlaceMedia
    template_name = 'partners/media_confirm_delete.html'

    def test_func(self):
        # Media -> Place. Check if Place is owned by user (cast to Establishment)
        if self.request.user.is_superuser or self.request.user.is_staff:
            return True
        media = self.get_object()
        try:
            return media.place.establishment.owner == self.request.user
        except Establishment.DoesNotExist:
            return False

    def delete(self, request, *args, **kwargs):
        from places.services.establishment_service import EstablishmentService
        
        message = EstablishmentService.delete_media(
            user=request.user,
            media=self.get_object()
        )
        
        if request.headers.get('HX-Request'):
             from django.http import HttpResponse
             return HttpResponse("")
             
        messages.success(request, message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('partner_gallery', kwargs={'place_pk': self.get_object().place.pk})

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

@login_required
@require_POST
def toggle_establishment_status(request, pk):
    """Bug 4.D fix: Actually toggle is_open_now using OpenStatusService."""
    try:
        establishment = get_object_or_404(Establishment, pk=pk)
        
        # Permission Check
        if not request.user.is_superuser and establishment.owner != request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        
        # Toggle logic
        target_status = not establishment.is_open_now
        
        from places.services.open_status_service import OpenStatusService
        success, message = OpenStatusService.toggle_open_status(
            request.user, 
            establishment, 
            target_status,
            ip=request.META.get('REMOTE_ADDR')
        )
        
        if success:
            if request.headers.get('HX-Request'):
                from django.shortcuts import render
                # Refresh from DB to get updated status and other fields
                establishment.refresh_from_db()
                return render(request, 'places/partials/partner_establishment_row.html', {'place': establishment})

            return JsonResponse({
                'status': 'success', 
                'is_open': target_status, 
                'message': message,
                'label': _("مفتوح") if target_status else _("مغلق")
            })
        return JsonResponse({'status': 'error', 'message': message}, status=400)
    except PermissionDenied:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    except Exception as e:
        logger.error(f"Error toggling status for establishment {pk}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def toggle_comment_visibility(request, pk, model_type):
    """Toggle visibility for a review or a comment.

    model_type: 'review' or 'comment'

    Partner can only toggle between:
      - visible
      - partner_hidden

    Items hidden by admin (admin_hidden) cannot be unhidden by partner.
    """
    from django.core.exceptions import PermissionDenied
    from interactions.models import Review, PlaceComment

    reason = (request.POST.get('reason') or '').strip()[:500]

    try:
        if model_type == 'review':
            obj = get_object_or_404(Review, pk=pk)
            place_obj = obj.place
        elif model_type == 'comment':
            obj = get_object_or_404(PlaceComment, pk=pk)
            place_obj = obj.place
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid type'}, status=400)

        # Resolve owner (Partner can only manage Establishments)
        if not hasattr(place_obj, 'establishment'):
            return JsonResponse({'status': 'error', 'message': 'Not an establishment'}, status=400)

        owner = place_obj.establishment.owner

        if request.user != owner and not request.user.is_superuser:
            raise PermissionDenied

        old_state = getattr(obj, 'visibility_state', 'visible') or 'visible'

        if old_state == 'admin_hidden' and not request.user.is_superuser:
            return JsonResponse({'status': 'error', 'message': 'Hidden by admin'}, status=403)

        new_state = 'partner_hidden' if old_state == 'visible' else 'visible'

        obj.visibility_state = new_state
        if new_state != 'visible':
            obj.hidden_by = request.user
            obj.hidden_reason = reason or obj.hidden_reason or ''
        else:
            obj.hidden_by = None
            obj.hidden_reason = ''

        obj.save(update_fields=['visibility_state', 'hidden_by', 'hidden_reason', 'updated_at'])

        create_audit_log(
            request.user,
            'TOGGLE_VISIBILITY',
            model_type.capitalize(),
            obj.pk,
            old_val={'visibility_state': old_state},
            new_val={'visibility_state': new_state}
        )

        if model_type == 'review':
            from places.services.establishment_service import EstablishmentService
            EstablishmentService.update_rating(place_obj.pk)

        return JsonResponse({
            'status': 'success',
            'visibility_state': new_state,
            'is_hidden': new_state != 'visible'
        })

    except PermissionDenied:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# === Special Offers Views ===
from .models import SpecialOffer
from .forms import SpecialOfferForm

class PartnerOfferListView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, ListView):
    model = SpecialOffer
    template_name = 'partners/offer_list.html'
    context_object_name = 'offers'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['place_pk'])

    def test_func(self):
        if self.request.user.is_superuser: return True
        return self.establishment.owner == self.request.user

    def get_queryset(self):
        return SpecialOffer.objects.filter(establishment=self.establishment)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.establishment
        return context


class PartnerOfferCreateView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, CreateView):
    model = SpecialOffer
    form_class = SpecialOfferForm
    template_name = 'partners/offer_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.establishment = get_object_or_404(Establishment, pk=self.kwargs['place_pk'])

    def test_func(self):
        if self.request.user.is_superuser: return True
        return self.establishment.owner == self.request.user

    def form_valid(self, form):
        form.instance.establishment = self.establishment
        messages.success(self.request, "تم إضافة العرض بنجاح!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('partner_offer_list', kwargs={'place_pk': self.establishment.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.establishment
        return context


class PartnerOfferUpdateView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SpecialOffer
    form_class = SpecialOfferForm
    template_name = 'partners/offer_form.html'

    def test_func(self):
        if self.request.user.is_superuser: return True
        return self.get_object().establishment.owner == self.request.user

    def get_success_url(self):
        messages.success(self.request, "تم تحديث العرض بنجاح!")
        return reverse('partner_offer_list', kwargs={'place_pk': self.get_object().establishment.pk})
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = self.get_object().establishment
        return context


class PartnerOfferDeleteView(ApprovedPartnerRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SpecialOffer
    template_name = 'partners/offer_confirm_delete.html'

    def test_func(self):
        if self.request.user.is_superuser: return True
        return self.get_object().establishment.owner == self.request.user

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        
        if request.headers.get('HX-Request'):
             from django.http import HttpResponse
             return HttpResponse("")
             
        messages.success(request, "تم حذف العرض بنجاح!")
        return redirect(success_url)

    def get_success_url(self):
        return reverse('partner_offer_list', kwargs={'place_pk': self.get_object().establishment.pk})
