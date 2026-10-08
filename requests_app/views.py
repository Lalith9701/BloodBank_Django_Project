from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
import csv

from datetime import datetime, timedelta
from inventory.models import BloodGroup, BloodStock
from donors.models import Donor
from notifications.models import Notification
from accounts.models import AuditLog
from agents.services.emergency_agent import run_emergency_dispatch_agent
from .models import Donation, BloodRequest, DonationAppointment


# ===================================
# ADD DONATION / SCHEDULE APPOINTMENT
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

    # Calculate cool-down metrics
    cooldown_days = donor.cooldown_days
    last_donation = Donation.objects.filter(donor=donor).order_by('-donation_date').first()
    today = timezone.now().date()

    if last_donation:
        days_since_last = (today - last_donation.donation_date.date()).days
        next_eligible_date = last_donation.donation_date.date() + timedelta(days=cooldown_days)
    else:
        days_since_last = None
        next_eligible_date = today

    is_cooling = next_eligible_date > today
    days_remaining = (next_eligible_date - today).days if is_cooling else 0
    next_eligible_date_iso = next_eligible_date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        units = request.POST.get('units')
        scheduled_date_str = request.POST.get('scheduled_date')
        time_slot = request.POST.get('time_slot', '09:00 AM - 11:00 AM')

        if not units:
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'last_donation': last_donation, 'cooldown_days': cooldown_days,
                'next_eligible_date': next_eligible_date,
                'next_eligible_date_iso': next_eligible_date_iso,
                'days_remaining': days_remaining, 'days_since_last': days_since_last,
                'is_cooling': is_cooling,
                'error': 'Please enter the number of units.'
            })

        if donor.eligibility_status == 'PENDING':
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'last_donation': last_donation, 'cooldown_days': cooldown_days,
                'next_eligible_date': next_eligible_date,
                'next_eligible_date_iso': next_eligible_date_iso,
                'days_remaining': days_remaining, 'days_since_last': days_since_last,
                'is_cooling': is_cooling,
                'error': 'Your donation cannot be processed. Your health status requires Admin approval.'
            })
        elif donor.eligibility_status == 'REJECTED':
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'last_donation': last_donation, 'cooldown_days': cooldown_days,
                'next_eligible_date': next_eligible_date,
                'next_eligible_date_iso': next_eligible_date_iso,
                'days_remaining': days_remaining, 'days_since_last': days_since_last,
                'is_cooling': is_cooling,
                'error': 'Your donation cannot be processed because your health status was rejected by an Admin.'
            })

        # Validate scheduled date against cool-down policy
        if scheduled_date_str:
            try:
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
            except ValueError:
                scheduled_date = next_eligible_date
        else:
            scheduled_date = next_eligible_date

        if scheduled_date < next_eligible_date:
            return render(request, 'add_donation.html', {
                'blood_groups': blood_groups, 'donor': donor,
                'last_donation': last_donation, 'cooldown_days': cooldown_days,
                'next_eligible_date': next_eligible_date,
                'next_eligible_date_iso': next_eligible_date_iso,
                'days_remaining': days_remaining, 'days_since_last': days_since_last,
                'is_cooling': is_cooling,
                'error': (
                    f'Invalid Appointment Date: Your medical cool-down period requires you to wait until '
                    f'{next_eligible_date.strftime("%B %d, %Y")} before your next donation.'
                )
            })

        units_int = int(units)

        if scheduled_date <= today:
            # Direct donation today
            Donation.objects.create(
                donor=donor,
                blood_group=donor.blood_group,
                units=units_int
            )

            points_earned = units_int * 100
            donor.life_points += points_earned
            donor.availability = False
            donor.save()

            r_info = donor.reward_info

            Notification.objects.create(
                user=request.user,
                title="🩸 Donation Recorded & LIFE Points Earned!",
                message=(
                    f"Thank you! Your donation of {units_int} unit(s) has been recorded. "
                    f"You earned +{points_earned} LIFE Points! "
                    f"Your total balance is {r_info['points']} Points (Level: {r_info['level_name']})."
                ),
                notif_type="success"
            )

            messages.success(
                request,
                f"Thank you for donating blood! You earned +{points_earned} LIFE Points! Level: {r_info['level_name']}"
            )
            return redirect('my_donations')
        else:
            # Future appointment scheduled
            appointment = DonationAppointment.objects.create(
                donor=donor,
                blood_group=donor.blood_group,
                units=units_int,
                scheduled_date=scheduled_date,
                time_slot=time_slot,
                status='SCHEDULED'
            )

            Notification.objects.create(
                user=request.user,
                title="📅 Donation Appointment Scheduled!",
                message=(
                    f"Your donation appointment is confirmed for {scheduled_date.strftime('%B %d, %Y')} "
                    f"({time_slot}). Thank you for planning ahead!"
                ),
                notif_type="info"
            )

            messages.success(
                request,
                f"🎉 Donation appointment successfully scheduled for {scheduled_date.strftime('%B %d, %Y')} ({time_slot})!"
            )
            return redirect('my_donations')

    return render(request, 'add_donation.html', {
        'blood_groups': blood_groups,
        'donor': donor,
        'last_donation': last_donation,
        'cooldown_days': cooldown_days,
        'next_eligible_date': next_eligible_date,
        'next_eligible_date_iso': next_eligible_date_iso,
        'days_remaining': days_remaining,
        'days_since_last': days_since_last,
        'is_cooling': is_cooling,
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

    donations = Donation.objects.filter(donor=donor).order_by('-donation_date')
    appointments = DonationAppointment.objects.filter(donor=donor, status='SCHEDULED').order_by('scheduled_date')

    return render(request, 'my_donations.html', {
        'donor': donor,
        'donations': donations,
        'appointments': appointments
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
        urgency        = request.POST.get('urgency', 'NORMAL')

        purpose = request.POST.get('purpose', '').strip()
        patient_name = request.POST.get('patient_name', '').strip()
        patient_phone = request.POST.get('patient_phone', '').strip()
        patient_gender = request.POST.get('patient_gender', '').strip()
        patient_address = request.POST.get('patient_address', '').strip()
        prescription_doc = request.FILES.get('prescription_document')

        if not blood_group_id or not units_required:
            return render(request, 'request_blood.html', {
                'blood_groups': blood_groups,
                'error': 'Please fill all required fields.'
            })

        blood_req = BloodRequest.objects.create(
            user=request.user,
            blood_group_id=int(blood_group_id),
            units_required=int(units_required),
            urgency=urgency,
            purpose=purpose,
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_gender=patient_gender,
            patient_address=patient_address,
            prescription_document=prescription_doc,
            status='PENDING'
        )

        # Automatically trigger AI Agent for all request types (NORMAL, URGENT, EMERGENCY)
        # The agent will automatically approve the request if stock is available without needing admin intervention.
        try:
            run_emergency_dispatch_agent(blood_req.id, trigger_type='AUTOMATIC')
        except Exception:
            pass

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
            AuditLog.objects.create(
                actor=request.user,
                action='Blood Request Approved',
                target=f'Request by: {blood_request.user.get_full_name() or blood_request.user.username}',
                detail=f'{blood_request.units_required} units of {blood_request.blood_group}'
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
            AuditLog.objects.create(
                actor=request.user,
                action='Blood Request Rejected',
                target=f'Request by: {blood_request.user.get_full_name() or blood_request.user.username}',
                detail=f'{blood_request.units_required} units of {blood_request.blood_group}. Reason: {reason}'
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


# ===================================
# TOGGLE DONOR AVAILABILITY
# ===================================
@login_required
def toggle_availability(request):
    if request.user.role != 'DONOR':
        return redirect('dashboard')
    if request.method == 'POST':
        try:
            donor = Donor.objects.get(user=request.user)
            donor.availability = not donor.availability
            donor.save()
            status = 'Available' if donor.availability else 'Unavailable'
            messages.success(request, f'Your availability has been set to {status}.')
            Notification.objects.create(
                user=request.user,
                title=f'Availability Updated',
                message=f'You have set your donor availability to {status}.',
                notif_type='success' if donor.availability else 'info'
            )
        except Donor.DoesNotExist:
            messages.error(request, 'Donor profile not found.')
    return redirect('dashboard')
