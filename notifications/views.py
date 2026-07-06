from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Notification


@login_required
def notifications_view(request):

    if request.method == "POST":
        notification = Notification.objects.get(
            id=request.POST.get("notification_id"),
            user=request.user
        )

        notification.notification_status = "READ"
        notification.read_at = timezone.now()
        notification.save()

        return redirect("notifications")

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-sent_at")

    return render(request, "notifications.html", {
        "notifications": notifications
    })