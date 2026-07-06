from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.reports_view,
        name="reports"
    ),

    path(
        "audit/",
        views.audit_logs_view,
        name="audit_logs"
    ),
]