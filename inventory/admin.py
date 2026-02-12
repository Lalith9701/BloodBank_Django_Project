from django.contrib import admin
from .models import BloodGroup, BloodStock


@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'blood_group')


@admin.register(BloodStock)
class BloodStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'blood_group', 'units_available')
