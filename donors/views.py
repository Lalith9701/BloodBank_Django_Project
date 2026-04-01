from django.shortcuts import render
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
