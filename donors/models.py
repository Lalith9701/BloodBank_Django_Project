from django.db import models
from accounts.models import User
from inventory.models import BloodGroup

class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.CASCADE)

    phone = models.CharField(max_length=15, unique=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    weight = models.FloatField()

    health_issue = models.BooleanField(default=False)
    health_issue_description = models.TextField(blank=True, null=True)
    health_document = models.FileField(
        upload_to='health_documents/',
        blank=True, null=True,
        help_text='Medical certificate, prescription, or any supporting document (PDF, JPG, PNG)'
    )
    
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

    @property
    def cooldown_days(self):
        """Returns required cooling period between blood donations: 90 days for men, 120 days for women."""
        if self.gender and self.gender.strip().lower() == 'female':
            return 120
        return 90

    def __str__(self):
        return self.user.username
