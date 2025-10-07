from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from accounts.models import Verification
from .models import Comment
from .serializers import CommentSerializer


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
        serializer.save(author=user, is_approved=bool(user and (getattr(user, 'is_admin', False) or user.is_staff)))


