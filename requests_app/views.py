from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
import csv

from inventory.models import BloodGroup
from donors.models import Donor
from notifications.models import Notification
from .models import Donation, BloodRequest


# ===================================
# ADD DONATION
# ===================================
@login_required
def add_donation(request):
    if request.user.role != 'DONOR':
        return redirect('dashboard')

    blood_groups = BloodGroup.objects.all()
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        units = request.POST.get('units')

        if not units:
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'error': 'Please enter the number of units.'
            })

        if donor.eligibility_status == 'PENDING':
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'error': 'Your donation cannot be processed. Your health status requires Admin approval.'
            })
        elif donor.eligibility_status == 'REJECTED':
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'error': 'Your donation cannot be processed because your health status was rejected by an Admin.'
            })

        # 90-day cooldown check
        last_donation = Donation.objects.filter(donor=donor).order_by('-donation_date').first()
        if last_donation:
            days_since = (timezone.now() - last_donation.donation_date).days
            if days_since < 90:
                return render(request, 'add_donation.html', {
                    'blood_groups': blood_groups, 'donor': donor,
                    'error': (
                        f'You must wait 90 days between donations. '
                        f'Your last donation was {days_since} days ago. '
                        f'Please wait {90 - days_since} more days.'
                    )
                })

        Donation.objects.create(
            donor=donor,
            blood_group=donor.blood_group,
            units=int(units)
        )

        donor.availability = False
        donor.save()

        Notification.objects.create(
            user=request.user,
            title="Donation Recorded",
            message=(
                f"Thank you! Your donation of {units} units has been recorded. "
                f"Your availability has been set to Offline for recovery."
            ),
            notif_type="success"
        )

        return redirect('my_donations')

    return render(request, 'add_donation.html', {
        'blood_groups': blood_groups,
        'donor': donor
    })


# ===================================
# MY DONATIONS
# ===================================
@login_required
def my_donations(request):
    if request.user.role != 'DONOR':
        return redirect('dashboard')
    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found.")
        return redirect('dashboard')

    donations = Donation.objects.filter(donor=donor)
    return render(request, 'my_donations.html', {'donations': donations})


# ===================================
# REQUEST BLOOD
# ===================================
@login_required
def request_blood(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        blood_group_id = request.POST.get('blood_group')
        units_required = request.POST.get('units_required')
        urgency        = request.POST.get('urgency', 'NORMAL')

        if not blood_group_id or not units_required:
            return render(request, 'request_blood.html', {
                'blood_groups': blood_groups,
                'error': 'Please fill all fields.'
            })

        BloodRequest.objects.create(
            user=request.user,
            blood_group_id=int(blood_group_id),
            units_required=int(units_required),
            urgency=urgency,
            status='PENDING'
        )
        return redirect('dashboard')

    return render(request, 'request_blood.html', {'blood_groups': blood_groups})


# ===================================
# MY REQUESTS
# ===================================
@login_required
def my_requests(request):
    reqs = BloodRequest.objects.filter(user=request.user).order_by('-request_date')
    return render(request, 'my_requests.html', {'requests': reqs})


# ===================================
# ADMIN REQUESTS (Approve / Reject)
# ===================================
@login_required
def admin_requests(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        action     = request.POST.get('action')
        request_id = request.POST.get('request_id')
        blood_request = get_object_or_404(BloodRequest, id=request_id)

        if action == 'approve':
            blood_request.status = 'APPROVED'
            blood_request.save()
            Notification.objects.create(
                user=blood_request.user,
                title="Blood Request Approved",
                message=(
                    f"Your request for {blood_request.units_required} units of "
                    f"{blood_request.blood_group} has been approved."
                ),
                notif_type="success"
            )

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            blood_request.status = 'REJECTED'
            blood_request.rejection_reason = reason
            blood_request.save()
            Notification.objects.create(
                user=blood_request.user,
                title="Blood Request Rejected",
                message=(
                    f"Your request for {blood_request.units_required} units of "
                    f"{blood_request.blood_group} was rejected. Reason: {reason}"
                ),
                notif_type="danger"
            )

        return redirect('admin_requests')

    reqs = BloodRequest.objects.all().order_by('-request_date')
    return render(request, 'admin_requests.html', {'requests': reqs})


# ===================================
# EXPORT REQUESTS CSV
# ===================================
@login_required
def export_requests_csv(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="blood_requests.csv"'
    writer = csv.writer(response)
    writer.writerow(['Requester', 'Blood Group', 'Units', 'Urgency', 'Status', 'Date'])

    for req in BloodRequest.objects.all().select_related('user', 'blood_group').order_by('-request_date'):
        writer.writerow([
            req.user.username,
            req.blood_group.blood_group,
            req.units_required,
            req.urgency,
            req.status,
            req.request_date.strftime("%Y-%m-%d %H:%M")
        ])
    return response
