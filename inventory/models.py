from django.db import models

class BloodGroup(models.Model):
    blood_group = models.CharField(max_length=5, unique=True)

    def __str__(self):
        return self.blood_group


class BloodStock(models.Model):
    blood_group = models.OneToOneField(BloodGroup, on_delete=models.CASCADE)
    units_available = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.blood_group} - {self.units_available} units"
