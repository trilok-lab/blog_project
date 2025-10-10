from django.contrib import admin
from .models import Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'key')


