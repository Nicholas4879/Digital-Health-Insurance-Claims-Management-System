from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import re

from claims.models import Claim
from .models import Complaint
from notifications.models import Notification
from reports.models import AuditLog
from accounts.models import InsuranceProvider


def record_action(user, action, entity="", entity_id=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id
    )


def get_lookup_id(value):
    match = re.search(r"\(#(\d+)\)\s*$", value or "")
    return match.group(1) if match else None


def is_insurance_provider(user):
    return user.is_authenticated and (
        user.role == "INSURANCE_PROVIDER" or user.is_superuser
    )


@login_required
def complaints_view(request):
    if request.user.role == "PATIENT":
        claims = Claim.objects.filter(patient=request.user.patient)
        complaints = Complaint.objects.filter(patient=request.user.patient)

    elif is_insurance_provider(request.user):
        claims = Claim.objects.all()
        complaints = Complaint.objects.all()
        if request.user.role == "INSURANCE_PROVIDER" and not hasattr(request.user, "insuranceprovider"):
            InsuranceProvider.objects.create(user=request.user)

    else:
        # Administrators no longer process inquiries — that is exclusively
        # the Insurance Provider's responsibility.
        claims = Claim.objects.none()
        complaints = Complaint.objects.none()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "file_complaint" and request.user.role == "PATIENT":
            claim_id = (
                request.POST.get("claim")
                or get_lookup_id(request.POST.get("claim_search"))
            )

            if not claim_id:
                return render(request, "complaints.html", {
                    "claims": claims,
                    "complaints": complaints,
                    "error": "Please select a claim from the search suggestions."
                })

            complaint = Complaint.objects.create(
                claim=Claim.objects.get(id=claim_id),
                patient=request.user.patient,
                complaint_message=request.POST.get("complaint_message"),
                complaint_status="PENDING"
            )

            record_action(
                request.user,
                "Filed inquiry",
                "Complaint",
                complaint.id
            )

            return redirect("complaints")

        elif action == "respond_complaint" and is_insurance_provider(request.user):
            complaint = Complaint.objects.get(id=request.POST.get("complaint_id"))
            insurance_profile = getattr(request.user, "insuranceprovider", None)

            complaint.response = request.POST.get("response")
            complaint.complaint_status = "RESOLVED"
            complaint.resolved_by = insurance_profile
            complaint.resolved_at = timezone.now()
            complaint.save()

            Notification.objects.create(
                user=complaint.patient.user,
                claim=complaint.claim,
                sent_by=insurance_profile,
                message=f"Your inquiry for claim #{complaint.claim.id} has been responded to."
            )

            record_action(
                request.user,
                "Responded to inquiry",
                "Complaint",
                complaint.id
            )

            return redirect("complaints")

    return render(request, "complaints.html", {
        "claims": claims,
        "complaints": complaints
    })