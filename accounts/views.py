from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from inventory.models import BloodGroup
from donors.models import Donor

User = get_user_model()


# --------------------
# LOGIN VIEW
# --------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'login.html')


# --------------------
# REGISTER VIEW
# --------------------
def register(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        blood_group_id = request.POST.get('blood_group')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        weight = request.POST.get('weight')
        health_issue = request.POST.get('health_issue')

        user = User.objects.create_user(
            username=username,
            password=password,
            role='DONOR'
        )

        Donor.objects.create(
            user=user,
            phone=phone,
            blood_group_id=blood_group_id,
            age=age,
            gender=gender,
            weight=weight,
            health_issue=True if health_issue == "True" else False
        )

        return redirect('login')

    return render(request, 'register.html', {
        'blood_groups': blood_groups
    })


# --------------------
# DASHBOARD VIEW
# --------------------
@login_required
def dashboard(request):
    user = request.user

    if user.role == 'ADMIN':
        return render(request, 'admin_dashboard.html')

    elif user.role == 'DONOR':
        return render(request, 'donor_dashboard.html')

    elif user.role == 'REQUESTER':
        return render(request, 'requester_dashboard.html')

    else:
        return redirect('login')


# --------------------
# LOGOUT VIEW
# --------------------
def logout_view(request):
    logout(request)
    return redirect('login')
