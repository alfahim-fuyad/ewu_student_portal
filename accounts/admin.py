"""Admin site registration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Custom admin for the custom User model."""
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Portal info', {'fields': ('role', 'phone', 'address', 'date_of_birth', 'bio', 'avatar')}),
    )
