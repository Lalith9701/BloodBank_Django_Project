from django.contrib import admin
from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'blood_group', 'phone', 'availability')
