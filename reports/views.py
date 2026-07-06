from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from claims.models import Claim
from complaints.models import Complaint
from .models import Report, AuditLog


def can_generate_reports(user):
    """Both the System Administrator (system reports) and the Insurance
    Provider (insurance reports) can generate reports from this shared
    view — the report_type dropdown covers both use cases."""
    return user.is_authenticated and (
        user.role in ["ADMIN", "INSURANCE_PROVIDER"] or user.is_superuser
    )


@login_required
def reports_view(request):
    if not can_generate_reports(request.user):
        return render(request, "reports.html", {
            "error": "Only administrators and insurance providers can access reports."
        })

    if request.method == "POST":
        report_type = request.POST.get("report_type")

        report = Report.objects.create(
            report_type=report_type,
            generated_by=request.user,
            report_status="Generated"
        )

        AuditLog.objects.create(
            user=request.user,
            action="Generated report",
            entity="Report",
            entity_id=report.id
        )

        return redirect(f"{reverse('reports')}?type={report_type}")

    selected_type = request.GET.get("type", "")

    total_claims = Claim.objects.count()
    approved_claims = Claim.objects.filter(claim_status="APPROVED").count()
    rejected_claims = Claim.objects.filter(claim_status="REJECTED").count()
    pending_claims = Claim.objects.filter(claim_status="PENDING").count()
    total_complaints = Complaint.objects.count()

    approval_rate = round(
        (approved_claims / total_claims) * 100, 1
    ) if total_claims else 0

    context = {
        "reports": Report.objects.all(),
        "selected_type": selected_type,
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "pending_claims": pending_claims,
        "total_complaints": total_complaints,
        "approval_rate": approval_rate,
    }

    if selected_type == "CLAIMS":
        context["report_claims"] = Claim.objects.all().order_by("-submission_date")
    elif selected_type == "COMPLAINTS":
        context["report_complaints"] = Complaint.objects.all()

    return render(request, "reports.html", context)


@login_required
def audit_logs_view(request):
    """System Administrator only. Insurance Providers must not see audit
    logs — that stays exclusively with system administration."""
    if not (request.user.role == "ADMIN" or request.user.is_superuser):
        return redirect("login")

    return render(request, "audit_logs.html", {
        "logs": AuditLog.objects.all().order_by("-timestamp")
    })