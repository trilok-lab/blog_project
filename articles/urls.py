from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CategoryViewSet


router = DefaultRouter()
router.register('items', ArticleViewSet, basename='article')
router.register('categories', CategoryViewSet, basename='category')


urlpatterns = [
    path('', include(router.urls)),
]


