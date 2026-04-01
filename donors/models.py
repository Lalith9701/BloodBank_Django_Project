from django.db import models
from accounts.models import User
from inventory.models import BloodGroup

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE)

    phone = models.CharField(max_length=15)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    weight = models.FloatField()

    health_issue = models.BooleanField(default=False)
    health_issue_description = models.TextField(blank=True, null=True)
    
    ELIGIBILITY_CHOICES = (
        ('ELIGIBLE', 'Eligible'),
        ('PENDING', 'Pending Approval'),
        ('REJECTED', 'Rejected'),
    )
    eligibility_status = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES, default='ELIGIBLE')

    availability = models.BooleanField(default=True)

    # Address/Location Information
    address = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    nation = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username
