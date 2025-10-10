from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HealthView, ConfigView, ContactView, ThemeViewSet, PermalinkArticleView, PermalinkCategoryView, MePermissionsView, AdminStatsView, DebugErrorView


router = DefaultRouter()
router.register('themes', ThemeViewSet, basename='theme')


urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
    path('config/', ConfigView.as_view(), name='config'),
    path('debug/error/', DebugErrorView.as_view(), name='debug-error'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('permalink/article/<slug:slug>/', PermalinkArticleView.as_view(), name='permalink-article'),
    path('permalink/category/<slug:slug>/', PermalinkCategoryView.as_view(), name='permalink-category'),
    path('me/permissions/', MePermissionsView.as_view(), name='me-permissions'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('', include(router.urls)),
    path('themes/activate/', ThemeViewSet.activate, name='theme-activate'),
    path('themes/active/', ThemeViewSet.active, name='theme-active'),
]


