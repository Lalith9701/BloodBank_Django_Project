from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import BloodGroup, BloodStock

@login_required
def blood_stock(request):
    stocks = BloodStock.objects.select_related('blood_group').all()
    return render(request, 'blood_stock.html', {'stocks': stocks})


@login_required
def add_blood_group(request):
    if request.method == 'POST':
        group = request.POST.get('blood_group')
        if group:
            BloodGroup.objects.get_or_create(blood_group=group)
        return redirect('blood_stock')

    return render(request, 'add_blood_group.html')


@login_required
def add_blood_stock(request):
    if request.method == 'POST':
        group_id = request.POST.get('blood_group')
        units = request.POST.get('units')

        blood_group = BloodGroup.objects.get(id=group_id)
        stock, created = BloodStock.objects.get_or_create(
            blood_group=blood_group,
            defaults={'units_available': units}
        )

        if not created:
            stock.units_available += int(units)
            stock.save()

        return redirect('blood_stock')

    groups = BloodGroup.objects.all()
    return render(request, 'add_blood_stock.html', {'groups': groups})
