from django.contrib import admin

from .models import Candidate, Contest, Guardian, Voter


class CandidateInline(admin.TabularInline):
    model = Candidate
    fields = ('name',)


class GuardianInline(admin.TabularInline):
    model = Guardian


class ContestAdmin(admin.ModelAdmin):
    inlines = [CandidateInline, GuardianInline]

    def save_model(self, request, obj, form, change):
        response = super().save_model(request, obj, form, change)
        obj.voters_update()
        return response
admin.site.register(Contest, ContestAdmin)
