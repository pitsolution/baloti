from django.contrib import admin

from .models import Candidate, Contest, Guardian, Voter, ParentContest, Recommender, ContestRecommender, ContestType


class CandidateInline(admin.TabularInline):
    model = Candidate
    fields = ('name',)


class GuardianInline(admin.TabularInline):
    model = Guardian

class ContestRecommenderInline(admin.TabularInline):
    model = ContestRecommender


class ParentContestAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'status'
    )
admin.site.register(ParentContest, ParentContestAdmin)

class RecommenderAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
admin.site.register(Recommender, RecommenderAdmin)

class ContestTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
admin.site.register(ContestType, ContestTypeAdmin)

class ContestAdmin(admin.ModelAdmin):
    inlines = [ContestRecommenderInline, CandidateInline, GuardianInline]
    list_display = (
        'name',
        'mediator',
        'start',
        'end',
        'parent',
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

