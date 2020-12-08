from django import forms
from django import http
from django.urls import path
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from .models import Contest, Candidate


class ContestQuerySetMixin:
    def get_queryset(self):
        return Contest.objects.all()


class ContestListView(ContestQuerySetMixin, generic.ListView):
    @classmethod
    def as_url(cls):
        return path(
            '',
            cls.as_view(),
            name='contest_list'
        )


class ContestManifestView(ContestQuerySetMixin, generic.DetailView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/manifest/',
            cls.as_view(),
            name='contest_manifest'
        )

    def get(self, request, *args, **kwargs):
        return http.JsonResponse(self.get_object().get_manifest())


class ContestDetailView(ContestQuerySetMixin, generic.DetailView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/',
            cls.as_view(),
            name='contest_detail'
        )


class ContestVoteView(ContestQuerySetMixin, SingleObjectMixin, generic.FormView):
    @classmethod
    def as_url(cls):
        return path(
            '<pk>/vote/',
            cls.as_view(),
            name='contest_vote'
        )


urlpatterns = [
    ContestDetailView.as_url(),
    ContestManifestView.as_url(),
    ContestVoteView.as_url(),
    ContestListView.as_url(),
]
