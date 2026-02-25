from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, StreamingHttpResponse
from django.template.loader import render_to_string
import time
import json
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Count
from places.models import Place
from .models import Review, Report, Favorite, Notification
from .forms_public import ReviewForm, ReportForm
from interactions.services.review_service import ReviewService
from ibb_guide.utils.htmx import is_htmx, htmx_redirect, login_redirect_url

from django_ratelimit.decorators import ratelimit
from management.services.moderation_service import analyze_text, log_moderation_event

@require_POST
def review_create(request, place_pk):
    if not request.user.is_authenticated:
        if is_htmx(request):
            return htmx_redirect(login_redirect_url(request))
        return redirect('login')

    place = get_object_or_404(Place, pk=place_pk)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '')

    success, result = ReviewService.create_review(
        request.user, 
        place, 
        rating, 
        comment,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    if request.headers.get('HX-Request'):
        place.refresh_from_db()
        # Refresh reviews and calculate stats
        reviews = place.reviews.filter(visibility_state='visible').order_by('-created_at')
        total = reviews.count()
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        stats_query = reviews.values('rating').annotate(count=Count('rating'))
        for item in stats_query:
            distribution[item['rating']] = item['count']
        
        final_dist = []
        for star in range(5, 0, -1):
            count = distribution.get(star, 0)
            percent = (count / total * 100) if total > 0 else 0
            final_dist.append({'star': star, 'count': count, 'percent': percent})
        
        rating_stats = {'total_reviews': total, 'distribution': final_dist}
        
        # Render reviews list
        list_html = render_to_string('places/partials/reviews_list.html', {
            'reviews': reviews,
            'place': place,
            'user': request.user
        }, request=request)
        
        # Render summary with OOB
        summary_html = render_to_string('places/partials/rating_summary.html', {
            'place': place,
            'rating_stats': rating_stats
        }, request=request)
        
        return HttpResponse(list_html + summary_html)

    return redirect('place_detail', pk=place_pk)

@require_POST
def review_delete(request, place_pk, review_pk):
    if not request.user.is_authenticated:
        if is_htmx(request):
            return htmx_redirect(login_redirect_url(request))
        return redirect('login')

    place = get_object_or_404(Place, pk=place_pk)
    review = get_object_or_404(Review, pk=review_pk, place=place)
    
    # Ownership check
    if review.user != request.user and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    review.delete()

    if request.headers.get('HX-Request'):
        place.refresh_from_db()
        # Same refresh logic as create
        reviews = place.reviews.filter(visibility_state='visible').order_by('-created_at')
        total = reviews.count()
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        stats_query = reviews.values('rating').annotate(count=Count('rating'))
        for item in stats_query:
            distribution[item['rating']] = item['count']
        
        final_dist = []
        for star in range(5, 0, -1):
            count = distribution.get(star, 0)
            percent = (count / total * 100) if total > 0 else 0
            final_dist.append({'star': star, 'count': count, 'percent': percent})
        
        rating_stats = {'total_reviews': total, 'distribution': final_dist}
        
        list_html = render_to_string('places/partials/reviews_list.html', {
            'reviews': reviews,
            'place': place,
            'user': request.user
        }, request=request)
        
        summary_html = render_to_string('places/partials/rating_summary.html', {
            'place': place,
            'rating_stats': rating_stats
        }, request=request)
        
        return HttpResponse(list_html + summary_html)

    return redirect('place_detail', pk=place_pk)

@login_required
@require_POST
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def add_reply(request, review_pk):
    review = get_object_or_404(Review, pk=review_pk)
    content = request.POST.get('content', '')
    
    from interactions.services.comment_service import CommentService
    
    obj, success, message = CommentService.create_comment(
        user=request.user,
        place=review.place,
        review=review,
        content=content,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    if success:
        messages.success(request, message) # Or warning if included in message
    else:
        messages.error(request, message)
        
    return redirect('place_detail', pk=review.place.pk)

@login_required
@require_POST
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def add_place_comment(request, place_pk):
    """
    Step 3: Add standalone comment to a place (not a review).
    """
    place = get_object_or_404(Place, pk=place_pk)
    content = request.POST.get('content', '')
    
    from interactions.services.comment_service import CommentService
    
    obj, success, message = CommentService.create_comment(
        user=request.user,
        place=place,
        review=None,
        content=content,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    if request.headers.get('HX-Request'):
        if success:
            from django.shortcuts import render
            # Calculate rights for the partial
            has_management_rights = False
            if request.user.is_staff:
                has_management_rights = True
            elif hasattr(place, 'establishment') and place.establishment.owner == request.user:
                has_management_rights = True

            return render(request, 'places/partials/comment_card.html', {
                'comment': obj,
                'place': place,
                'user': request.user,
                'has_management_rights': has_management_rights
            })
        else:
            from django.http import HttpResponse
            # Return error as a dismissible alert to prepend
            return HttpResponse(f"""
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    {message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            """)

    if success:
        if "warnings" in message:
            messages.warning(request, message)
        else:
            messages.success(request, "تم إضافة تعليقك بنجاح.")
    else:
        messages.error(request, message)
        
    return redirect('place_detail', pk=place.pk)

@login_required
@require_POST
@ratelimit(key='user', rate='15/h', method='POST', block=True)
def reply_to_comment(request, comment_pk):
    """
    Step 3: Reply to an existing comment (Threaded).
    """
    from interactions.models import PlaceComment
    parent = get_object_or_404(PlaceComment, pk=comment_pk)
    content = request.POST.get('content', '')
    
    # Check parent visibility? 
    if not parent.is_visible and not request.user.is_staff and parent.place.establishment.owner != request.user:
         messages.error(request, "لا يمكن الرد على تعليق مخفي.")
         return redirect('place_detail', pk=parent.place.pk)

    from interactions.services.comment_service import CommentService
    
    obj, success, message = CommentService.create_comment(
        user=request.user,
        place=parent.place,
        review=parent.review, # Maintain link to review if parent is linked
        parent_id=parent.pk,
        content=content,
        ip=request.META.get('REMOTE_ADDR')
    )
    
    if request.headers.get('HX-Request'):
        if success:
             from django.shortcuts import render
             # Calculate rights
             has_management_rights = False
             if request.user.is_staff:
                 has_management_rights = True
             elif hasattr(parent.place, 'establishment') and parent.place.establishment.owner == request.user:
                 has_management_rights = True
                 
             return render(request, 'places/partials/comment_reply.html', {
                 'reply': obj,
                 'place': parent.place,
                 'user': request.user,
                 'has_management_rights': has_management_rights
             })
        else:
             from django.http import HttpResponse
             return HttpResponse(f"<div class='alert alert-danger'>{message}</div>")

    if success:
         messages.success(request, "تم إضافة ردك بنجاح.")
    else:
        messages.error(request, message)
        
    return redirect('place_detail', pk=parent.place.pk)


@login_required
@require_POST
@ratelimit(key='user', rate='3/h', method='POST', block=True)
def report_place(request, place_pk):
    place = get_object_or_404(Place, pk=place_pk)
    
    form = ReportForm(request.POST, request.FILES)
    if form.is_valid():
        from interactions.services.report_service import ReportService
        from django.core.exceptions import ValidationError
        
        try:
            ReportService.create_report(
                user=request.user,
                content_object=place,
                report_type=form.cleaned_data['report_type'],
                description=form.cleaned_data['description'],
                proof_image=form.cleaned_data.get('proof_image')
            )
            if request.headers.get('HX-Request'):
                from django.shortcuts import render
                return render(request, 'interactions/partials/report_success.html')
            
            messages.warning(request, "تم استلام بلاغك بنجاح. سنقوم بمراجعته في أقرب وقت.")
        except ValidationError as e:
            if request.headers.get('HX-Request'):
                 return HttpResponse(f"<div class='alert alert-danger'>{str(e)}</div>", status=400)
            messages.error(request, str(e))
        except Exception:
            if request.headers.get('HX-Request'):
                 return HttpResponse("<div class='alert alert-danger'>حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.</div>", status=500)
            messages.error(request, "حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.")
    else:
         if request.headers.get('HX-Request'):
             return HttpResponse("<div class='alert alert-danger'>البيانات المدخلة غير صحيحة. يرجى التحقق وإعادة المحاولة.</div>", status=400)
         messages.error(request, "البيانات المدخلة غير صحيحة. يرجى التحقق وإعادة المحاولة.")

    return redirect('place_detail', pk=place_pk)

from django.http import JsonResponse, HttpResponse

@require_POST
def toggle_favorite(request, place_pk):
    """Step 6A.2: Improved toggle with proper JSON response and HTMX support."""
    # Handle unauthenticated AJAX requests
    if not request.user.is_authenticated:
        if is_htmx(request):
            return htmx_redirect(login_redirect_url(request))
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)
    
    place = get_object_or_404(Place, pk=place_pk)
    
    # Use get_or_create to avoid race conditions
    favorite, created = Favorite.objects.get_or_create(user=request.user, place=place)
    
    if not created:
        # Already existed, so delete it
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True
    
    # Get updated count for the place
    favorites_count = Favorite.objects.filter(place=place).count()
    
    # Check for HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'partials/favorite_button.html', {
            'place': place,
            'is_fav': is_favorited,
            'favorites_count': favorites_count,
            'user': request.user
        })

    return JsonResponse({
        'liked': is_favorited,
        'favorites_count': favorites_count
    })

