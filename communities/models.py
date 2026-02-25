from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel

class Community(TimeStampedModel):
    """
    Represents a specialized tourism community (e.g., 'Nature Lovers', 'History Buffs').
    """
    name = models.CharField(max_length=100, verbose_name="اسم المجتمع")
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name="الرابط المختصر")
    description = models.TextField(verbose_name="وصف المجتمع")
    cover_image = models.ImageField(upload_to='communities/covers/', verbose_name="صورة الغلاف", blank=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_communities',
        verbose_name="مؤسس المجتمع"
    )
    
    is_official = models.BooleanField(default=False, verbose_name="مجموعة رسمية")
    
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='CommunityMembership', 
        related_name='joined_communities',
        verbose_name="الأعضاء"
    )

    class Meta:
        verbose_name = "مجتمع سياحي"
        verbose_name_plural = "المجتمعات السياحية"
        ordering = ['-is_official', 'name']

    def __str__(self):
        return self.name

class CommunityMembership(TimeStampedModel):
    """
    Intermediate model for user membership in a community, tracking role and join date.
    """
    ROLE_CHOICES = [
        ('MEMBER', 'عضو'),
        ('MODERATOR', 'مشرف'),
        ('ADMIN', 'مدير'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER', verbose_name="الدور")
    
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")

    class Meta:
        unique_together = ('user', 'community')
        verbose_name = "عضوية المجتمع"
        verbose_name_plural = "عضويات المجتمعات"

    def __str__(self):
        return f"{self.user} in {self.community}"

class CommunityPost(TimeStampedModel):
    """
    A post within a community. Can be a text update, sharing a photo, etc.
    """
    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name="المجتمع"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='community_posts',
        verbose_name="الناشر"
    )
    
    content = models.TextField(verbose_name="محتوى المنشور")
    image = models.ImageField(upload_to='communities/posts/', blank=True, null=True, verbose_name="صورة مرفقة")
    
    linked_place = models.ForeignKey(
        'places.Place',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='community_mentions',
        verbose_name="المعلم السياحي المرتبط"
    )

    POST_TYPE_CHOICES = [
        ('EXPERIENCE', 'تجربة زيارة'),
        ('ADVICE', 'نصيحة'),
        ('WARNING', 'تحذير/تنبيه'),
        ('GENERAL', 'عام'),
    ]
    post_type = models.CharField(
        max_length=20, 
        choices=POST_TYPE_CHOICES, 
        default='GENERAL',
        verbose_name="نوع المنشور"
    )
    
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='liked_posts', 
        blank=True,
        verbose_name="الإعجابات"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "منشور مجتمعي"
        verbose_name_plural = "منشورات المجتمع"

    def __str__(self):
        return f"Post by {self.author} in {self.community}"

    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()


class PostComment(TimeStampedModel):
    """
    تعليق على منشور في المجتمع
    """
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="المنشور"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_comments',
        verbose_name="كاتب التعليق"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="الرد على"
    )
    content = models.TextField(verbose_name="محتوى التعليق")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "تعليق على منشور"
        verbose_name_plural = "التعليقات على المنشورات"
    
    def __str__(self):
        return f"Comment by {self.author} on post {self.post.id}"

