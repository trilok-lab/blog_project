from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("article", "author", "author_name", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("author_name", "content")

