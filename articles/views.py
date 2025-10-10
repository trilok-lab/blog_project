import os
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Article, Category
from .serializers import ArticleSerializer, CategorySerializer
from accounts.models import Verification
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings


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
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminOrAuthorCanEdit()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return qs.filter(is_approved=True)
        if getattr(user, 'is_staff', False) or getattr(user, 'is_admin', False):
            return qs
        return qs.filter(Q(is_approved=True) | Q(author_id=user.id))

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            # Enforce paywall for authenticated users unless admin/staff
            if not (getattr(user, 'is_admin', False) or user.is_staff or getattr(user, 'can_submit_articles', False)):
                raise ValidationError({'detail': 'Payment required before submitting articles'})
            article = serializer.save(author=user, is_approved=getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False))
        else:
            # Guest submission requires OTP verification
            mobile = self.request.data.get('mobile_no')
            code = self.request.data.get('code')
            if not mobile or not code:
                raise ValidationError({'detail': 'mobile_no and code required for guest submissions'})
            try:
                ver = Verification.objects.filter(mobile_no=mobile, purpose='guest_article').latest('created_at')
                if ver.code != code or not ver.is_verified:
                    raise ValidationError({'detail': 'invalid verification'})
            except Verification.DoesNotExist:
                raise ValidationError({'detail': 'no verification found'})
            article = serializer.save(author=None, is_approved=False)

        # Notify admin on new submission
        try:
            admin_email = os.getenv('ADMIN_EMAIL') or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            if admin_email:
                send_mail(subject='New article submitted', message=f'# New Article Submitted\n\n**Title**: {article.title}', from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[admin_email], fail_silently=True)
        except Exception:
            pass

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True, is_approved=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_slug>[^/.]+)', permission_classes=[permissions.AllowAny])
    def by_category(self, request, category_slug=None):
        qs = self.get_queryset().filter(categories__slug=category_slug, is_approved=True).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_image(self, request, slug=None):
        article = self.get_object()
        user = request.user
        if not (user.is_staff or getattr(user, 'is_admin', False) or article.author_id == user.id):
            raise ValidationError({'detail': 'not permitted'})
        image = request.FILES.get('image')
        if not image:
            raise ValidationError({'detail': 'image file required'})
        if not getattr(image, 'content_type', '').startswith('image/'):
            raise ValidationError({'detail': 'invalid file type'})
        article.image = image
        article.save(update_fields=['image'])
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def popularity(self, request, slug=None):
        article = self.get_object()
        value = request.data.get('value')
        try:
            value = int(value)
        except Exception:
            raise ValidationError({'detail': 'integer value required'})
        article.popularity = value
        article.save(update_fields=['popularity'])
        return Response({'popularity': article.popularity}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, slug=None):
        article = self.get_object()
        article.is_approved = True
        article.save(update_fields=['is_approved'])
        return Response(self.get_serializer(article).data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser], url_path='admin')
    def admin_list(self, request):
        qs = Article.objects.all().order_by('-created_at')
        status_param = request.query_params.get('status')
        if status_param == 'pending':
            qs = qs.filter(is_approved=False)
        elif status_param == 'approved':
            qs = qs.filter(is_approved=True)
        author = request.query_params.get('author')
        if author:
            if author.isdigit():
                qs = qs.filter(author_id=int(author))
            else:
                qs = qs.filter(author__username=author)
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(categories__slug=category)
        ordering = request.query_params.get('ordering')
        if ordering:
            qs = qs.order_by(ordering)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def feature(self, request, slug=None):
        article = self.get_object()
        is_featured = request.data.get('is_featured')
        if isinstance(is_featured, str):
            is_featured = is_featured.lower() in ['1', 'true', 'yes']
        elif not isinstance(is_featured, bool):
            raise ValidationError({'detail': 'is_featured must be boolean'})
        article.is_featured = bool(is_featured)
        article.save(update_fields=['is_featured'])
        return Response(self.get_serializer(article).data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        qs = self.get_queryset().filter(author_id=request.user.id).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def permalink(self, request, slug=None):
        article = self.get_object()
        if not article.is_approved and not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'is_admin', False) or article.author_id == request.user.id)):
            raise ValidationError({'detail': 'not available'})
        return Response({'permalink': article.permalink, 'slug': article.slug, 'id': article.id})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def perform_destroy(self, instance):
        if instance.articles.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Cannot delete category with related articles'})
        return super().perform_destroy(instance)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser], url_path='admin')
    def admin_list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


