from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'article', 'author', 'author_name', 'author_mobile', 'content', 'is_approved', 'created_at']
        read_only_fields = ['id', 'author', 'is_approved', 'created_at']


