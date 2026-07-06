from django.shortcuts import render

def landing(request):
    """
    Landing Page
    """

    patient_count = Patient.objects.count()

    provider_count = HealthcareProvider.objects.count()

    admin_count = Administrator.objects.count()

    claim_count = Claim.objects.count()

    approved_claims = Claim.objects.filter(
        claim_status="APPROVED"
    ).count()

    pending_claims = Claim.objects.filter(
        claim_status="PENDING"
    ).count()

    rejected_claims = Claim.objects.filter(
        claim_status="REJECTED"
    ).count()

    complaint_count = Complaint.objects.count()

    report_count = Report.objects.count()

    notification_count = Notification.objects.count()

    latest_claims = Claim.objects.order_by(
        "-submission_date"
    )[:5]

    latest_complaints = Complaint.objects.order_by(
        "-created_at"
    )[:5]

    recent_notifications = Notification.objects.order_by(
        "-sent_at"
    )[:5]

    context = {

        "patient_count": patient_count,

        "provider_count": provider_count,

        "admin_count": admin_count,

        "claim_count": claim_count,

        "approved_claims": approved_claims,

        "pending_claims": pending_claims,

        "rejected_claims": rejected_claims,

        "complaint_count": complaint_count,

        "report_count": report_count,

        "notification_count": notification_count,

        "latest_claims": latest_claims,

        "latest_complaints": latest_complaints,

        "recent_notifications": recent_notifications,

    }

    return render(
        request,
        "landing.html",
        context,
    )