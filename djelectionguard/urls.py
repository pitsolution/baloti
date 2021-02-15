from django.urls import include, path
from django.conf.urls import url

from .views import (
    GuardianDownloadView,
    GuardianVerifyView,
    GuardianUploadView,
    ContestCreateView,
    ContestUpdateView,
    ContestVoteView,
    ContestBallotEncryptView,
    ContestBallotCastView,
    ContestPubkeyView,
    ContestDecryptView,
    ContestOpenView,
    ContestCloseView,
    ContestListView,
    ContestManifestView,
    ContestCandidateCreateView,
    ContestCandidateDeleteView,
    ContestVotersUpdateView,
    ContestVotersDetailView,
    ContestDetailView,
)


urlpatterns = [
    GuardianDownloadView.as_url(),
    GuardianVerifyView.as_url(),
    GuardianUploadView.as_url(),
    ContestCreateView.as_url(),
    ContestUpdateView.as_url(),
    ContestVoteView.as_url(),
    ContestBallotEncryptView.as_url(),
    ContestBallotCastView.as_url(),
    ContestPubkeyView.as_url(),
    ContestDecryptView.as_url(),
    ContestOpenView.as_url(),
    ContestCloseView.as_url(),
    ContestListView.as_url(),
    ContestManifestView.as_url(),
    ContestCandidateCreateView.as_url(),
    ContestCandidateDeleteView.as_url(),
    ContestVotersUpdateView.as_url(),
    ContestVotersDetailView.as_url(),
    ContestDetailView.as_url(),
]
