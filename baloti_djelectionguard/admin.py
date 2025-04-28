from django.contrib import admin
from .models import ParentContesti18n, Initiatori18n, ContestTypei18n, Recommenderi18n, Contesti18n

# Register your models here.

class ParentContesti18nAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'status',
        'language'
    )

class Initiatori18nAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'language'
    )

class ContestTypei18nAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'language'
    )

class Recommenderi18nAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'recommender_type',
        'language'
    )

class Contesti18Admin(admin.ModelAdmin):
    list_display = (
        'name',
        'language',
    )

admin.site.register(ParentContesti18n, ParentContesti18nAdmin)
admin.site.register(Initiatori18n, Initiatori18nAdmin)
admin.site.register(ContestTypei18n, ContestTypei18nAdmin)
admin.site.register(Recommenderi18n, Recommenderi18nAdmin)
admin.site.register(Contesti18n, Contesti18Admin)