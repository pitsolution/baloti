from django.contrib import admin

from .models import Candidate, Contest, Guardian, Voter


class CandidateInline(admin.TabularInline):
    model = Candidate
    fields = ('name',)


class GuardianInline(admin.TabularInline):
    model = Guardian


class ContestAdmin(admin.ModelAdmin):
    inlines = [CandidateInline, GuardianInline]
    list_display = (
        'name',
        'mediator',
        'start',
        'end',
    )
admin.site.register(Contest, ContestAdmin)


class VoterAdmin(admin.ModelAdmin):
    list_display = (
        'contest',
        'user',
    )
    search_fields = (
        'user__email',
        'contest__name',
    )
    list_filter = (
        'casted',
    )
    readonly_fields = (
        'casted',
        'open_email_sent',
        'close_email_sent',
    )
admin.site.register(Voter, VoterAdmin)
