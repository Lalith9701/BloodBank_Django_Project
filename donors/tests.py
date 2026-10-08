from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import BloodGroup
from donors.models import Donor
from requests_app.models import Donation

User = get_user_model()

class LifeDropRewardSystemTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.bg = BloodGroup.objects.create(blood_group='O+')
        self.donor_user = User.objects.create_user(
            username='9876543210',
            password='Password123!',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            role='DONOR'
        )
        self.donor = Donor.objects.create(
            user=self.donor_user,
            blood_group=self.bg,
            phone='9876543210',
            age=28,
            gender='Male',
            weight=70.0,
            eligibility_status='ELIGIBLE',
            availability=True,
            life_points=0
        )

    def test_initial_level_is_life_saver(self):
        info = self.donor.reward_info
        self.assertEqual(info['points'], 0)
        self.assertEqual(info['level_name'], 'Life Saver')
        self.assertEqual(info['next_level_name'], 'Life Guardian')
        self.assertEqual(info['points_needed'], 200)

    def test_points_accumulation_and_level_up(self):
        # 1st donation: 1 unit => 100 Pts
        Donation.objects.create(donor=self.donor, blood_group=self.bg, units=1)
        self.donor.refresh_from_db()
        self.donor.life_points += 100
        self.donor.save()

        info = self.donor.reward_info
        self.assertEqual(info['points'], 100)
        self.assertEqual(info['level_name'], 'Life Saver')

        # 2nd donation: 1 unit => 200 Pts Total => Life Guardian!
        Donation.objects.create(donor=self.donor, blood_group=self.bg, units=1)
        self.donor.life_points += 100
        self.donor.save()

        info = self.donor.reward_info
        self.assertEqual(info['points'], 200)
        self.assertEqual(info['level_name'], 'Life Guardian')
        self.assertEqual(info['next_level_name'], 'Life Hero')

        # Add 300 more points => 500 Pts Total => Life Hero!
        self.donor.life_points = 500
        self.donor.save()
        info = self.donor.reward_info
        self.assertEqual(info['level_name'], 'Life Hero')
        self.assertEqual(info['next_level_name'], 'Life Champion')

        # Add 500 more points => 1000 Pts Total => Life Champion!
        self.donor.life_points = 1000
        self.donor.save()
        info = self.donor.reward_info
        self.assertEqual(info['level_name'], 'Life Champion')
        self.assertIsNone(info['next_level_name'])

    def test_rewards_view_requires_login(self):
        response = self.client.get(reverse('donor_rewards'))
        self.assertEqual(response.status_code, 302)

    def test_rewards_view_authenticated(self):
        self.client.login(username='9876543210', password='Password123!')
        response = self.client.get(reverse('donor_rewards'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'LIFE DROP DONOR REWARD SYSTEM')
        self.assertContains(response, 'Life Saver')

    def test_family_certificate_view(self):
        self.client.login(username='9876543210', password='Password123!')
        response = self.client.get(reverse('donor_family_certificate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Certificate of Family Support Eligibility')