@login_required
@require_POST
def bulk_delete_favorites(request):
    """Bulk remove places from favorites."""
    place_ids = request.POST.getlist('place_ids')
    if place_ids:
        count, _ = Favorite.objects.filter(user=request.user, place_id__in=place_ids).delete()
        messages.success(request, f"تم إزالة {count} من المفضلات بنجاح.")
    else:
        messages.warning(request, "لم يتم تحديد أي عناصر للحذف.")
    
    # Redirection logic
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
        
    return redirect('favorite_list')

@require_POST
def toggle_follow(request, place_pk):
    """
    Toggle follow status for an establishment (via Place).
    """
    if not request.user.is_authenticated:
        if is_htmx(request):
             return htmx_redirect(login_redirect_url(request))
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)
    
    place = get_object_or_404(Place, pk=place_pk)
    
    # Ensure place is an establishment
    if not hasattr(place, 'establishment'):
        return JsonResponse({'error': 'not_establishment'}, status=400)
        
    establishment = place.establishment
    from .models import EstablishmentFollow
    
    follow, created = EstablishmentFollow.objects.get_or_create(user=request.user, establishment=establishment)
    
    if not created:
        follow.delete()
        following = False
    else:
        following = True
        
    followers_count = EstablishmentFollow.objects.filter(establishment=establishment).count()
    
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        from django.shortcuts import render
        return render(request, 'interactions/partials/follow_button.html', {
            'place': place,
            'following': following,
            'followers_count': followers_count
        })

    return JsonResponse({
        'following': following,
        'followers_count': followers_count
    })



