from django.contrib import admin

from .models import Language, Text

class TextAdmin(admin.TabularInline):
    model = Text
    fields = ('key', 'val', 'nval')


class LanguageAdmin(admin.ModelAdmin):
    model = Language
    inlines = [TextAdmin]
    list_display = ('name', 'site')
    fields = ('name', 'iso', 'site')
    readonly_fields = ('site',)

admin.site.register(Language, LanguageAdmin)
