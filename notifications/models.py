from django.db import models
from accounts.models import User, InsuranceProvider
from claims.models import Claim


class Notification(models.Model):
    STATUS_CHOICES = (
        ('UNREAD', 'Unread'),
        ('READ', 'Read'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, null=True, blank=True)
    # Sending notifications is an Insurance Provider responsibility, not an
    # Administrator one.
    sent_by = models.ForeignKey(InsuranceProvider, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    notification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNREAD')
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return self.message[:50]