# Notification Views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse
from .models import Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'interactions/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    # Filter groups mapping URL param to notification_type values
    TYPE_GROUPS = {
        'partner': [
            'partner_approved', 'partner_rejected', 'partner_needs_info',
        ],
        'establishment': [
            'establishment_approved', 'establishment_rejected',
            'establishment_suspended', 'establishment_reactivated',
            'new_establishment_request', 'establishment_update_request',
            'pending_change_requested', 'pending_change_approved', 'pending_change_rejected',
        ],
        'review': [
            'new_review', 'review_reply', 'review_objection',
        ],
        'report': [
            'new_user_report', 'new_report_on_establishment',
            'report_update', 'report_resolved', 'report_rejected',
        ],
        'system': ['general'],
    }

    FILTER_LABELS = [
        ('', 'الكل'),
        ('partner', 'الشراكة'),
        ('establishment', 'المنشآت'),
        ('weather', 'الطقس'),
        ('review', 'التقييمات'),
        ('report', 'البلاغات'),
        ('system', 'النظام'),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from management.models import NotificationSetting, FeatureToggle
        
        settings = NotificationSetting.objects.first()
        context['notification_settings'] = settings
        context['allow_delete'] = True # Always allow delete (per user request)
        context['allow_mark_all'] = settings.allow_mark_all if settings else True
        context['enable_notifications'] = FeatureToggle.objects.filter(
            key='enable_notifications', is_enabled=True
        ).exists()
        
        # Dynamic template inheritance
        if hasattr(self.request.user, 'role') and self.request.user.role and self.request.user.role.name == 'Partner':
            context['base_template'] = 'partners/base_partner.html'
        else:
            context['base_template'] = 'base.html'

        # Filter context
        context['active_filter'] = self.request.GET.get('type', '')
        context['filter_choices'] = self.FILTER_LABELS
            
        return context

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
        type_filter = self.request.GET.get('type', '')
        
        if type_filter == 'weather':
            # Weather alerts use event_type since they map to 'general' notification_type
            qs = qs.filter(event_type='WEATHER_ALERT')
        elif type_filter in self.TYPE_GROUPS:
            qs = qs.filter(notification_type__in=self.TYPE_GROUPS[type_filter])
        
        return qs

@require_POST
def mark_notification_read(request, pk):
    """Step 7.4 fix: Also update read_at timestamp."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=403)
        
    from management.models import FeatureToggle, NotificationSetting
    if not FeatureToggle.objects.filter(key='enable_notifications', is_enabled=True).exists():
         return JsonResponse({'status': 'error', 'message': 'disabled'}, status=403)

    from django.utils import timezone
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    if request.headers.get('HX-Request'):
        from django.shortcuts import render
        settings = NotificationSetting.objects.first()
        allow_delete = settings.allow_delete if settings else False
        response = render(request, 'interactions/partials/notification_item.html', {
            'notification': notification,
            'allow_delete': allow_delete 
        })
        response['HX-Trigger'] = 'notificationUpdated'
        return response

    return JsonResponse({'status': 'ok'})

@require_POST
def mark_all_notifications_read(request):
    """Step 7.4 fix: Also update read_at timestamp."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=403)
    
    from management.models import FeatureToggle, NotificationSetting
    if not FeatureToggle.objects.filter(key='enable_notifications', is_enabled=True).exists():
         return JsonResponse({'status': 'error', 'message': 'disabled'}, status=403)
    
    settings = NotificationSetting.objects.first()
    if settings and not settings.allow_mark_all:
         return JsonResponse({'status': 'error', 'message': 'not_allowed'}, status=403)

    from django.utils import timezone
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    if request.headers.get('HX-Request'):
        from django.http import HttpResponse
        response = HttpResponse("OK")
        response['HX-Refresh'] = "true"
        return response

    return JsonResponse({'status': 'ok'})

@require_POST
def delete_notification(request, pk):
    """Delete a notification with policy enforcement."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=403)
    
    # Check FeatureToggle
    from management.models import FeatureToggle, NotificationSetting
    if not FeatureToggle.objects.filter(key='enable_notifications', is_enabled=True).exists():
        return JsonResponse({'status': 'error', 'message': 'disabled'}, status=403)
    
    # Check allow_delete policy - Disabled per user request
    settings = NotificationSetting.objects.first()
    # if settings and not settings.allow_delete:
    #    return JsonResponse({'status': 'error', 'message': 'deletion_not_allowed'}, status=403)
        
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    
    if request.headers.get('HX-Request'):
        from django.http import HttpResponse
        response = HttpResponse("")
        response['HX-Trigger'] = 'notificationUpdated'
        return response

    return JsonResponse({'status': 'ok'})

@require_POST
def delete_all_notifications(request):
    """Delete all notifications for the current user."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error'}, status=403)
    
    # Check FeatureToggle
    from management.models import FeatureToggle
    if not FeatureToggle.objects.filter(key='enable_notifications', is_enabled=True).exists():
        return JsonResponse({'status': 'error', 'message': 'disabled'}, status=403)
    
    # Check allow_delete policy - Disabled per user request (Wait, user requested this feature specifically now)
    # The previous comment in delete_notification said "Disabled per user request", but now user EXPLICITLY asked for it.
    # So we proceed.
        
    Notification.objects.filter(recipient=request.user).delete()
    
    if request.headers.get('HX-Request'):
        from django.http import HttpResponse
        # Return empty list or refresh
        response = HttpResponse("")
        response['HX-Refresh'] = "true"
        return response

    return JsonResponse({'status': 'ok'})

@login_required
def unread_count(request):
    """Return count of unread notifications for live badge updates."""
    count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()

    if request.headers.get('HX-Request'):
        from django.template import Context, Template
        from django.http import HttpResponse
        
        # We return OOB swaps for the badge containers
        # If count > 0, we render the badge. If 0, empty string.
        
        partner_badge = f'<span class="badge bg-danger float-end mt-1">{count}</span>' if count > 0 else ""
        public_badge = f'<span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger border border-light p-1" style="font-size:0.6rem;">{count}</span>' if count > 0 else ""
        
        return HttpResponse(f"""
            <div id="partner-notification-badge-container" hx-swap-oob="innerHTML">{partner_badge}</div>
            <div id="public-notification-badge-container" hx-swap-oob="innerHTML">{public_badge}</div>
        """)

    return JsonResponse({'count': count})

class FavoriteListView(LoginRequiredMixin, ListView):
    model = Favorite
    template_name = 'interactions/favorite_list.html'
    context_object_name = 'favorites'
    paginate_by = 12

    def get_queryset(self):
        qs = Favorite.objects.filter(user=self.request.user).select_related('place', 'place__category').order_by('-created_at')
        category_id = self.request.GET.get('category')
        if category_id:
            qs = qs.filter(place__category_id=category_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get unique categories from user's favorites
        user_favs = Favorite.objects.filter(user=self.request.user).select_related('place__category')
        categories = {}
        for fav in user_favs:
            if fav.place.category:
                categories[fav.place.category.id] = fav.place.category
        
        context['favorite_categories'] = categories.values()
        context['active_category'] = self.request.GET.get('category')
        return context


@login_required
@require_POST
def toggle_comment_visibility(request, pk, model_type='comment'):
    """
    Toggle visibility of a review or comment.
    Used by partners to hide/show content on their establishment.
    """
    from interactions.services.comment_service import CommentService
    from interactions.models import Review, PlaceComment
    
    # 1. Determine Model
    model_class = Review if model_type == 'review' else PlaceComment
    obj = get_object_or_404(model_class, pk=pk)
    
    # 2. Check Permissions (Partner Owner or Admin)
    place = obj.place
    if hasattr(place, 'establishment'):
        is_owner = place.establishment.owner == request.user
    else:
        is_owner = False
        
    if not (is_owner or request.user.is_staff):
        messages.error(request, "ليس لديك صلاحية للقيام بهذا الإجراء.")
        return redirect('place_detail', pk=place.pk)

    # 3. Determine Action
    current_state = obj.visibility_state
    new_state = 'visible'
    reason = request.POST.get('reason', '')
    
    if current_state == 'visible':
        new_state = 'partner_hidden'
    elif current_state == 'partner_hidden':
        new_state = 'visible'
    elif current_state == 'admin_hidden':
        if not request.user.is_staff:
             messages.error(request, "لا يمكن إظهار محتوى تم إخفاؤه بواسطة الإدارة.")
             return redirect('place_detail', pk=place.pk)
        new_state = 'visible' # Admin unhiding

    # 4. Call Service
    success, msg = CommentService.set_visibility(request.user, pk, new_state, reason, model_class=model_class)
    
    if success:
        messages.success(request, msg)
        # Update object state for partial
        obj.visibility_state = new_state
    else:
        messages.error(request, msg)

    if request.headers.get('HX-Request'):
         from django.shortcuts import render
         return render(request, 'interactions/partials/visibility_toggle.html', {
             'item': obj,
             'type': model_type
         })
        
    return redirect('place_detail', pk=place.pk)


@login_required
def stream_notifications(request):
    """
    SSE stream for real-time notifications.
    Yields unread count (badge) and latest notifications (dropdown).
    """
    def event_stream():
        last_notif_id = None
        first_run = True
        
        while True:
            # 1. Fetch unread count
            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            
            # 2. Fetch latest notifications
            latest_notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
            
            # 3. Check for new notifications
            current_top_id = latest_notifs[0].id if latest_notifs.exists() else None
            
            # Always send badge
            badge_html = render_to_string('partials/notifications_badge.html', {
                'unread_notifications_count': unread_count
            })
            badge_payload = badge_html.replace("\n", "")
            yield f"event: badge\ndata: {badge_payload}\n\n"
            
            # Send dropdown if new notification arrives or on first run
            if first_run or current_top_id != last_notif_id:
                dropdown_html = render_to_string('partials/notifications_dropdown.html', {
                    'latest_notifications': latest_notifs,
                    'unread_notifications_count': unread_count
                })
                dropdown_payload = dropdown_html.replace("\n", "")
                yield f"event: dropdown\ndata: {dropdown_payload}\n\n"
                last_notif_id = current_top_id
                first_run = False
            
            time.sleep(5) # Poll every 5 seconds

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable buffering for Nginx
    return response


@login_required
def notifications_snapshot(request):
    """
    Lightweight snapshot for initial notifications badge + dropdown.
    Intended for HTMX/AJAX on page load.
    """
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]

    badge_html = render_to_string('partials/notifications_badge.html', {
        'unread_notifications_count': unread_count
    }, request=request)
    dropdown_html = render_to_string('partials/notifications_dropdown.html', {
        'latest_notifications': latest_notifications,
        'unread_notifications_count': unread_count
    }, request=request)

    html = (
        f'<div id="notif-badge" hx-swap-oob="innerHTML">{badge_html}</div>'
        f'<ul id="notif-dropdown" hx-swap-oob="innerHTML">{dropdown_html}</ul>'
    )
    return HttpResponse(html)
