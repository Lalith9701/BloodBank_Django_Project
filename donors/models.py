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
    availability = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
