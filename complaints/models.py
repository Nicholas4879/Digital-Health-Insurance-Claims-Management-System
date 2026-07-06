from django.db import models
from accounts.models import Patient, InsuranceProvider
from claims.models import Claim


class Complaint(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('RESOLVED', 'Resolved'),
    )

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    complaint_message = models.TextField()
    complaint_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    response = models.TextField(blank=True)
    # Responding to patient inquiries is an Insurance Provider
    # responsibility, not an Administrator one.
    resolved_by = models.ForeignKey(InsuranceProvider, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint {self.id} - {self.complaint_status}"