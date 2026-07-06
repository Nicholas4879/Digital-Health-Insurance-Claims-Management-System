from django.db import models
from accounts.models import (
    Patient,
    HealthcareProvider,
    InsuranceProvider,
    InsuranceCompany,
)

class Claim(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    claim_type = models.CharField(max_length=100)
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    claim_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submission_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    provider = models.ForeignKey(HealthcareProvider, on_delete=models.CASCADE)
    insurance_company = models.ForeignKey(
    InsuranceCompany,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="claims"
)
    approved_by = models.ForeignKey(
    InsuranceProvider,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)

    def __str__(self):
        return f"Claim {self.id} - {self.claim_status}"


class Document(models.Model):
    VERIFICATION_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    document_name = models.CharField(max_length=100)
    document_type = models.CharField(max_length=100)
    file_path = models.FileField(upload_to='documents/')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(
    InsuranceProvider,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.document_name
