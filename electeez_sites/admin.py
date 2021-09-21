from django import forms
from django.contrib import admin


from .models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')


from django.contrib.sites.models import Site

admin.site.unregister(Site)
