from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Donor
from inventory.models import BloodGroup

def donor_search(request):
    blood_groups = BloodGroup.objects.all()
    blood_group_id = request.GET.get('blood_group')
    city = request.GET.get('city')
    pincode = request.GET.get('pincode')

    donors = Donor.objects.filter(availability=True, eligibility_status='ELIGIBLE')

    if blood_group_id:
        donors = donors.filter(blood_group_id=blood_group_id)
    if city:
        donors = donors.filter(city__icontains=city)
    if pincode:
        donors = donors.filter(pincode__icontains=pincode)

    return render(request, 'donor_search.html', {
        'donors': donors,
        'blood_groups': blood_groups,
        'query': {
            'blood_group': blood_group_id,
            'city': city,
            'pincode': pincode
        }
    })


@login_required
def donor_rewards(request):
    if request.user.role != 'DONOR':
        messages.info(request, "The LIFE DROP Reward System is designed for registered blood donors.")
        return redirect('dashboard')

    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found.")
        return redirect('dashboard')

    donations = list(donor.donation_set.order_by('-donation_date'))
    reward_info = donor.reward_info
    achievements = donor.achievements

    return render(request, 'donor_rewards.html', {
        'donor': donor,
        'reward_info': reward_info,
        'achievements': achievements,
        'donations': donations,
    })


@login_required
def donor_family_certificate(request):
    if request.user.role != 'DONOR':
        return redirect('dashboard')

    try:
        donor = Donor.objects.get(user=request.user)
    except Donor.DoesNotExist:
        messages.error(request, "Donor profile not found.")
        return redirect('dashboard')

    return render(request, 'family_certificate.html', {
        'donor': donor,
        'reward_info': donor.reward_info,
    })

