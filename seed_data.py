import os
import sys
import random
from datetime import timedelta

# Set utf-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloodbank.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from inventory.models import BloodGroup, BloodStock
from donors.models import Donor
from requests_app.models import BloodRequest, Donation
from notifications.models import Notification
from ratings.models import Rating
from agents.models import AgentExecutionLog
from agents.services.emergency_agent import run_emergency_dispatch_agent

User = get_user_model()

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
    "Shaurya", "Rudra", "Ananya", "Diya", "Pari", "Saanvi", "Riya", "Aadhya", "Avani", "Kiara",
    "Myra", "Ira", "Rohan", "Rahul", "Priya", "Neha", "Amit", "Pooja", "Vikas", "Sunita",
    "Rajesh", "Suresh", "Kavita", "Deepak", "Anita", "Manoj", "Meena", "Sanjay", "Rekha", "Ramesh",
    "Lakshmi", "Ganesh", "Venkat", "Swati", "Karthik", "Divya", "Prashanth", "Ramya", "Siddharth", "Bhavana"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Reddy", "Rao", "Nair", "Iyer", "Kumar", "Singh",
    "Joshi", "Kulkarni", "Deshmukh", "Chaudhary", "Mehta", "Shah", "Agarwal", "Bhat", "Shenoy", "Pillai",
    "Hegde", "Mishra", "Pandey", "Tripathi", "Shukla", "Yadav", "Gowda", "Naidu", "Prasad", "Das"
]

CITIES = [
    ("Hyderabad", "Telangana"),
    ("Bengaluru", "Karnataka"),
    ("Chennai", "Tamil Nadu"),
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh")
]

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

