from rest_framework import viewsets, permissions, generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from accounts.models import Verification
from articles.models import Article
from .models import Comment
from .serializers import CommentSerializer
from django.core.mail import send_mail
from django.conf import settings


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if not user:
            mobile = self.request.data.get('author_mobile')
            code = self.request.data.get('code')
            if not mobile or not code:
                raise ValidationError({'detail': 'author_mobile and code required for guests'})
            try:
                ver = Verification.objects.filter(mobile_no=mobile, purpose='guest_comment').latest('created_at')
                if ver.code != code or not ver.is_verified:
                    raise ValidationError({'detail': 'invalid verification'})
            except Verification.DoesNotExist:
                raise ValidationError({'detail': 'no verification found'})
        comment = serializer.save(author=user, is_approved=bool(user and (getattr(user, 'is_admin', False) or user.is_staff)))
        # Notify article author of new comment
        try:
            article_author_email = getattr(getattr(comment, 'article', None), 'author', None)
            article_author_email = getattr(article_author_email, 'email', None)
            if article_author_email:
                send_mail(subject='New comment on your article', message=f'# New Comment\n\n{comment.content}', from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[article_author_email], fail_silently=True)
        except Exception:
            pass

    def get_queryset(self):
        qs = super().get_queryset().filter(is_approved=True)
        article_id = self.request.query_params.get('article')
        if article_id:
            qs = qs.filter(article_id=article_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        is_admin = bool(user and (user.is_staff or getattr(user, 'is_admin', False)))
        if not user.is_authenticated:
            raise ValidationError({'detail': 'authentication required'})
        if not (is_admin or instance.author_id == user.id):
            raise ValidationError({'detail': 'not permitted'})
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        qs = Comment.objects.filter(author=request.user).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class ArticleCommentsView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return Comment.objects.filter(article__slug=slug, is_approved=True).order_by('-created_at')

    def perform_create(self, serializer):
        slug = self.kwargs.get('slug')
        article = get_object_or_404(Article, slug=slug)
        request = self.request
        user = request.user if request.user.is_authenticated else None
        if not user:
            mobile = request.data.get('author_mobile')
            code = request.data.get('code')
            if not mobile or not code:
                raise ValidationError({'detail': 'author_mobile and code required for guests'})
            try:
                ver = Verification.objects.filter(mobile_no=mobile, purpose='guest_comment').latest('created_at')
                if ver.code != code or not ver.is_verified:
                    raise ValidationError({'detail': 'invalid verification'})
            except Verification.DoesNotExist:
                raise ValidationError({'detail': 'no verification found'})
        comment = serializer.save(article=article, author=user, is_approved=bool(user and (getattr(user, 'is_admin', False) or user.is_staff)))
        try:
            article_author_email = getattr(getattr(comment, 'article', None), 'author', None)
            article_author_email = getattr(article_author_email, 'email', None)
            if article_author_email:
                send_mail(subject='New comment on your article', message=f'# New Comment\n\n{comment.content}', from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[article_author_email], fail_silently=True)
        except Exception:
            pass


class AdminCommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = Comment.objects.all().order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param == 'pending':
            qs = qs.filter(is_approved=False)
        elif status_param == 'approved':
            qs = qs.filter(is_approved=True)
        article_slug = self.request.query_params.get('article')
        if article_slug:
            qs = qs.filter(article__slug=article_slug)
        return qs


class AdminApproveCommentView(generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.is_approved = True
        comment.save(update_fields=['is_approved'])
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


