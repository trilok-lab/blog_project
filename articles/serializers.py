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
    category_slugs = serializers.ListField(child=serializers.SlugField(), write_only=True, required=False)
    num_comments = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'description', 'image', 'author',
            'categories', 'category_slugs', 'is_approved', 'is_featured', 'popularity', 'permalink', 'num_comments',
            'created_at'
        ]
        read_only_fields = ['id', 'slug', 'permalink', 'author', 'is_approved', 'created_at']

    def get_num_comments(self, obj):
        return obj.comments.filter(is_approved=True).count()

    def _assign_categories(self, article: Article, category_slugs):
        if category_slugs is None:
            return
        categories = list(Category.objects.filter(slug__in=category_slugs))
        missing = sorted(set(category_slugs) - set([c.slug for c in categories]))
        if missing:
            raise serializers.ValidationError({'category_slugs': [f'Unknown category slug: {s}' for s in missing]})
        article.categories.set(categories)

    def create(self, validated_data):
        category_slugs = validated_data.pop('category_slugs', None)
        article = super().create(validated_data)
        self._assign_categories(article, category_slugs)
        return article

    def update(self, instance, validated_data):
        category_slugs = validated_data.pop('category_slugs', None)
        article = super().update(instance, validated_data)
        self._assign_categories(article, category_slugs)
        return article


