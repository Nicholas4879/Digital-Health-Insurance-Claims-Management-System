from django.contrib import admin
from django.urls import path
from accounts.views import (
    login_view,
    register_view,
    patient_dashboard,
    provider_dashboard,
    admin_dashboard,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("patient-dashboard/", patient_dashboard, name="patient_dashboard"),
    path("provider-dashboard/", provider_dashboard, name="provider_dashboard"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
]