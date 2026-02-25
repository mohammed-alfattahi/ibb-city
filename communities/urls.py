from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.CommunityListView.as_view(), name='list'),
    path('<slug:slug>/', views.CommunityDetailView.as_view(), name='detail'),
    path('<slug:slug>/join/', views.JoinCommunityView.as_view(), name='join'),
    path('<slug:slug>/leave/', views.LeaveCommunityView.as_view(), name='leave'),
    path('<slug:slug>/post/', views.PostCreateView.as_view(), name='create_post'),
    
    # Comments & Likes
    path('post/<int:post_id>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('post/<int:post_id>/like/', views.LikePostView.as_view(), name='like_post'),
    path('comment/<int:comment_id>/delete/', views.DeleteCommentView.as_view(), name='delete_comment'),
]

