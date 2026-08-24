from django.db import models
from requests_app.models import BloodRequest


class AgentExecutionLog(models.Model):
    TRIGGER_CHOICES = (
        ('AUTOMATIC', 'Automatic (System Request)'),
        ('MANUAL_ADMIN', 'Manual Staff Trigger'),
    )

    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='agent_logs'
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_CHOICES,
        default='AUTOMATIC'
    )
    requested_blood_group = models.CharField(max_length=10)
    units_requested = models.PositiveIntegerField()
    stock_available = models.PositiveIntegerField(default=0)
    
    # Stores list of compatible blood groups checked (e.g. ["O-", "A-"])
    compatible_blood_groups = models.CharField(max_length=255)
    
    eligible_donors_found = models.PositiveIntegerField(default=0)
    donors_notified_count = models.PositiveIntegerField(default=0)
    
    # Detailed natural language breakdown of the agent's logic and decision-making
    reasoning_summary = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Agent Run #{self.id} for Request #{self.blood_request_id} ({self.requested_blood_group})"
