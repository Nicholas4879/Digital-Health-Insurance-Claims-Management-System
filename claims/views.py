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

        patient = Patient.objects.get(id=patient_id)

        claim = Claim.objects.create(
            patient=patient,
            provider=request.user.healthcareprovider,
            insurance_company=patient.insurance_company,
            claim_type=request.POST.get("claim_type"),
            claim_amount=request.POST.get("claim_amount"),
            description=request.POST.get("description"),
            claim_status="PENDING"
        )

        if request.FILES.get("file_path"):
            Document.objects.create(
                claim=claim,
                document_name=request.POST.get("document_name"),
                document_type=request.POST.get("document_type"),
                file_path=request.FILES.get("file_path")
            )

        notify_user(
            claim.patient.user,
            f"Your claim #{claim.id} has been submitted and is pending review.",
            claim
        )

        record_action(
            request.user,
            "Resubmitted a rejected claim" if resubmitting_claim else "Submitted a claim",
            "Claim",
            claim.id
        )

        return redirect("provider_dashboard")

    form_values = {}
    if resubmitting_claim:
        document = Document.objects.filter(claim=resubmitting_claim).first()
        form_values = {
            "patient_id": resubmitting_claim.patient.id,
            "patient_label": (
                f"{resubmitting_claim.patient.user.get_full_name()} - "
                f"{resubmitting_claim.patient.insurance_number} "
                f"(#{resubmitting_claim.patient.id})"
            ),
            "claim_type": resubmitting_claim.claim_type,
            "claim_amount": resubmitting_claim.claim_amount,
            "description": resubmitting_claim.description,
            "rejection_reason": resubmitting_claim.rejection_reason,
            "document_name": document.document_name if document else "",
            "document_type": document.document_type if document else "",
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

    if request.user.role == "INSURANCE_PROVIDER" and not hasattr(request.user, "insuranceprovider"):
        InsuranceProvider.objects.create(user=request.user)

    insurance_profile = getattr(request.user, "insuranceprovider", None)
    pending_claims = Claim.objects.filter(
    insurance_company=insurance_profile.insurance_company,
    claim_status="PENDING"
).prefetch_related("document_set")

    if request.method == "POST":
        action = request.POST.get("action")

        if action in ["approve", "reject"]:
            claim = Claim.objects.get(id=request.POST.get("claim_id"))

            if action == "approve":
                claim.claim_status = "APPROVED"
                claim.approved_by = insurance_profile
                claim.rejection_reason = ""
                message = f"Your claim #{claim.id} has been approved."
                audit_message = "Approved claim"
            else:
                rejection_reason = request.POST.get("rejection_reason", "").strip()
                if not rejection_reason:
                    return render(request, "manage_claims.html", {
                        "claims": pending_claims,
                        "documents": Document.objects.all(),
                        "error": "Please provide a reason before rejecting a claim."
                    })

                claim.claim_status = "REJECTED"
                claim.approved_by = insurance_profile
                claim.rejection_reason = rejection_reason
                message = (
                    f"Your claim #{claim.id} has been rejected. "
                    f"Reason: {rejection_reason}"
                )
                audit_message = "Rejected claim"

            claim.save()

            notify_user(claim.patient.user, message, claim, insurance_profile)
            notify_user(claim.provider.user, message, claim, insurance_profile)

            record_action(request.user, audit_message, "Claim", claim.id)

        elif action in ["verify_document", "reject_document"]:
            document = Document.objects.get(id=request.POST.get("document_id"))

            if action == "verify_document":
                document.verification_status = "VERIFIED"
                document.verified_by = insurance_profile
                audit_message = "Verified supporting document"
            else:
                document.verification_status = "REJECTED"
                document.verified_by = insurance_profile
                audit_message = "Rejected supporting document"

            document.verified_at = timezone.now()
            document.save()

            record_action(request.user, audit_message, "Document", document.id)

        return redirect("manage_claims")

    return render(request, "manage_claims.html", {
        "claims": pending_claims,
        "documents": Document.objects.all()
    })