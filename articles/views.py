from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article, Category
from .serializers import ArticleSerializer, CategorySerializer


class IsAdminOrAuthorCanEdit(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, 'is_admin', False) or user.is_staff:
            return True
        if isinstance(obj, Article):
            return obj.author_id == getattr(user, 'id', None)
        return False


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_featured', 'is_approved', 'categories__slug']
    search_fields = ['title', 'excerpt', 'description']
    ordering_fields = ['created_at', 'popularity']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminOrAuthorCanEdit()]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        # Enforce paywall for authenticated users
        if user and not (getattr(user, 'is_admin', False) or user.is_staff or getattr(user, 'can_submit_articles', False)):
            raise Exception('Payment required before submitting articles')
        serializer.save(author=user, is_approved=getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False))

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True, is_approved=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_destroy(self, instance):
        if instance.articles.exists():
            raise Exception('Cannot delete category with related articles')
        return super().perform_destroy(instance)


