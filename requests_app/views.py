from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from inventory.models import BloodGroup
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
            units_required=int(units_required),
            status='PENDING'   # ✅ MUST MATCH MODEL
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
    requests = BloodRequest.objects.filter(
        user=request.user
    ).order_by('-request_date')

    return render(request, 'my_requests.html', {
        'requests': requests
    })


# ===================================
# ADMIN REQUESTS (Approve / Reject)
# ===================================
@login_required
def admin_requests(request):

    # Allow only admin/staff
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == "POST":
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")

        blood_request = get_object_or_404(BloodRequest, id=request_id)

        if action == "approve":
            blood_request.status = "APPROVED"
            blood_request.save()

        elif action == "reject":
            blood_request.status = "REJECTED"
            blood_request.save()

        return redirect('admin_requests')

    requests = BloodRequest.objects.all().order_by('-request_date')

    return render(request, 'admin_requests.html', {
        'requests': requests
    })