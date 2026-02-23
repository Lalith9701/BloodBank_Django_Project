from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from inventory.models import BloodGroup, BloodStock
from donors.models import Donor
from .models import Donation, BloodRequest


# ===================================
# ADD DONATION
# ===================================
@login_required
def add_donation(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        blood_group_id = request.POST.get('blood_group')
        units = request.POST.get('units')

        if not blood_group_id or not units:
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups,
                'error': 'Please fill all fields'
            })

        donor = Donor.objects.get(user=request.user)

        Donation.objects.create(
            donor=donor,
            blood_group_id=int(blood_group_id),
            units=int(units)
        )

        return redirect('my_donations')

    return render(request, 'add_donation.html', {
        'blood_groups': blood_groups
    })


# ===================================
# MY DONATIONS
# ===================================
@login_required
def my_donations(request):
    donor = Donor.objects.get(user=request.user)
    donations = Donation.objects.filter(donor=donor)

    return render(request, 'my_donations.html', {
        'donations': donations
    })


# ===================================
# REQUEST BLOOD
# ===================================
@login_required
def request_blood(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        blood_group_id = request.POST.get('blood_group')
        units_required = request.POST.get('units_required')

        if not blood_group_id or not units_required:
            return render(request, 'request_blood.html', {
                'blood_groups': blood_groups,
                'error': 'Please fill all fields'
            })

        BloodRequest.objects.create(
            user=request.user,
            blood_group_id=int(blood_group_id),
            units_required=int(units_required)
        )

        return redirect('dashboard')

    return render(request, 'request_blood.html', {
        'blood_groups': blood_groups
    })


# ===================================
# MY REQUESTS
# ===================================
@login_required
def my_requests(request):
    requests = BloodRequest.objects.filter(user=request.user).order_by('-request_date')

    return render(request, 'my_requests.html', {
        'requests': requests
    })
@login_required
def admin_requests(request):
    return render(request, 'admin_requests.html')