from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from inventory.models import BloodGroup, BloodStock
from donors.models import Donor
from requests_app.models import BloodRequest, Donation
from notifications.models import Notification
from agents.models import AgentExecutionLog
from agents.services.compatibility import get_compatible_donor_groups
from agents.services.emergency_agent import run_emergency_dispatch_agent

User = get_user_model()


class BloodCompatibilityTestCase(TestCase):
    def test_o_negative_compatibility(self):
        # O- can only receive from O-
        groups = get_compatible_donor_groups('O-')
        self.assertEqual(groups, ['O-'])

    def test_ab_positive_compatibility(self):
        # AB+ is universal recipient
        groups = get_compatible_donor_groups('AB+')
        self.assertEqual(len(groups), 8)
        self.assertIn('O-', groups)
        self.assertIn('AB+', groups)

    def test_a_positive_compatibility(self):
        # A+ can receive from O-, O+, A-, A+
        groups = get_compatible_donor_groups('A+')
        self.assertEqual(set(groups), {'O-', 'O+', 'A-', 'A+'})


class EmergencyAgentTestCase(TestCase):
    def setUp(self):
        self.group_o_neg = BloodGroup.objects.create(blood_group='O-')
        self.group_a_pos = BloodGroup.objects.create(blood_group='A+')

        BloodStock.objects.create(blood_group=self.group_a_pos, units_available=0)
        BloodStock.objects.create(blood_group=self.group_o_neg, units_available=2)

        # Create Requester
        self.requester = User.objects.create_user(
            username='requester_user',
            email='requester@example.com',
            password='password123',
            role='REQUESTER'
        )

        # Create Admin
        self.admin = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='password123',
            role='ADMIN',
            is_staff=True
        )

        # Create Donor 1 (A+, Eligible)
        self.donor_user1 = User.objects.create_user(
            username='donor1',
            email='donor1@example.com',
            password='password123',
            role='DONOR'
        )
        self.donor1 = Donor.objects.create(
            user=self.donor_user1,
            blood_group=self.group_a_pos,
            phone='9000000002',
            age=25,
            gender='Male',
            weight=70.0,
            availability=True,
            eligibility_status='ELIGIBLE'
        )

        # Create Donor 2 (O- Universal Donor, Eligible)
        self.donor_user2 = User.objects.create_user(
            username='donor2',
            email='donor2@example.com',
            password='password123',
            role='DONOR'
        )
        self.donor2 = Donor.objects.create(
            user=self.donor_user2,
            blood_group=self.group_o_neg,
            phone='9000000003',
            age=30,
            gender='Female',
            weight=65.0,
            availability=True,
            eligibility_status='ELIGIBLE'
        )

        # Create Donor 3 (A+, in 90-day cooldown)
        self.donor_user3 = User.objects.create_user(
            username='donor3',
            email='donor3@example.com',
            password='password123',
            role='DONOR'
        )
        self.donor3 = Donor.objects.create(
            user=self.donor_user3,
            blood_group=self.group_a_pos,
            phone='9000000004',
            age=28,
            gender='Male',
            weight=75.0,
            availability=True,
            eligibility_status='ELIGIBLE'
        )
        # Record recent donation 10 days ago for donor3
        Donation.objects.create(
            donor=self.donor3,
            blood_group=self.group_a_pos,
            units=1
        )

    def test_run_emergency_dispatch_agent(self):
        # Create Emergency request for A+ (stock = 0)
        req = BloodRequest.objects.create(
            user=self.requester,
            blood_group=self.group_a_pos,
            units_required=3,
            urgency='EMERGENCY',
            status='PENDING'
        )

        log = run_emergency_dispatch_agent(req.id, trigger_type='AUTOMATIC')

        self.assertIsNotNone(log)
        self.assertEqual(log.blood_request, req)
        self.assertEqual(log.stock_available, 1)
        self.assertIn('O-', log.compatible_blood_groups)
        self.assertIn('A+', log.compatible_blood_groups)

        # donor1 (A+) and donor2 (O-) should be notified. donor3 (cooldown) should NOT be notified.
        self.assertEqual(log.donors_notified_count, 2)

        # Verify notification created for donor1 and donor2
        notifs_donor1 = Notification.objects.filter(user=self.donor_user1)
        self.assertTrue(notifs_donor1.exists())

        notifs_donor2 = Notification.objects.filter(user=self.donor_user2)
        self.assertTrue(notifs_donor2.exists())

        notifs_donor3 = Notification.objects.filter(user=self.donor_user3)
        self.assertFalse(notifs_donor3.exists())

    def test_auto_approval_when_stock_available_and_verified(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        dummy_prescription = SimpleUploadedFile("prescription.pdf", b"Dummy PDF content", content_type="application/pdf")

        # Ensure O- stock is 5 units
        stock_o_neg = BloodStock.objects.get(blood_group=self.group_o_neg)
        stock_o_neg.units_available = 5
        stock_o_neg.save()

        # Submit fully verified request
        req = BloodRequest.objects.create(
            user=self.requester,
            blood_group=self.group_o_neg,
            units_required=2,
            urgency='NORMAL',
            purpose='Emergency Surgery',
            patient_name='Rahul Kumar',
            patient_phone='9876543210',
            patient_gender='Male',
            patient_address='Apollo Hospital, Room 302',
            prescription_document=dummy_prescription,
            status='PENDING'
        )

        log = run_emergency_dispatch_agent(req.id, trigger_type='AUTOMATIC')

        # Verify status auto-approved
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')

        # Stock deducted: 5 - 2 = 3
        stock_o_neg.refresh_from_db()
        self.assertEqual(stock_o_neg.units_available, 3)

        # Log mentions all tiers passed
        self.assertIn("ALL TIERS PASSED", log.reasoning_summary)

    def test_handover_to_admin_when_prescription_missing(self):
        stock_o_neg = BloodStock.objects.get(blood_group=self.group_o_neg)
        stock_o_neg.units_available = 5
        stock_o_neg.save()

        # Submit request missing prescription
        req = BloodRequest.objects.create(
            user=self.requester,
            blood_group=self.group_o_neg,
            units_required=2,
            urgency='NORMAL',
            purpose='General',
            patient_name='Rahul Kumar',
            patient_phone='9876543210',
            patient_gender='Male',
            patient_address='City Hospital',
            prescription_document=None, # Missing prescription
            status='PENDING'
        )

        log = run_emergency_dispatch_agent(req.id, trigger_type='AUTOMATIC')

        # Status remains PENDING for Admin Review
        req.refresh_from_db()
        self.assertEqual(req.status, 'PENDING')

        # Stock remains undeducted
        stock_o_neg.refresh_from_db()
        self.assertEqual(stock_o_neg.units_available, 5)

        # Log mentions handover to admin review
        self.assertIn("HANDOVER TO ADMIN REVIEW", log.reasoning_summary)

