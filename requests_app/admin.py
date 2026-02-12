from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import BloodRequest
from inventory.models import BloodStock


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'units_required', 'status', 'request_date')
    list_filter = ('status', 'blood_group')
    actions = ['approve_requests', 'reject_requests']

    # ✅ APPROVE ACTION
    def approve_requests(self, request, queryset):
        for obj in queryset:

            # If already approved, skip
            if obj.status == 'APPROVED':
                self.message_user(
                    request,
                    f"{obj} is already approved.",
                    level=messages.WARNING
                )
                continue

            # Get stock (must exist)
            try:
                stock = BloodStock.objects.get(blood_group=obj.blood_group)
            except BloodStock.DoesNotExist:
                self.message_user(
                    request,
                    f"No stock record found for {obj.blood_group}",
                    level=messages.ERROR
                )
                continue

            # Check stock availability
            if stock.units_available >= obj.units_required:
                stock.units_available -= obj.units_required
                stock.save()

                obj.status = 'APPROVED'
                obj.save()

                self.message_user(
                    request,
                    f"Request approved for {obj.user}",
                    level=messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"Not enough stock for {obj.blood_group}",
                    level=messages.ERROR
                )

    approve_requests.short_description = "Approve selected requests"

    # ✅ REJECT ACTION
    def reject_requests(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(
            request,
            f"{updated} request(s) rejected.",
            level=messages.WARNING
        )

    reject_requests.short_description = "Reject selected requests"
