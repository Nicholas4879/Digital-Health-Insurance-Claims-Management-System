from django.db import models
from accounts.models import User


class Report(models.Model):
    REPORT_TYPES = (
        ('CLAIMS', 'Claims Report'),
        ('COMPLAINTS', 'Complaints Report'),
        ('PERFORMANCE', 'Performance Report'),
    )

    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    # Both the System Administrator (system reports) and the Insurance
    # Provider (insurance reports) can generate reports, so this points
    # directly at User rather than the old Administrator-only profile.
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_status = models.CharField(max_length=30, default='Generated')

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.report_type} Report"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    entity = models.CharField(max_length=100)
    entity_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action}"