def run_seeder():
    print("Starting Data Seeder for Blood Bank Management System...")
    
    # Pre-hash common password once for fast batch creation
    hashed_password = make_password("password123")

    # 1. Ensure Blood Groups exist
    bg_objects = {}
    for bg_str in BLOOD_GROUPS:
        bg_obj, _ = BloodGroup.objects.get_or_create(blood_group=bg_str)
        bg_objects[bg_str] = bg_obj
        stock_obj, created = BloodStock.objects.get_or_create(blood_group=bg_obj)
        if created or stock_obj.units_available < 10:
            stock_obj.units_available = random.randint(15, 60)
            stock_obj.save()

    print("Blood Groups & Initial Stock verified.")

    users_created = 0
    donors_created = 0
    donations_created = 0
    requests_created = 0
    notifications_created = 0

    existing_phones = set(User.objects.values_list('username', flat=True))
    existing_emails = set(User.objects.values_list('email', flat=True))

    def generate_phone():
        while True:
            p = f"{random.randint(6000000000, 9999999999)}"
            if p not in existing_phones:
                existing_phones.add(p)
                return p

    def generate_email(first, last, idx):
        while True:
            e = f"{first.lower()}.{last.lower()}{idx}{random.randint(100, 999)}@example.com"
            if e not in existing_emails:
                existing_emails.add(e)
                return e

    # 2. Seed 160 Donors
    print("Creating 160 Donor accounts & profiles...")
    donor_list = []
    for i in range(1, 161):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        phone = generate_phone()
        email = generate_email(first, last, i)
        username = f"donor_{phone}"

        user = User.objects.create(
            username=username,
            first_name=first,
            last_name=last,
            email=email,
            password=hashed_password,
            role="DONOR"
        )
        users_created += 1

        city, state = random.choice(CITIES)
        bg_choice = random.choice(BLOOD_GROUPS)

        eligibility = random.choices(
            ['ELIGIBLE', 'PENDING', 'REJECTED'],
            weights=[85, 10, 5],
            k=1
        )[0]

        donor = Donor.objects.create(
            user=user,
            blood_group=bg_objects[bg_choice],
            phone=phone,
            age=random.randint(18, 55),
            gender=random.choice(['Male', 'Female']),
            weight=round(random.uniform(52.0, 95.0), 1),
            health_issue=(eligibility != 'ELIGIBLE'),
            health_issue_description="Minor seasonal allergies" if eligibility != 'ELIGIBLE' else "",
            eligibility_status=eligibility,
            availability=random.choice([True, True, True, False]),
            address=f"Flat #{random.randint(101, 999)}, Road #{random.randint(1, 25)}",
            pincode=f"{random.randint(500001, 500099)}",
            city=city,
            state=state,
            nation="India"
        )
        donor_list.append(donor)
        donors_created += 1

    print("160 Donors created successfully.")

    # 3. Seed 40 Requesters
    print("Creating 40 Requester accounts...")
    requester_users = []
    for i in range(1, 41):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        phone = generate_phone()
        email = generate_email(first, last, i + 500)
        username = f"requester_{phone}"

        user = User.objects.create(
            username=username,
            first_name=first,
            last_name=last,
            email=email,
            password=hashed_password,
            role="REQUESTER"
        )
        users_created += 1
        requester_users.append(user)

    print("40 Requesters created successfully.")

    # 4. Create Historical Donations (~60 records)
    print("Generating 60 historical Donation records...")
    now = timezone.now()
    eligible_donors = [d for d in donor_list if d.eligibility_status == 'ELIGIBLE']
    
    for _ in range(60):
        d = random.choice(eligible_donors)
        days_ago = random.randint(5, 180)
        donation_time = now - timedelta(days=days_ago)
        units = random.choice([1, 1, 2])

        don = Donation.objects.create(
            donor=d,
            blood_group=d.blood_group,
            units=units
        )
        don.donation_date = donation_time
        don.save(update_fields=['donation_date'])
        donations_created += 1

    print("60 Donations created.")

    # 5. Create Blood Requests (~50 records) with Urgency & Statuses
    print("Generating 50 Blood Request records...")
    urgencies = ['NORMAL', 'URGENT', 'EMERGENCY']
    statuses = ['APPROVED', 'PENDING', 'REJECTED']

    for i in range(50):
        req_user = random.choice(requester_users)
        bg = bg_objects[random.choice(BLOOD_GROUPS)]
        urgency = random.choice(urgencies)
        status = random.choices(statuses, weights=[60, 25, 15], k=1)[0]
        units = random.randint(1, 4)

        days_ago = random.randint(0, 45)
        req_time = now - timedelta(days=days_ago)

        blood_req = BloodRequest.objects.create(
            user=req_user,
            blood_group=bg,
            units_required=units,
            urgency=urgency,
            status=status,
            rejection_reason="Inventory stock deficit" if status == 'REJECTED' else ""
        )
        blood_req.request_date = req_time
        blood_req.save(update_fields=['request_date'])
        requests_created += 1

        if urgency in ['EMERGENCY', 'URGENT']:
            try:
                run_emergency_dispatch_agent(blood_req.id, trigger_type='AUTOMATIC')
            except Exception:
                pass

        if status == 'APPROVED' and random.choice([True, False]):
            try:
                Rating.objects.create(
                    blood_request=blood_req,
                    rater=req_user,
                    donor_rating=random.randint(4, 5),
                    service_rating=random.randint(4, 5),
                    feedback="Prompt service and polite blood bank staff. Very satisfied!"
                )
            except Exception:
                pass

    print("50 Blood Requests created.")

    # 6. Generate Notifications (~50 records)
    print("Creating Notifications...")
    all_users = list(User.objects.all())
    for _ in range(50):
        u = random.choice(all_users)
        notif_type = random.choice(['info', 'success', 'warning', 'danger'])
        title_map = {
            'info': 'System Update',
            'success': 'Blood Request Approved',
            'warning': 'Urgent Blood Shortage Alert',
            'danger': 'Emergency Match Dispatch'
        }
        Notification.objects.create(
            user=u,
            title=title_map[notif_type],
            message=f"System notification regarding account activities and blood bank dispatches.",
            notif_type=notif_type,
            is_read=random.choice([True, False])
        )
        notifications_created += 1

    print("\n------------------------------------------")
    print(f"SEEDING SUCCESSFUL!")
    print(f" • Total Users Created:         {users_created}")
    print(f" • Total Donors Created:        {donors_created}")
    print(f" • Total Requesters Created:    {len(requester_users)}")
    print(f" • Total Donations Recorded:   {donations_created}")
    print(f" • Total Blood Requests:       {requests_created}")
    print(f" • Total Notifications Sent:   {notifications_created}")
    print(f" • AI Agent Execution Logs:     {AgentExecutionLog.objects.count()}")
    print(f"------------------------------------------")

if __name__ == '__main__':
    run_seeder()
