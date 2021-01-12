from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User

admin.site.unregister(Group)

UserAdmin.ordering = None
UserAdmin.list_display = ('email', 'first_name', 'last_name', 'is_staff')
UserAdmin.search_fields = ('first_name', 'last_name', 'email')
UserAdmin.fieldsets = (
    (None, {'fields': ('email', 'password',)}),
    ('Personal info', {'fields': ('first_name', 'last_name')}),
    ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    ('Important dates', {'fields': ('last_login', 'date_joined')}),
)
UserAdmin.add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('username', 'password1', 'password2'),
    }),
)
admin.site.register(User, UserAdmin)
