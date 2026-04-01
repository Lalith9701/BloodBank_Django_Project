from django.db import models
from accounts.models import User
from requests_app.models import BloodRequest

class Rating(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    blood_request = models.OneToOneField(BloodRequest, on_delete=models.CASCADE, related_name='rating')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    
    # User's request for "Donor + Service rating"
    donor_rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    service_rating = models.PositiveIntegerField(choices=RATING_CHOICES, default=5)
    
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.blood_request} by {self.rater}"
