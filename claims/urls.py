from django.urls import path
from . import views

urlpatterns = [
    path(
        "submit/",
        views.submit_claim,
        name="submit_claim"
    ),

    path(
        "resubmit/<int:claim_id>/",
        views.submit_claim,
        name="resubmit_claim"
    ),

    path(
        "track/",
        views.track_claim,
        name="track_claim"
    ),

    path(
        "manage/",
        views.manage_claims,
        name="manage_claims"
    ),
]