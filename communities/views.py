from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Count
from .models import Community, CommunityPost, CommunityMembership
from django import forms

class CommunityListView(ListView):
    model = Community
    template_name = 'communities/community_list.html'
    context_object_name = 'communities'
    
    def get_queryset(self):
        return Community.objects.annotate(member_count=Count('members')).order_by('-is_official', '-member_count')

class CommunityDetailView(DetailView):
    model = Community
    template_name = 'communities/community_detail.html'
    context_object_name = 'community'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['is_member'] = CommunityMembership.objects.filter(user=user, community=self.object).exists()
        else:
            context['is_member'] = False
        
        # Inject Feature Toggles
        from management.models import FeatureToggle
        toggles = FeatureToggle.objects.filter(is_enabled=True).values_list('key', flat=True)
        context['toggles'] = {key: True for key in toggles}

        # Pass the form for the modal
        context['post_form'] = PostCreateForm()
        return context

class PostCreateForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ['content', 'image', 'linked_place', 'post_type']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'شارك تجربتك...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'linked_place': forms.Select(attrs={'class': 'form-select'}),
            'post_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['linked_place'].queryset = self.fields['linked_place'].queryset.select_related('category')
        self.fields['linked_place'].label = "مرتبط بمعلم (اختياري)"
        self.fields['post_type'].label = "نوع المشاركة"

class PostCreateView(LoginRequiredMixin, CreateView):
    model = CommunityPost
    form_class = PostCreateForm
    
    def form_valid(self, form):
        community = get_object_or_404(Community, slug=self.kwargs['slug'])
        # Check membership
        if not CommunityMembership.objects.filter(user=self.request.user, community=community).exists():
             messages.error(self.request, "يجب أن تكون عضوًا في المجتمع لتتمكن من النشر")
             return redirect('communities:detail', slug=community.slug)
             
        form.instance.community = community
        form.instance.author = self.request.user
        messages.success(self.request, "تم نشر مشاركتك بنجاح")
        
        if self.request.headers.get('HX-Request'):
             from django.shortcuts import render
             return render(self.request, 'communities/partials/post_item.html', {'post': form.instance, 'user': self.request.user})

        return super().form_valid(form)

    def form_invalid(self, form):
        # No dedicated form template exists — redirect back with error messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect('communities:detail', slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse('communities:detail', kwargs={'slug': self.kwargs['slug']})

class JoinCommunityView(LoginRequiredMixin, View):
    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        membership, created = CommunityMembership.objects.get_or_create(user=request.user, community=community)
        
        if created:
            messages.success(request, f"تم الانضمام إلى {community.name} بنجاح")
        else:
            messages.info(request, f"أنت بالفعل عضو في {community.name}")
            
        if request.headers.get('HX-Request'):
            from django.shortcuts import render
            return render(request, 'communities/partials/join_leave_area.html', {
                'community': community,
                'is_member': True
            })

        return redirect('communities:detail', slug=slug)

class LeaveCommunityView(LoginRequiredMixin, View):
    def post(self, request, slug):
        community = get_object_or_404(Community, slug=slug)
        deleted_count, _ = CommunityMembership.objects.filter(user=request.user, community=community).delete()
        
        if deleted_count > 0:
            messages.success(request, f"تمت مغادرة {community.name}")
        
        if request.headers.get('HX-Request'):
            from django.shortcuts import render
            return render(request, 'communities/partials/join_leave_area.html', {
                'community': community,
                'is_member': False
            })

        return redirect('communities:detail', slug=slug)


# ============================================
# Post Comments & Likes
# ============================================
from .models import PostComment
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


class AddCommentView(LoginRequiredMixin, View):
    """إضافة تعليق على منشور"""
    
    def post(self, request, post_id):
        from management.models import FeatureToggle
        if not FeatureToggle.objects.filter(key='enable_comments', is_enabled=True).exists():
             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'التعليقات معطلة حالياً'}, status=403)
             messages.error(request, "التعليقات معطلة حالياً")
             return redirect(request.META.get('HTTP_REFERER', '/'))

        post = get_object_or_404(CommunityPost, pk=post_id)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')
        
        if not content:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'التعليق لا يمكن أن يكون فارغاً'}, status=400)
            messages.error(request, "التعليق لا يمكن أن يكون فارغاً")
            return redirect('communities:detail', slug=post.community.slug)
        
        # إنشاء التعليق
        comment = PostComment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent_id=parent_id if parent_id else None
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author': request.user.get_full_name() or request.user.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y/%m/%d %H:%M'),
                }
            })
        
        messages.success(request, "تم إضافة تعليقك بنجاح")
        return redirect('communities:detail', slug=post.community.slug)


class DeleteCommentView(LoginRequiredMixin, View):
    """حذف تعليق (للمالك فقط)"""
    
    def post(self, request, comment_id):
        comment = get_object_or_404(PostComment, pk=comment_id)
        
        # التحقق من أن المستخدم هو صاحب التعليق أو مشرف
        if comment.author != request.user and not request.user.is_staff:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'غير مصرح لك بحذف هذا التعليق'}, status=403)
            messages.error(request, "غير مصرح لك بحذف هذا التعليق")
            return redirect('communities:detail', slug=comment.post.community.slug)
        
        community_slug = comment.post.community.slug
        comment.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, "تم حذف التعليق")
        return redirect('communities:detail', slug=community_slug)


class LikePostView(LoginRequiredMixin, View):
    """الإعجاب أو إلغاء الإعجاب بمنشور"""
    
    def post(self, request, post_id):
        from management.models import FeatureToggle
        if not FeatureToggle.objects.filter(key='enable_likes', is_enabled=True).exists():
             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'الإعجابات معطلة حالياً'}, status=403)
             return redirect(request.META.get('HTTP_REFERER', '/'))

        post = get_object_or_404(CommunityPost, pk=post_id)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'liked': liked,
                'count': post.like_count
            })
        
        return redirect('communities:detail', slug=post.community.slug)

