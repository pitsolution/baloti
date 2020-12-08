from django.contrib import admin

from .models import Candidate, Contest


class CandidateInline(admin.TabularInline):
    model = Candidate


class ContestAdmin(admin.ModelAdmin):
    inlines = [CandidateInline]
admin.site.register(Contest, ContestAdmin)
