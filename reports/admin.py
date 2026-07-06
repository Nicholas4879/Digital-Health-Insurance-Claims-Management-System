from django.contrib import admin
from .models import Report, AuditLog

admin.site.register(Report)
admin.site.register(AuditLog)