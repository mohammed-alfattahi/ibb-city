from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Advertisement
from .forms import AdvertisementForm
from users.mixins import ApprovedPartnerRequiredMixin

class PartnerAdsListView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, ListView):
    model = Advertisement
    template_name = 'partners/ads.html'
    context_object_name = 'ads'

    def get_queryset(self):
        return Advertisement.objects.filter(owner=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = self.get_queryset().filter(status='pending').count()
        context['active_count'] = self.get_queryset().filter(status='active').count()
        context['expired_count'] = self.get_queryset().filter(status='expired').count()
        return context

class AdvertisementCreateView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, CreateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'partners/ad_form.html'
    success_url = reverse_lazy('partner_ads') # Will be overridden in form_valid

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def form_valid(self, form):
        # Step 8-أ fix: Use AdService to create draft & invoice
        from .services.ad_service import AdService
        
        try:
            self.object = AdService.create_ad_draft(
                user=self.request.user,
                place=form.cleaned_data['place'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                banner_image=form.cleaned_data['banner_image'],
                placement=form.cleaned_data.get('placement'),
                target_url=form.cleaned_data.get('target_url'),
                duration_days=form.cleaned_data['duration_days'],
                start_date=form.cleaned_data.get('start_date'),
                price=form.cleaned_data.get('price'),
                discount_price=form.cleaned_data.get('discount_price')
            )
            
            messages.success(self.request, "تم إنشاء مسودة الإعلان والفاتورة. يرجى سداد الرسوم لتفعيل العرض.")
            
            # Audit Log
            from management.models import AuditLog
            AuditLog.objects.create(
                user=self.request.user, 
                action='CREATE_DRAFT', 
                table_name='Advertisement', 
                record_id=str(self.object.pk), 
                new_values={'title': self.object.title, 'status': 'draft'}
            )
            
            return redirect('ad_payment', pk=self.object.pk)
            
        except Exception as e:
            messages.error(self.request, f"حدث خطأ أثناء إنشاء الإعلان: {str(e)}")
            return self.form_invalid(form)


class AdvertisementUpdateView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, UpdateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'partners/ad_form.html'
    success_url = reverse_lazy('partner_ads')

    def get_queryset(self):
        return Advertisement.objects.filter(owner=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        review_fields = {
            'title', 'description', 'banner_image', 'placement', 'price',
            'discount_price', 'place', 'target_url', 'duration_days', 'start_date'
        }
        needs_review = any(field in review_fields for field in form.changed_data)
        if needs_review and self.object.status in ['active', 'paused', 'rejected']:
            form.instance.status = 'pending'
            form.instance.admin_notes = ''
            messages.info(self.request, 'تم تحديث الإعلان وإعادته للمراجعة.')

        messages.success(self.request, "تم تحديث الإعلان بنجاح.")
        # Audit Log
        from management.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user, 
            action='UPDATE', 
            table_name='Advertisement', 
            record_id=str(self.object.pk), 
            new_values={'title': self.object.title}
        )
        return super().form_valid(form)


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import PaymentProofForm

class AdPaymentView(LoginRequiredMixin, ApprovedPartnerRequiredMixin, UpdateView):
    model = Advertisement
    form_class = PaymentProofForm
    template_name = 'partners/payment_upload.html'
    
    def get_queryset(self):
        return Advertisement.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        # Step 8-ب fix: Use AdService to submit payment
        from .services.ad_service import AdService
        
        try:
            AdService.submit_payment(
                ad=self.object,
                receipt_image=form.cleaned_data['receipt_image'],
                transaction_ref=form.cleaned_data['transaction_reference']
            )
            
            # Audit Log
            from management.models import AuditLog
            AuditLog.objects.create(
                user=self.request.user, 
                action='SUBMIT_PAYMENT', 
                table_name='Advertisement', 
                record_id=str(self.object.pk), 
                new_values={'status': 'pending', 'ref': form.cleaned_data['transaction_reference']}
            )
            # Notify Admin
            from interactions.notifications.admin import AdminNotifications
            AdminNotifications.notify_ad_payment_uploaded(self.object)
            
            return render(self.request, 'pages/success.html', {
                'title': 'تم استلام السداد!',
                'message': 'شكراً! تم رفع سند السداد بنجاح. سنقوم بمراجعة الطلب وتفعيل الإعلان قريباً.',
                'next_url': reverse('partner_ads')
            })
            
        except Exception as e:
            messages.error(self.request, f"خطأ في معالجة الدفع: {str(e)}")
            return self.form_invalid(form)
