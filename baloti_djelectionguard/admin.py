from django.contrib import admin
from .models import ParentContesti18n

# Register your models here.

class ParentContesti18nAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'status',
        'language'
    )
admin.site.register(ParentContesti18n, ParentContesti18nAdmin)