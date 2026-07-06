import re

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

import claims

from .models import Patient, HealthcareProvider, InsuranceProvider, Administrator, InsuranceCompany
from claims.models import Claim, Document
from complaints.models import Complaint
from notifications.models import Notification
from reports.models import AuditLog

User = get_user_model()

PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

PATIENT_PROFILE_FIELDS = [
    "insurance_number",
    "insurance_company",
    "policy_number",
    "membership_number",
    "insurance_card_number",
    "plan_type",
    "coverage_start_date",
    "coverage_end_date",
    "policy_status",
    "phone_number",
    "national_id",
    "date_of_birth",
    "gender",
    "address",
    "principal_member_name",
    "relationship_to_principal",
    "employer_name",
    "employer_code",
    "corporate_scheme_name",
    "next_of_kin_name",
    "next_of_kin_phone",
    "next_of_kin_relationship",
]


def is_admin(user):
    """System Administrator only. Administration of the system — not claim
    processing. Superusers are treated as admins for convenience/bootstrap."""
    return user.is_authenticated and (
        user.role == "ADMIN" or user.is_superuser
    )


def is_insurance_provider(user):
    """Insurance Provider — owns all claim-processing responsibilities.
    Superusers are also allowed through so an operator account can always
    unblock a stuck claim/complaint queue."""
    return user.is_authenticated and (
        user.role == "INSURANCE_PROVIDER" or user.is_superuser
    )


def record_action(user, action, entity="", entity_id=None):
    if user.is_authenticated:
        AuditLog.objects.create(
            user=user,
            action=action,
            entity=entity,
            entity_id=entity_id
        )


def dashboard_url_for(user):
    if user.is_superuser or user.role == "ADMIN":
        return "admin_dashboard"
    if user.role == "INSURANCE_PROVIDER":
        return "insurance_dashboard"
    if user.role == "PATIENT":
        return "patient_dashboard"
    if user.role == "PROVIDER":
        return "provider_dashboard"
    return "landing"


def landing_view(request):
    if request.user.is_authenticated:
        return redirect(dashboard_url_for(request.user))

    return render(request, "landing.html")


def validate_password(password, confirm_password):
    if password != confirm_password:
        return "Passwords do not match."

    if not re.match(PASSWORD_PATTERN, password):
        return (
            "Password must contain at least 8 characters, "
            "one uppercase letter, one lowercase letter, "
            "one number and one special character."
        )

    return None


def get_insurance_companies():
    return InsuranceCompany.objects.filter(is_active=True)


def get_lookup_id(value):
    match = re.search(r"\(#(\d+)\)\s*$", value or "")
    return match.group(1) if match else None


def get_patient_profile_data(request):
    insurance_company_id = (
        request.POST.get("insurance_company")
        or get_lookup_id(request.POST.get("insurance_company_search"))
    )

    return {
        "insurance_number": request.POST.get("insurance_number", "").strip(),
        "insurance_company": InsuranceCompany.objects.filter(
            id=insurance_company_id
        ).first() if insurance_company_id else None,
        "policy_number": request.POST.get("policy_number", "").strip(),
        "membership_number": request.POST.get("membership_number", "").strip(),
        "insurance_card_number": request.POST.get("insurance_card_number", "").strip(),
        "plan_type": request.POST.get("plan_type", ""),
        "coverage_start_date": request.POST.get("coverage_start_date") or None,
        "coverage_end_date": request.POST.get("coverage_end_date") or None,
        "policy_status": request.POST.get("policy_status", "PENDING_VERIFICATION"),
        "phone_number": request.POST.get("phone_number", "").strip(),
        "national_id": request.POST.get("national_id", "").strip(),
        "date_of_birth": request.POST.get("date_of_birth") or None,
        "gender": request.POST.get("gender", ""),
        "address": request.POST.get("address", "").strip(),
        "principal_member_name": request.POST.get("principal_member_name", "").strip(),
        "relationship_to_principal": request.POST.get("relationship_to_principal", "").strip(),
        "employer_name": request.POST.get("employer_name", "").strip(),
        "employer_code": request.POST.get("employer_code", "").strip(),
        "corporate_scheme_name": request.POST.get("corporate_scheme_name", "").strip(),
        "next_of_kin_name": request.POST.get("next_of_kin_name", "").strip(),
        "next_of_kin_phone": request.POST.get("next_of_kin_phone", "").strip(),
        "next_of_kin_relationship": request.POST.get("next_of_kin_relationship", "").strip(),
    }


