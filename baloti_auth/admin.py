from django.contrib import admin
from .models import BalotiUser

class BalotiUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'password',
        'status'
    )

admin.site.register(BalotiUser, BalotiUserAdmin)