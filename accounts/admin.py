from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Verification


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'Extra',
            {
                'fields': (
                    'mobile_no', 'is_admin', 'is_mobile_verified', 'can_submit_articles',
                )
            },
        ),
    )
    list_display = ('username', 'email', 'mobile_no', 'is_admin', 'is_mobile_verified', 'can_submit_articles')


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('mobile_no', 'purpose', 'is_verified', 'created_at')
    list_filter = ('purpose', 'is_verified')

