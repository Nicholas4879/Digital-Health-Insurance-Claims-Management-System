from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('PROVIDER', 'Healthcare Provider'),
        ('INSURANCE_PROVIDER', 'Insurance Provider'),
        ('ADMIN', 'Administrator'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='PATIENT'
    )


class InsuranceCompany(models.Model):
    name = models.CharField(max_length=100, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    contact_email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    


class Patient(models.Model):
    PLAN_CHOICES = (
        ('', 'Select plan type'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
        ('CORPORATE', 'Corporate'),
        ('FAMILY', 'Family'),
    )

    POLICY_STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('PENDING_VERIFICATION', 'Pending Verification'),
    )

    VERIFICATION_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    insurance_number = models.CharField(max_length=50, unique=True)
    insurance_company = models.ForeignKey(
    InsuranceCompany,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="patients"
)
    policy_number = models.CharField(max_length=50, blank=True)
    membership_number = models.CharField(max_length=50, blank=True)
    insurance_card_number = models.CharField(max_length=50, blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True)
    coverage_start_date = models.DateField(null=True, blank=True)
    coverage_end_date = models.DateField(null=True, blank=True)
    policy_status = models.CharField(
        max_length=30,
        choices=POLICY_STATUS_CHOICES,
        default='PENDING_VERIFICATION'
    )
    phone_number = models.CharField(max_length=30, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    principal_member_name = models.CharField(max_length=100, blank=True)
    relationship_to_principal = models.CharField(max_length=50, blank=True)
    employer_name = models.CharField(max_length=100, blank=True)
    employer_code = models.CharField(max_length=50, blank=True)
    corporate_scheme_name = models.CharField(max_length=100, blank=True)
    next_of_kin_name = models.CharField(max_length=100, blank=True)
    next_of_kin_phone = models.CharField(max_length=30, blank=True)
    next_of_kin_relationship = models.CharField(max_length=50, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='PENDING'
    )

    def __str__(self):
        return self.user.get_full_name()


class HealthcareProvider(models.Model):
    FACILITY_TYPE_CHOICES = (
        ('', 'Select facility type'),
        ('HOSPITAL', 'Hospital'),
        ('CLINIC', 'Clinic'),
        ('DIAGNOSTIC_LAB', 'Diagnostic Laboratory'),
        ('PHARMACY', 'Pharmacy'),
        ('DENTAL', 'Dental Clinic'),
        ('MATERNITY', 'Maternity Home'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=100, blank=True)

    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPE_CHOICES, blank=True)
    moh_registration_number = models.CharField(
        max_length=50, blank=True,
        help_text="Ministry of Health / KMPDC facility registration number"
    )
    county = models.CharField(max_length=100, blank=True)
    physical_address = models.TextField(blank=True)
    facility_phone = models.CharField(max_length=30, blank=True)
    facility_email = models.EmailField(blank=True)
    bed_capacity = models.PositiveIntegerField(null=True, blank=True)
    date_established = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.hospital_name


class InsuranceProvider(models.Model):
    """
    Staff profile for the INSURANCE_PROVIDER role. This role owns all
    claim-processing responsibilities that used to live on Administrator
    (approving/rejecting claims, verifying documents, responding to
    complaints, sending notifications, generating insurance reports).
    """
    JOB_TITLE_CHOICES = (
        ('', 'Select job title'),
        ('CLAIMS_OFFICER', 'Claims Officer'),
        ('CLAIMS_MANAGER', 'Claims Manager'),
        ('DOCUMENT_VERIFICATION_OFFICER', 'Document Verification Officer'),
        ('UNDERWRITER', 'Underwriter'),
        ('CUSTOMER_SERVICE_OFFICER', 'Customer Service Officer'),
        ('BRANCH_MANAGER', 'Branch Manager'),
    )

    EMPLOYMENT_TYPE_CHOICES = (
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACT', 'Contract'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    insurance_company = models.ForeignKey(
        InsuranceCompany, on_delete=models.SET_NULL, null=True, blank=True
    )
    department = models.CharField(max_length=100, default="Claims Processing")
    employee_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    job_title = models.CharField(max_length=40, choices=JOB_TITLE_CHOICES, blank=True)
    employment_type = models.CharField(
        max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='FULL_TIME'
    )
    office_branch = models.CharField(max_length=100, blank=True)
    work_phone = models.CharField(max_length=30, blank=True)
    work_email = models.EmailField(blank=True)
    date_joined = models.DateField(null=True, blank=True)
    supervisor_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class Administrator(models.Model):
    """
    Staff profile for the ADMIN role. Scope is limited to system
    administration only: creating provider/insurance-provider accounts,
    managing user accounts, audit logs, and system reports. Administrators
    no longer approve/reject claims, verify documents, or respond to
    complaints — that is exclusively the InsuranceProvider's job.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_level = models.CharField(max_length=50, default="Standard")

    def __str__(self):
        return self.user.get_full_name()