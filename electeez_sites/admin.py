from django import forms
from django.contrib import admin
from django_svg_image_form_field import SvgAndImageFormField


from .models import Site


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        exclude = []
        field_classes = {
            'email_banner': SvgAndImageFormField,
            'email_footer': SvgAndImageFormField,
        }


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    form = SiteForm
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')


from django.contrib.sites.models import Site

admin.site.unregister(Site)
