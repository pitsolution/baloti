from django.contrib import admin

from .models import Candidate, Contest, Guardian, Voter


class CandidateInline(admin.TabularInline):
    model = Candidate
    fields = ('name',)


class GuardianInline(admin.TabularInline):
    model = Guardian


class ContestAdmin(admin.ModelAdmin):
    inlines = [CandidateInline, GuardianInline]
admin.site.register(Contest, ContestAdmin)