def assign_patient_profile_data(patient, profile_data):
    for field, value in profile_data.items():
        setattr(patient, field, value)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            record_action(
                user,
                "Logged into the system",
                "User",
                user.id
            )

            return redirect(dashboard_url_for(user))

        return render(request, "login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        profile_data = get_patient_profile_data(request)

        password_error = validate_password(password, confirm_password)

        if password_error:
            return render(request, "register.html", {
                "error": password_error,
                "insurance_companies": get_insurance_companies(),
            })

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Username already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {
                "error": "Email already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        if Patient.objects.filter(
            insurance_number=profile_data["insurance_number"]
        ).exists():
            return render(request, "register.html", {
                "error": "Insurance number already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        user = User.objects.create_user(
            username=username,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            email=email,
            password=password,
            role="PATIENT"
        )

        patient = Patient(user=user)
        assign_patient_profile_data(patient, profile_data)

        patient.save()

        record_action(
            user,
            "Registered as a patient",
            "Patient",
            patient.id
        )

        return redirect("login")

    return render(request, "register.html", {
        "insurance_companies": get_insurance_companies(),
    })


@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("landing")


@login_required
def patient_dashboard(request):
    if request.user.role != "PATIENT":
        return redirect("login")

    patient = request.user.patient

    claims = Claim.objects.filter(patient=patient)
    complaints = Complaint.objects.filter(patient=patient)
    notifications = Notification.objects.filter(
        user=request.user,
        notification_status="UNREAD"
    )

    return render(request, "patient_dashboard.html", {
        "patient": patient,
        "total_claims": claims.count(),
        "approved_claims": claims.filter(
            claim_status="APPROVED"
        ).count(),
        "pending_claims": claims.filter(
            claim_status="PENDING"
        ).count(),
        "rejected_claims": claims.filter(
            claim_status="REJECTED"
        ).count(),
        "complaints": complaints.count(),
        "notifications": notifications.count(),
        "patient_name": request.user.get_full_name(),
        "insurance_number": patient.insurance_number,
    })


@login_required
def patient_profile(request):
    if request.user.role != "PATIENT":
        return redirect("login")

    patient = request.user.patient

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        profile_data = get_patient_profile_data(request)

        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return render(request, "patient_profile.html", {
                "patient": patient,
                "insurance_companies": get_insurance_companies(),
                "error": "Email address already exists."
            })

        if Patient.objects.filter(
            insurance_number=profile_data["insurance_number"]
        ).exclude(id=patient.id).exists():
            return render(request, "patient_profile.html", {
                "patient": patient,
                "insurance_companies": get_insurance_companies(),
                "error": "Insurance number already exists."
            })

        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.email = email
        request.user.save()

        assign_patient_profile_data(patient, profile_data)

        patient.save()

        record_action(
            request.user,
            "Updated patient profile",
            "Patient",
            patient.id
        )

        return render(request, "patient_profile.html", {
            "patient": patient,
            "insurance_companies": get_insurance_companies(),
            "success": "Your profile has been updated."
        })

    return render(request, "patient_profile.html", {
        "patient": patient,
        "insurance_companies": get_insurance_companies(),
    })


@login_required
def provider_dashboard(request):
    if request.user.role != "PROVIDER":
        return redirect("login")

    provider = request.user.healthcareprovider

    claims = Claim.objects.filter(provider=provider)
    notifications = Notification.objects.filter(
        user=request.user,
        notification_status="UNREAD"
    )

    return render(request, "provider_dashboard.html", {
        "provider": provider,
        "submitted_claims": claims.count(),
        "approved_claims": claims.filter(
            claim_status="APPROVED"
        ).count(),
        "pending_claims": claims.filter(
            claim_status="PENDING"
        ).count(),
        "rejected_claims": claims.filter(
            claim_status="REJECTED"
        ).count(),
        "notifications": notifications.count(),
        "provider_name": provider.hospital_name,
    })


@login_required
def insurance_dashboard(request):
    if not is_insurance_provider(request.user):
        return redirect("login")

    if request.user.role == "INSURANCE_PROVIDER" and not hasattr(request.user, "insuranceprovider"):
        InsuranceProvider.objects.create(user=request.user)

    insurance_profile = request.user.insuranceprovider

    # Only claims for this insurance company
    claims = Claim.objects.filter(
        insurance_company=insurance_profile.insurance_company
    )

    # Only documents belonging to those claims
    documents = Document.objects.filter(
        claim__insurance_company=insurance_profile.insurance_company
    )

    # Only complaints related to patients insured by this company
    complaints = Complaint.objects.filter(
        patient__insurance_company=insurance_profile.insurance_company
    )

    notifications_sent = Notification.objects.filter(
        sent_by=insurance_profile
    ).count()

    return render(request, "insurance_dashboard.html", {
        "insurance_name": request.user.get_full_name() or request.user.username,
        "insurance_company": insurance_profile.insurance_company,

        "total_claims": claims.count(),

        "pending_claims": claims.filter(
            claim_status="PENDING"
        ).count(),

        "approved_claims": claims.filter(
            claim_status="APPROVED"
        ).count(),

        "rejected_claims": claims.filter(
            claim_status="REJECTED"
        ).count(),

        "pending_document_verification": documents.filter(
            verification_status="PENDING"
        ).count(),

        "total_complaints": complaints.count(),

        "open_complaints": complaints.filter(
            complaint_status__in=["PENDING", "UNDER_REVIEW"]
        ).count(),

        "notifications_sent": notifications_sent,
    })


@login_required
def admin_dashboard(request):
    """System Administrator dashboard. Administration only — no claim
    approval/rejection, document verification, or complaint responses.
    Those belong exclusively to the Insurance Provider."""
    if not is_admin(request.user):
        return redirect("login")

    if not hasattr(request.user, "administrator"):
        Administrator.objects.create(user=request.user)

    return render(request, "admin_dashboard.html", {
        "admin_name": request.user.get_full_name() or request.user.username,
        "total_patients": Patient.objects.count(),
        "total_providers": HealthcareProvider.objects.count(),
        "total_insurance_providers": InsuranceProvider.objects.count(),
        "total_admins": Administrator.objects.count(),
        "total_users": User.objects.count(),
    })


@login_required
def create_provider(request):
    if not is_admin(request.user):
        return redirect("login")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        password_error = validate_password(password, confirm_password)

        if password_error:
            return render(request, "create_provider.html", {
                "error": password_error
            })

        if User.objects.filter(username=username).exists():
            return render(request, "create_provider.html", {
                "error": "Username already exists."
            })

        if User.objects.filter(email=email).exists():
            return render(request, "create_provider.html", {
                "error": "Email already exists."
            })

        if HealthcareProvider.objects.filter(
            license_number=request.POST.get("license_number")
        ).exists():
            return render(request, "create_provider.html", {
                "error": "License number already exists."
            })

        if request.POST.get("moh_registration_number") and HealthcareProvider.objects.filter(
            moh_registration_number=request.POST.get("moh_registration_number")
        ).exists():
            return render(request, "create_provider.html", {
                "error": "MOH registration number already exists."
            })

        user = User.objects.create_user(
            username=username,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            email=email,
            password=password,
            role="PROVIDER"
        )

        provider = HealthcareProvider.objects.create(
            user=user,
            hospital_name=request.POST.get("hospital_name"),
            license_number=request.POST.get("license_number"),
            specialization=request.POST.get("specialization"),
            facility_type=request.POST.get("facility_type", ""),
            moh_registration_number=request.POST.get("moh_registration_number", "").strip(),
            county=request.POST.get("county", "").strip(),
            physical_address=request.POST.get("physical_address", "").strip(),
            facility_phone=request.POST.get("facility_phone", "").strip(),
            facility_email=request.POST.get("facility_email", "").strip(),
            bed_capacity=request.POST.get("bed_capacity") or None,
            date_established=request.POST.get("date_established") or None,
        )

        record_action(
            request.user,
            "Created healthcare provider account",
            "HealthcareProvider",
            provider.id
        )

        return redirect("admin_dashboard")

    return render(request, "create_provider.html")


@login_required
def create_insurance_provider(request):
    """System Administrator creates Insurance Provider staff accounts."""
    if not is_admin(request.user):
        return redirect("login")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        password_error = validate_password(password, confirm_password)

        if password_error:
            return render(request, "create_insurance_provider.html", {
                "error": password_error,
                "insurance_companies": get_insurance_companies(),
            })

        if User.objects.filter(username=username).exists():
            return render(request, "create_insurance_provider.html", {
                "error": "Username already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        if User.objects.filter(email=email).exists():
            return render(request, "create_insurance_provider.html", {
                "error": "Email already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        employee_id = request.POST.get("employee_id", "").strip()
        if employee_id and InsuranceProvider.objects.filter(employee_id=employee_id).exists():
            return render(request, "create_insurance_provider.html", {
                "error": "Employee ID already exists.",
                "insurance_companies": get_insurance_companies(),
            })

        insurance_company_id = (
            request.POST.get("insurance_company")
            or get_lookup_id(request.POST.get("insurance_company_search"))
        )

        user = User.objects.create_user(
            username=username,
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            email=email,
            password=password,
            role="INSURANCE_PROVIDER"
        )

        insurance_provider = InsuranceProvider.objects.create(
            user=user,
            insurance_company=InsuranceCompany.objects.filter(id=insurance_company_id).first()
                if insurance_company_id else None,
            department=request.POST.get("department") or "Claims Processing",
            employee_id=employee_id or None,
            job_title=request.POST.get("job_title", ""),
            employment_type=request.POST.get("employment_type", "FULL_TIME"),
            office_branch=request.POST.get("office_branch", "").strip(),
            work_phone=request.POST.get("work_phone", "").strip(),
            work_email=request.POST.get("work_email", "").strip(),
            date_joined=request.POST.get("date_joined") or None,
            supervisor_name=request.POST.get("supervisor_name", "").strip(),
        )

        record_action(
            request.user,
            "Created insurance provider account",
            "InsuranceProvider",
            insurance_provider.id
        )

        return redirect("admin_dashboard")

    return render(request, "create_insurance_provider.html", {
        "insurance_companies": get_insurance_companies(),
    })

@login_required
def manage_users(request):
    """System Administrator: manage user accounts (activate/deactivate).
    Does not touch claims, documents, or complaints."""
    if not is_admin(request.user):
        return redirect("login")

    if request.method == "POST":
        target_user = User.objects.filter(id=request.POST.get("user_id")).first()

        if target_user and target_user.id != request.user.id:
            target_user.is_active = not target_user.is_active
            target_user.save()

            record_action(
                request.user,
                "Deactivated user account" if not target_user.is_active else "Reactivated user account",
                "User",
                target_user.id
            )

        return redirect("manage_users")

    return render(request, "manage_users.html", {
        "users": User.objects.all().order_by("role", "username")
    })


@login_required
def complaints(request):
    """Insurance Provider: View complaints from patients insured by their company."""
    if not is_insurance_provider(request.user):
        return redirect("login")

    insurance_profile = request.user.insuranceprovider
    company = insurance_profile.insurance_company

    if request.method == "POST":
        complaint = Complaint.objects.filter(
            id=request.POST.get("complaint_id"),
            patient__insurance_company=company
        ).first()

        action = request.POST.get("action")

        if complaint and action in (
            "UNDER_REVIEW",
            "RESOLVED",
            "CLOSED"
        ):
            complaint.complaint_status = action
            complaint.save()

            record_action(
                request.user,
                f"Marked complaint as {action.title()}",
                "Complaint",
                complaint.id
            )

        return redirect("complaints")

    status_filter = request.GET.get("status", "")

    complaint_list = Complaint.objects.filter(
        patient__insurance_company=company
    ).order_by("-id")

    if status_filter:
        complaint_list = complaint_list.filter(
            complaint_status=status_filter
        )

    return render(request, "complaints.html", {
        "complaints": complaint_list,
        "status_filter": status_filter,
    })

@login_required
def notifications(request):
    """Insurance Provider: view sent notifications and send new ones."""
    if not is_insurance_provider(request.user):
        return redirect("login")

    insurance_profile = getattr(request.user, "insuranceprovider", None)

    if request.method == "POST":
        recipient = User.objects.filter(id=request.POST.get("user_id")).first()
        message = request.POST.get("message", "").strip()

        if recipient and message:
            Notification.objects.create(
                user=recipient,
                sent_by=insurance_profile,
                message=message,
                notification_status="UNREAD",
            )

            record_action(
                request.user,
                "Sent notification",
                "Notification",
                recipient.id
            )

        return redirect("notifications")

    notification_list = Notification.objects.filter(
        sent_by=insurance_profile
    ).order_by("-id") if insurance_profile else Notification.objects.none()

    return render(request, "notifications.html", {
        "notifications": notification_list,
        "users": User.objects.exclude(id=request.user.id),
    })



@login_required
def manage_claims(request):
    """Insurance Provider: View and process only claims belonging to their insurance company."""
    if not is_insurance_provider(request.user):
        return redirect("login")

    insurance_profile = request.user.insuranceprovider
    company = insurance_profile.insurance_company

    if request.method == "POST":
        claim = Claim.objects.filter(
            id=request.POST.get("claim_id"),
            insurance_company=company
        ).first()

        action = request.POST.get("action")

        if claim and action == "approve":
            claim.claim_status = "APPROVED"
            claim.approved_by = insurance_profile
            claim.rejection_reason = ""
            claim.save()

            record_action(
                request.user,
                "Approved claim",
                "Claim",
                claim.id
            )

        elif claim and action == "reject":
            rejection_reason = request.POST.get(
                "rejection_reason",
                ""
            ).strip()

            if not rejection_reason:
                claims = Claim.objects.filter(
                    insurance_company=company
                ).order_by("-id")

                return render(request, "manage_claims.html", {
                    "claims": claims,
                    "error": "A reason is required to reject a claim."
                })

            claim.claim_status = "REJECTED"
            claim.rejection_reason = rejection_reason
            claim.approved_by = insurance_profile
            claim.save()

            record_action(
                request.user,
                f"Rejected claim: {rejection_reason}",
                "Claim",
                claim.id
            )

        return redirect("manage_claims")

    status_filter = request.GET.get("status", "")

    claims = Claim.objects.filter(
        insurance_company=company
    ).order_by("-id")

    if status_filter:
        claims = claims.filter(
            claim_status=status_filter
        )

    return render(request, "manage_claims.html", {
        "claims": claims,
        "status_filter": status_filter,
    })