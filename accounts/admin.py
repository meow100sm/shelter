from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'role', 'is_2fa_enabled')
    list_filter = ('role', 'is_2fa_enabled')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'full_name', 'totp_secret', 'is_2fa_enabled')}),
    )