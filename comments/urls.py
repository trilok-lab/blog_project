from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet, ArticleCommentsView, AdminCommentListView, AdminApproveCommentView


router = DefaultRouter()
router.register('', CommentViewSet, basename='comment')


urlpatterns = [
    path('', include(router.urls)),
    path('articles/<slug:slug>/comments/', ArticleCommentsView.as_view(), name='article-comments'),
    path('admin/comments/', AdminCommentListView.as_view(), name='admin-comment-list'),
    path('admin/comments/<int:pk>/approve/', AdminApproveCommentView.as_view(), name='admin-comment-approve'),
]


