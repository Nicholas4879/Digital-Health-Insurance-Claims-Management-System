from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path(
        "",
        include("core.urls")
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "claims/",
        include("claims.urls")
    ),

    path(
        "complaints/",
        include("complaints.urls")
    ),

    path(
        "notifications/",
        include("notifications.urls")
    ),

    path(
        "reports/",
        include("reports.urls")
    ),

    path(
        "admin/",
        admin.site.urls
    ),

]

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )