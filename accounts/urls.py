from django.urls import path
from . import views

urlpatterns = [

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "patient/dashboard/",
        views.patient_dashboard,
        name="patient_dashboard"
    ),

    path(
        "patient/profile/",
        views.patient_profile,
        name="patient_profile"
    ),

    path(
        "provider/dashboard/",
        views.provider_dashboard,
        name="provider_dashboard"
    ),

    path(
        "insurance/dashboard/",
        views.insurance_dashboard,
        name="insurance_dashboard"
    ),
path(
        "insurance/manage-claims/",
        views.manage_claims,
        name="manage_claims"
    ),

    

    path(
        "insurance/complaints/",
        views.complaints,
        name="complaints"
    ),

    path(
        "insurance/notifications/",
        views.notifications,
        name="notifications"
    ),

    

    path(
        "admin/dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin/create-provider/",
        views.create_provider,
        name="create_provider"
    ),

    path(
        "admin/create-insurance-provider/",
        views.create_insurance_provider,
        name="create_insurance_provider"
    ),

    path(
        "admin/manage-users/",
        views.manage_users,
        name="manage_users"
    ),

]
