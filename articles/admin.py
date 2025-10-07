from django.contrib import admin
from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "is_approved", "is_featured", "popularity", "created_at")
    list_filter = ("is_approved", "is_featured", "categories")
    search_fields = ("title", "excerpt", "description")
    filter_horizontal = ("categories",)

