from rest_framework import serializers
from .models import Article, Category
from comments.models import Comment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'permalink']
        read_only_fields = ['id', 'slug', 'permalink']


class ArticleSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    num_comments = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'description', 'image', 'author',
            'categories', 'is_approved', 'is_featured', 'popularity', 'permalink', 'num_comments',
            'created_at'
        ]
        read_only_fields = ['id', 'slug', 'permalink', 'author', 'is_approved', 'created_at']


