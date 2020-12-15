from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

UserAdmin.ordering = None
admin.site.register(User, UserAdmin)
