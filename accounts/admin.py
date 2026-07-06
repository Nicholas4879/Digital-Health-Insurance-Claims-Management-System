from django.contrib import admin
from .models import User, Patient, HealthcareProvider, Administrator, InsuranceCompany

admin.site.register(User)
admin.site.register(Patient)
admin.site.register(HealthcareProvider)
admin.site.register(Administrator)
admin.site.register(InsuranceCompany)
