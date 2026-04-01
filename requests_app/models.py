from django.db import models
from accounts.models import User
from inventory.models import BloodGroup, BloodStock
from donors.models import Donor


# =====================================
# BLOOD REQUEST MODEL
# =====================================
class BloodRequest(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    URGENCY_CHOICES = (
        ('NORMAL', 'Normal'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE)
    units_required = models.PositiveIntegerField()

    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default='NORMAL'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    rejection_reason = models.TextField(blank=True, null=True)
    
    # Optional: track which donor fulfilled the request (useful for ratings)
    donor = models.ForeignKey(Donor, on_delete=models.SET_NULL, blank=True, null=True, related_name='fulfilled_requests')

    request_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if self.pk:
            old_request = BloodRequest.objects.get(pk=self.pk)

            # If request is being approved
            if old_request.status != 'APPROVED' and self.status == 'APPROVED':

                stock, created = BloodStock.objects.get_or_create(
                    blood_group=self.blood_group,
                    defaults={'units_available': 0}
                )

                # Check stock availability
                if stock.units_available >= self.units_required:
                    stock.units_available -= self.units_required
                    stock.save()
                else:
                    # Automatically reject if stock not enough
                    self.status = 'REJECTED'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.blood_group}"


# =====================================
# DONATION MODEL
# =====================================
class Donation(models.Model):

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE)
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE)
    units = models.PositiveIntegerField()
    donation_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        stock, created = BloodStock.objects.get_or_create(
            blood_group=self.blood_group,
            defaults={'units_available': 0}
        )

        stock.units_available += self.units
        stock.save()

    def __str__(self):
        return f"{self.donor.user.username} - {self.units} units"