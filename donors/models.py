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

    life_points = models.PositiveIntegerField(
        default=0,
        help_text="Total Life Points earned through verified blood donations."
    )

    def recalculate_life_points(self):
        """Recalculates life points based on actual completed donations."""
        total_units = sum(d.units for d in self.donation_set.all())
        self.life_points = total_units * 100
        self.save(update_fields=['life_points'])
        return self.life_points

    @property
    def total_donations_count(self):
        return self.donation_set.count()

    @property
    def total_units_donated(self):
        return sum(d.units for d in self.donation_set.all())

    @property
    def reward_info(self):
        """Returns comprehensive LIFE DROP reward level details and progress metrics."""
        donations = list(self.donation_set.all())
        total_units = sum(d.units for d in donations)
        effective_points = self.life_points
        if effective_points == 0 and total_units > 0:
            effective_points = total_units * 100
            Donor.objects.filter(pk=self.pk).update(life_points=effective_points)
            self.life_points = effective_points

        points = effective_points
        if points >= 1000:
            level_name = "Life Champion"
            level_icon = "bi-trophy-fill"
            badge_bg = "bg-warning text-dark border border-warning"
            badge_color = "#ffc107"
            next_level_name = None
            next_level_points = 1000
            points_needed = 0
            progress_percent = 100
        elif points >= 500:
            level_name = "Life Hero"
            level_icon = "bi-award-fill"
            badge_bg = "bg-primary text-white"
            badge_color = "#4361ee"
            next_level_name = "Life Champion"
            next_level_points = 1000
            points_needed = 1000 - points
            progress_percent = min(100, int(((points - 500) / 500) * 100))
        elif points >= 200:
            level_name = "Life Guardian"
            level_icon = "bi-shield-check"
            badge_bg = "bg-info text-dark"
            badge_color = "#0dcaf0"
            next_level_name = "Life Hero"
            next_level_points = 500
            points_needed = 500 - points
            progress_percent = min(100, int(((points - 200) / 300) * 100))
        else:
            level_name = "Life Saver"
            level_icon = "bi-heart-pulse-fill"
            badge_bg = "bg-secondary text-white"
            badge_color = "#6c757d"
            next_level_name = "Life Guardian"
            next_level_points = 200
            points_needed = 200 - points
            progress_percent = min(100, int((points / 200) * 100))

        return {
            'points': points,
            'level_name': level_name,
            'level_icon': level_icon,
            'badge_bg': badge_bg,
            'badge_color': badge_color,
            'next_level_name': next_level_name,
            'next_level_points': next_level_points,
            'points_needed': points_needed,
            'progress_percent': progress_percent,
            'total_donations': len(donations),
            'total_units': total_units,
            'family_support_eligible': len(donations) >= 1,
        }

    @property
    def achievements(self):
        r = self.reward_info
        donations = r['total_donations']
        points = r['points']

        return [
            {
                'id': 'first_drop',
                'title': 'First Life Drop',
                'description': 'Completed your 1st blood donation.',
                'icon': 'bi-droplet-half',
                'color': '#ef4444',
                'unlocked': donations >= 1,
                'progress': 100 if donations >= 1 else 0
            },
            {
                'id': 'life_guardian',
                'title': 'Guardian Shield',
                'description': 'Reached 200 Life Points milestone.',
                'icon': 'bi-shield-fill-check',
                'color': '#0ea5e9',
                'unlocked': points >= 200,
                'progress': min(100, int((points / 200) * 100))
            },
            {
                'id': 'triple_savior',
                'title': 'Triple Life Saver',
                'description': 'Completed 3 voluntary blood donations.',
                'icon': 'bi-lightning-charge-fill',
                'color': '#f59e0b',
                'unlocked': donations >= 3,
                'progress': min(100, int((donations / 3) * 100))
            },
            {
                'id': 'life_hero',
                'title': 'Heroic Vanguard',
                'description': 'Reached 500 Life Points milestone.',
                'icon': 'bi-award-fill',
                'color': '#8b5cf6',
                'unlocked': points >= 500,
                'progress': min(100, int((points / 500) * 100))
            },
            {
                'id': 'life_champion',
                'title': 'Champion of Humanity',
                'description': 'Reached 1000+ Life Points legend status.',
                'icon': 'bi-trophy-fill',
                'color': '#eab308',
                'unlocked': points >= 1000,
                'progress': min(100, int((points / 1000) * 100))
            },
            {
                'id': 'family_priority',
                'title': 'Family Support Member',
                'description': 'Unlocked priority donor-support benefits for immediate family.',
                'icon': 'bi-people-fill',
                'color': '#10b981',
                'unlocked': donations >= 1,
                'progress': 100 if donations >= 1 else 0
            }
        ]

    @property
    def cooldown_days(self):
        """Returns required cooling period between blood donations: 90 days for men, 120 days for women."""
        if self.gender and self.gender.strip().lower() == 'female':
            return 120
        return 90

    def __str__(self):
        return self.user.username

