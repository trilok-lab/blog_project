import os
from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from articles.models import Article, Category
from .models import Theme
from .serializers import ContactSerializer, ThemeSerializer
import markdown


class HealthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class DebugErrorView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Deliberately raise for testing global handler
        raise ValueError('This is a simulated error for testing')


class ConfigView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        page_size_default = int(os.getenv('PAGE_SIZE_DEFAULT', '10'))
        return Response({
            'pagination': {
                'default_page_size': page_size_default,
            },
            'features': {
                'stripe_required_for_submission': True,
                'twilio_required_for_guest': True,
            },
        })


class ContactView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        body_md = f"""
        # New Contact Message

        - **From**: {data['name']} <{data['email']}>
        - **Subject**: {data['subject']}

        ---

        {data['message']}
        """
        body = markdown.markdown(body_md)
        send_mail(subject=f"[Contact] {data['subject']}", message=body, from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[os.getenv('ADMIN_EMAIL') or getattr(settings, 'DEFAULT_FROM_EMAIL', None)], fail_silently=True)
        return Response({'detail': 'Message received'}, status=status.HTTP_200_OK)


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all().order_by('name')
    serializer_class = ThemeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'active']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def perform_create(self, serializer):
        # allow creation; if active=True, other actives will be turned off in model save
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        return super().perform_destroy(instance)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @views.api_view(['POST'])
    def activate(request):
        key = request.data.get('theme_key')
        theme = get_object_or_404(Theme, key=key)
        theme.is_active = True
        theme.save(update_fields=['is_active'])
        return Response({'detail': 'theme activated'}, status=status.HTTP_200_OK)

    @views.api_view(['GET'])
    def active(request):
        theme = Theme.objects.filter(is_active=True).first()
        if not theme:
            return Response({'active': None})
        return Response(ThemeSerializer(theme).data)


class PermalinkArticleView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        article = get_object_or_404(Article, slug=slug, is_approved=True)
        return Response({'slug': slug, 'permalink': article.permalink, 'id': article.id})


class PermalinkCategoryView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        return Response({'slug': slug, 'permalink': category.permalink, 'id': category.id})


class MePermissionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'is_authenticated': True,
            'is_admin': bool(getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False)),
            'can_submit_articles': bool(getattr(user, 'can_submit_articles', False)),
        })


class AdminStatsView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from articles.models import Article
        from comments.models import Comment
        User = get_user_model()
        return Response({
            'users': User.objects.count(),
            'articles_total': Article.objects.count(),
            'articles_pending': Article.objects.filter(is_approved=False).count(),
            'articles_featured': Article.objects.filter(is_featured=True, is_approved=True).count(),
            'comments_total': Comment.objects.count(),
            'comments_pending': Comment.objects.filter(is_approved=False).count(),
        })

