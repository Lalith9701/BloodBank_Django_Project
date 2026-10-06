from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from inventory.models import BloodGroup
from donors.models import Donor

User = get_user_model()

class DonorRegistrationValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bg = BloodGroup.objects.create(blood_group='A+')
        self.register_url = reverse('register')

    def test_invalid_email_format_numeric_username(self):
        """Test registration with invalid email format (e.g., 123@gmail.com) is rejected."""
        response = self.client.post(self.register_url, {
            'full_name': 'Test User',
            'email': '123@gmail.com',
            'phone': '9876543210',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '25',
            'gender': 'Male',
            'weight': '60',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('field_errors', response.context)
        self.assertIn('email', response.context['field_errors'])
        self.assertTrue(any('Enter a valid email address' in m for m in response.context['field_errors']['email']))

    def test_valid_email_format(self):
        """Test registration with valid email format (johndoe111@gmail.com) is accepted."""
        response = self.client.post(self.register_url, {
            'full_name': 'John Doe',
            'email': 'johndoe111@gmail.com',
            'phone': '9876543210',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '25',
            'gender': 'Male',
            'weight': '60',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='9876543210').exists())

    def test_age_out_of_range_below_18(self):
        """Test registration with age below 18 is rejected."""
        response = self.client.post(self.register_url, {
            'full_name': 'Young User',
            'email': 'young@gmail.com',
            'phone': '9876543211',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '17',
            'gender': 'Male',
            'weight': '50',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('age', response.context['field_errors'])
        self.assertTrue(any('18 and 65' in m for m in response.context['field_errors']['age']))

    def test_age_out_of_range_above_65(self):
        """Test registration with age above 65 is rejected."""
        response = self.client.post(self.register_url, {
            'full_name': 'Senior User',
            'email': 'senior@gmail.com',
            'phone': '9876543212',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '66',
            'gender': 'Male',
            'weight': '60',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('age', response.context['field_errors'])
        self.assertTrue(any('18 and 65' in m for m in response.context['field_errors']['age']))

    def test_weight_below_45(self):
        """Test registration with weight under 45 kg is rejected."""
        response = self.client.post(self.register_url, {
            'full_name': 'Low Weight User',
            'email': 'lowweight@gmail.com',
            'phone': '9876543213',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '25',
            'gender': 'Female',
            'weight': '44.5',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('weight', response.context['field_errors'])
        self.assertTrue(any('at least 45 kg' in m for m in response.context['field_errors']['weight']))

    def test_phone_number_not_10_digits(self):
        """Test registration with phone length != 10 digits is rejected."""
        response = self.client.post(self.register_url, {
            'full_name': 'Bad Phone User',
            'email': 'badphone@gmail.com',
            'phone': '98765432101', # 11 digits
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'blood_group': str(self.bg.id),
            'age': '25',
            'gender': 'Male',
            'weight': '60',
            'health_issue': 'False',
            'security_question': 'q1',
            'security_answer': 'Fluffy',
            'address': '123 Main St',
            'pincode': '400001',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'nation': 'India',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('phone', response.context['field_errors'])
        self.assertTrue(any('exactly 10 digits' in m for m in response.context['field_errors']['phone']))

    def test_gender_based_cooldown_property(self):
        """Test Donor.cooldown_days returns 90 for Male and 120 for Female."""
        male_user = User.objects.create_user(username='9000000001', password='Password123!', email='male@test.com', role='DONOR')
        female_user = User.objects.create_user(username='9000000002', password='Password123!', email='female@test.com', role='DONOR')

        male_donor = Donor.objects.create(user=male_user, phone='9000000001', blood_group=self.bg, age=25, gender='Male', weight=60)
        female_donor = Donor.objects.create(user=female_user, phone='9000000002', blood_group=self.bg, age=25, gender='Female', weight=55)

        self.assertEqual(male_donor.cooldown_days, 90)
        self.assertEqual(female_donor.cooldown_days, 120)
