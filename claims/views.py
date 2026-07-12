from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import re

from accounts.models import Patient, InsuranceProvider
from accounts.views import is_insurance_provider
from .models import Claim, Document
from notifications.models import Notification
from reports.models import AuditLog

def record_action(user, action, entity="", entity_id=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id
    )


def notify_user(user, message, claim=None, admin=None):
    Notification.objects.create(
        user=user,
        claim=claim,
        sent_by=admin,
        message=message
    )


def get_lookup_id(value):
    match = re.search(r"\(#(\d+)\)\s*$", value or "")
    return match.group(1) if match else None


@login_required
def submit_claim(request, claim_id=None):
    patients = Patient.objects.all()
    resubmitting_claim = None

    if request.user.role != "PROVIDER":
        return render(request, "submit_claim.html", {
            "patients": patients,
            "error": "Only healthcare providers can submit claims."
        })

    # Check whether this is a resubmission
    if claim_id:
        resubmitting_claim = get_object_or_404(
            Claim,
            id=claim_id,
            provider=request.user.healthcareprovider,
            claim_status="REJECTED"
        )

    if request.method == "POST":

        patient_id = (
            request.POST.get("patient")
            or get_lookup_id(request.POST.get("patient_search"))
        )

        if not patient_id:
            return render(request, "submit_claim.html", {
                "patients": patients,
                "form_values": request.POST,
                "resubmitting_claim": resubmitting_claim,
                "error": "Please select a patient from the search suggestions."
            })

        patient = get_object_or_404(Patient, id=patient_id)

        # ===============================
        # RESUBMIT EXISTING CLAIM
        # ===============================
        if resubmitting_claim:

            claim = resubmitting_claim

            claim.patient = patient
            claim.provider = request.user.healthcareprovider
            claim.insurance_company = patient.insurance_company
            claim.claim_type = request.POST.get("claim_type")
            claim.claim_amount = request.POST.get("claim_amount")
            claim.description = request.POST.get("description")
            claim.claim_status = "PENDING"
            claim.rejection_reason = ""
            claim.approved_by = None

            claim.save()

            # Delete previous supporting documents
            Document.objects.filter(claim=claim).delete()

        # ===============================
        # NEW CLAIM
        # ===============================
        else:

            claim = Claim.objects.create(
                patient=patient,
                provider=request.user.healthcareprovider,
                insurance_company=patient.insurance_company,
                claim_type=request.POST.get("claim_type"),
                claim_amount=request.POST.get("claim_amount"),
                description=request.POST.get("description"),
                claim_status="PENDING"
            )

        # ===============================
        # Upload new document
        # ===============================
        if request.FILES.get("file_path"):

            Document.objects.create(
                claim=claim,
                document_name=request.POST.get("document_name"),
                document_type=request.POST.get("document_type"),
                file_path=request.FILES["file_path"]
            )

        # ===============================
        # Notify patient
        # ===============================
        notify_user(
            claim.patient.user,
            f"Your claim #{claim.id} has been submitted and is pending review.",
            claim
        )

        # ===============================
        # Audit log
        # ===============================
        record_action(
            request.user,
            "Resubmitted claim" if resubmitting_claim else "Submitted claim",
            "Claim",
            claim.id
        )

        return redirect("track_claim")

    # ==================================
    # Pre-fill form when resubmitting
    # ==================================

    form_values = {}

    if resubmitting_claim:

        document = Document.objects.filter(
            claim=resubmitting_claim
        ).first()

        form_values = {
            "patient_id": resubmitting_claim.patient.id,
            "patient_label":
                f"{resubmitting_claim.patient.user.get_full_name()} - "
                f"{resubmitting_claim.patient.insurance_number} "
                f"(#{resubmitting_claim.patient.id})",

            "claim_type": resubmitting_claim.claim_type,
            "claim_amount": resubmitting_claim.claim_amount,
            "description": resubmitting_claim.description,
            "rejection_reason": resubmitting_claim.rejection_reason,

            "document_name":
                document.document_name if document else "",

            "document_type":
                document.document_type if document else "",
        }

    return render(request, "submit_claim.html", {
        "patients": patients,
        "form_values": form_values,
        "resubmitting_claim": resubmitting_claim,
    })

@login_required
def track_claim(request):
    if request.user.role == "PATIENT":
        claims = Claim.objects.filter(patient=request.user.patient)
    elif request.user.role == "PROVIDER":
        claims = Claim.objects.filter(provider=request.user.healthcareprovider)
    elif request.user.role == "INSURANCE_PROVIDER":
      claims = Claim.objects.filter(
        insurance_company=request.user.insuranceprovider.insurance_company
    )
    else:
        claims = Claim.objects.none()

    return render(request, "track_claim.html", {
        "claims": claims
    })


@login_required
def manage_claims(request):
    if not is_insurance_provider(request.user):
        return redirect("login")

    if (
        request.user.role == "INSURANCE_PROVIDER"
        and not hasattr(request.user, "insuranceprovider")
    ):
        InsuranceProvider.objects.create(user=request.user)

    insurance_profile = request.user.insuranceprovider

    # Process approval/rejection
    if request.method == "POST":

        claim = get_object_or_404(
            Claim,
            id=request.POST.get("claim_id"),
            insurance_company=insurance_profile.insurance_company,
        )

        action = request.POST.get("action")

        if action == "approve":

            claim.claim_status = "APPROVED"
            claim.approved_by = insurance_profile
            claim.rejection_reason = ""
            claim.save()

            notify_user(
                claim.patient.user,
                f"Your claim #{claim.id} has been approved.",
                claim,
                insurance_profile,
            )

            notify_user(
                claim.provider.user,
                f"Claim #{claim.id} has been approved.",
                claim,
                insurance_profile,
            )

            record_action(
                request.user,
                "Approved claim",
                "Claim",
                claim.id,
            )

        elif action == "reject":

            rejection_reason = request.POST.get(
                "rejection_reason",
                ""
            ).strip()

            if not rejection_reason:

                status_filter = request.GET.get("status", "")

                claims = Claim.objects.filter(
                    insurance_company=insurance_profile.insurance_company
                ).prefetch_related("document_set").order_by("-submission_date")

                if status_filter:
                    claims = claims.filter(
                        claim_status=status_filter
                    )

                return render(
                    request,
                    "manage_claims.html",
                    {
                        "claims": claims,
                        "status_filter": status_filter,
                        "error": "Please provide a reason before rejecting a claim.",
                    },
                )

            claim.claim_status = "REJECTED"
            claim.approved_by = insurance_profile
            claim.rejection_reason = rejection_reason
            claim.save()

            notify_user(
                claim.patient.user,
                f"Your claim #{claim.id} has been rejected.\nReason: {rejection_reason}",
                claim,
                insurance_profile,
            )

            notify_user(
                claim.provider.user,
                f"Claim #{claim.id} has been rejected.\nReason: {rejection_reason}",
                claim,
                insurance_profile,
            )

            record_action(
                request.user,
                "Rejected claim",
                "Claim",
                claim.id,
            )

        return redirect("manage_claims")

    # -------------------------
    # FILTER CLAIMS
    # -------------------------

    status_filter = request.GET.get("status", "")

    claims = Claim.objects.filter(
        insurance_company=insurance_profile.insurance_company
    ).prefetch_related(
        "document_set"
    ).order_by(
        "-submission_date"
    )

    if status_filter:
        claims = claims.filter(
            claim_status=status_filter
        )

    return render(
        request,
        "manage_claims.html",
        {
            "claims": claims,
            "status_filter": status_filter,
        },
    )