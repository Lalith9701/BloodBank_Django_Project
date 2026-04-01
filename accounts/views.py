from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
import csv
import logging
import re

from inventory.models import BloodGroup
from donors.models import Donor
from notifications.models import Notification
from .models import SecurityProfile, SECURITY_QUESTIONS

User = get_user_model()
logger = logging.getLogger('accounts')

# Brute-force lockout: 3 wrong answers → 15-minute lockout
SQ_MAX_ATTEMPTS = 3
SQ_LOCKOUT_MINS = 15


def validate_strong_password(password: str) -> list[str]:
    """
    Returns a list of error strings. Empty list = valid.
    Only used during registration — does NOT affect login or reset flows.
    """
    errors = []
    if len(password) < 8:
        errors.append("Be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Contain at least one uppercase letter (A–Z).")
    if not re.search(r'[a-z]', password):
        errors.append("Contain at least one lowercase letter (a–z).")
    if not re.search(r'\d', password):
        errors.append("Contain at least one digit (0–9).")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\;\'`~/]', password):
        errors.append("Contain at least one special character (!@#$%^&* etc.).")
    return errors


# ============================================================
# LOGIN
# ============================================================
def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        user = authenticate(request, username=login_id, password=password)

        if not user:
            normalized = ' '.join(login_id.split())
            name_parts = normalized.split(' ', 1)
            first_name = name_parts[0]
            last_name  = name_parts[1] if len(name_parts) > 1 else ''

            qs = (User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name)
                  if last_name else
                  User.objects.filter(first_name__iexact=first_name))

            for p_user in qs:
                authed = authenticate(request, username=p_user.username, password=password)
                if authed:
                    user = authed
                    break

        if user:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')

        return render(request, 'login.html', {
            'error': 'Invalid credentials. Try your phone number or full name.'
        })

    return render(request, 'login.html')


# ============================================================
# REGISTER
# ============================================================
def register(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        full_name         = request.POST.get('full_name', '').strip()
        name_parts        = full_name.split(' ', 1)
        first_name        = name_parts[0].strip()
        last_name         = name_parts[1].strip() if len(name_parts) > 1 else ''
        email             = request.POST.get('email', '').strip().lower()
        password          = request.POST.get('password', '')
        confirm_password  = request.POST.get('confirm_password', '')
        phone             = request.POST.get('phone', '').strip()
        blood_group_id    = request.POST.get('blood_group')
        age               = request.POST.get('age')
        gender            = request.POST.get('gender')
        weight            = request.POST.get('weight')
        health_issue      = request.POST.get('health_issue')
        health_issue_desc = request.POST.get('health_issue_description', '')
        address           = request.POST.get('address')
        pincode           = request.POST.get('pincode')
        city              = request.POST.get('city')
        state             = request.POST.get('state')
        nation            = request.POST.get('nation')
        question_key      = request.POST.get('security_question')
        sq_answer         = request.POST.get('security_answer', '').strip()

        field_errors = {}

        if not phone:
            field_errors['phone'] = 'Mobile number is required.'
        elif not phone.isdigit() or len(phone) < 10:
            field_errors['phone'] = 'Enter a valid 10-digit mobile number.'
        elif User.objects.filter(username=phone).exists():
            field_errors['phone'] = 'This mobile number is already registered.'

        if not email:
            field_errors['email'] = 'Email address is required.'
        elif User.objects.filter(email__iexact=email).exists():
            field_errors['email'] = 'This email is already registered.'

        if first_name and User.objects.filter(
            first_name__iexact=first_name,
            last_name__iexact=last_name
        ).exists():
            field_errors['full_name'] = 'A user with this full name already exists.'

        pw_errors = validate_strong_password(password)
        if pw_errors:
            field_errors['password'] = pw_errors

        if password and confirm_password and password != confirm_password:
            field_errors['confirm_password'] = 'Passwords do not match.'

        if not question_key or question_key not in dict(SECURITY_QUESTIONS):
            field_errors['security_question'] = 'Please select a valid security question.'
        if not sq_answer:
            field_errors['security_answer'] = 'Security answer is required.'

        if field_errors:
            return render(request, 'register.html', {
                'blood_groups': blood_groups,
                'security_questions': SECURITY_QUESTIONS,
                'field_errors': field_errors,
                'form_data': request.POST,
            })

        has_health_issue = (health_issue == "True")
        eligibility      = 'PENDING' if has_health_issue else 'ELIGIBLE'

        user = User.objects.create_user(
            username=phone, password=password,
            first_name=first_name, last_name=last_name,
            email=email, role='DONOR'
        )

        Donor.objects.create(
            user=user, phone=phone, blood_group_id=blood_group_id,
            age=age, gender=gender, weight=weight,
            health_issue=has_health_issue,
            health_issue_description=health_issue_desc,
            eligibility_status=eligibility,
            address=address, pincode=pincode,
            city=city, state=state, nation=nation
        )

        sp = SecurityProfile(user=user, question_key=question_key)
        sp.set_answer(sq_answer)
        sp.save()

        logger.info(f"New donor registered: {phone}")
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')

    return render(request, 'register.html', {
        'blood_groups': blood_groups,
        'security_questions': SECURITY_QUESTIONS,
        'field_errors': {},
        'form_data': {},
    })


# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard(request):
    user = request.user
    if user.role == 'ADMIN':
        return render(request, 'admin_dashboard.html')
    elif user.role == 'DONOR':
        return render(request, 'donor_dashboard.html')
    elif user.role == 'REQUESTER':
        return render(request, 'requester_dashboard.html')
    return redirect('login')


# ============================================================
# LOGOUT
# ============================================================
def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


# ============================================================
# FORGOT PASSWORD — Step 1: Enter phone / email
# ============================================================
def sq_lookup(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()

        user = (User.objects.filter(username=identifier).first() or
                User.objects.filter(email__iexact=identifier).first())

        if not user:
            logger.warning(f"Security question lookup for unknown identifier: {identifier}")
            return render(request, 'sq_lookup.html', {
                'error': 'No account found with that phone number or email.'
            })

        try:
            sp = user.security_profile
        except SecurityProfile.DoesNotExist:
            return render(request, 'sq_lookup.html', {
                'error': 'This account has no security question set. Please contact support.'
            })

        if sp.locked_until and timezone.now() < sp.locked_until:
            remaining = int((sp.locked_until - timezone.now()).total_seconds() // 60) + 1
            return render(request, 'sq_lookup.html', {
                'error': f'Account temporarily locked. Try again in {remaining} minute(s).'
            })

        request.session['sq_username'] = user.username
        logger.info(f"Security question lookup for: {user.username}")
        return redirect('sq_answer')

    return render(request, 'sq_lookup.html')


# ============================================================
# FORGOT PASSWORD — Step 2: Answer the security question
# ============================================================
def sq_answer(request):
    username = request.session.get('sq_username')
    if not username:
        return redirect('sq_lookup')

    try:
        user = User.objects.get(username=username)
        sp   = user.security_profile
    except (User.DoesNotExist, SecurityProfile.DoesNotExist):
        return redirect('sq_lookup')

    if sp.locked_until and timezone.now() < sp.locked_until:
        remaining = int((sp.locked_until - timezone.now()).total_seconds() // 60) + 1
        del request.session['sq_username']
        return render(request, 'sq_lookup.html', {
            'error': f'Too many wrong answers. Try again in {remaining} minute(s).'
        })

    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip()

        if sp.check_answer(answer):
            sp.reset_attempts = 0
            sp.locked_until   = None
            sp.save()
            request.session['sq_verified'] = username
            del request.session['sq_username']
            logger.info(f"Security question answered correctly for: {username}")
            return redirect('sq_reset_password')
        else:
            sp.reset_attempts += 1
            remaining = SQ_MAX_ATTEMPTS - sp.reset_attempts
            logger.warning(f"Wrong security answer for: {username} | attempts: {sp.reset_attempts}")

            if sp.reset_attempts >= SQ_MAX_ATTEMPTS:
                sp.locked_until   = timezone.now() + timezone.timedelta(minutes=SQ_LOCKOUT_MINS)
                sp.reset_attempts = 0
                sp.save()
                del request.session['sq_username']
                return render(request, 'sq_lookup.html', {
                    'error': f'Too many wrong answers. Account locked for {SQ_LOCKOUT_MINS} minutes.'
                })

            sp.save()
            return render(request, 'sq_answer.html', {
                'question': sp.question_text,
                'error': f'Incorrect answer. {remaining} attempt(s) remaining.',
            })

    return render(request, 'sq_answer.html', {'question': sp.question_text})


# ============================================================
# FORGOT PASSWORD — Step 3: Set new password
# ============================================================
def sq_reset_password(request):
    username = request.session.get('sq_verified')
    if not username:
        return redirect('sq_lookup')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')

        if p1 != p2:
            return render(request, 'sq_reset_password.html', {'error': 'Passwords do not match.'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            del request.session['sq_verified']
            return redirect('sq_lookup')

        try:
            validate_password(p1, user)
        except ValidationError as e:
            return render(request, 'sq_reset_password.html', {'error': ' '.join(e.messages)})

        user.set_password(p1)
        user.save()
        del request.session['sq_verified']
        logger.info(f"Password reset via security question for: {username}")
        messages.success(request, 'Password updated successfully. Please log in.')
        return redirect('login')

    return render(request, 'sq_reset_password.html')


# ============================================================
# ADMIN HEALTH APPROVALS
# ============================================================
@login_required
def admin_health_approvals(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        action   = request.POST.get('action')
        donor_id = request.POST.get('donor_id')
        try:
            donor = Donor.objects.get(id=donor_id)
            if action == 'approve':
                donor.eligibility_status = 'ELIGIBLE'
                donor.save()
                Notification.objects.create(
                    user=donor.user, title='Health Status Approved',
                    message='Your health eligibility has been approved. You can now donate blood.',
                    notif_type='success'
                )
            elif action == 'reject':
                donor.eligibility_status = 'REJECTED'
                donor.save()
                Notification.objects.create(
                    user=donor.user, title='Health Status Rejected',
                    message='Your health eligibility has been rejected by the admin.',
                    notif_type='danger'
                )
        except Donor.DoesNotExist:
            pass
        return redirect('admin_health_approvals')

    pending_donors = Donor.objects.filter(eligibility_status='PENDING').order_by('-id')
    return render(request, 'admin_health_approvals.html', {'pending_donors': pending_donors})


# ============================================================
# ADMIN ALL DONORS
# ============================================================
@login_required
def admin_all_donors(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    query = request.GET.get('q', '')
    qs = Donor.objects.filter(
        Q(user__username__icontains=query) |
        Q(phone__icontains=query) |
        Q(blood_group__blood_group__icontains=query) |
        Q(eligibility_status__icontains=query)
    ).order_by('-id') if query else Donor.objects.all().order_by('-id')

    return render(request, 'admin_all_donors.html', {'donors': qs, 'query': query})


# ============================================================
# EXPORT DONORS CSV
# ============================================================
@login_required
def export_donors_csv(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="donors.csv"'
    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Phone', 'Email', 'Blood Group', 'City', 'Status'])
    for d in Donor.objects.all().select_related('user', 'blood_group'):
        writer.writerow([
            f"{d.user.first_name} {d.user.last_name}",
            d.phone, d.user.email,
            d.blood_group.blood_group, d.city, d.eligibility_status
        ])
    return response


# ============================================================
# USER PROFILE
# ============================================================
@login_required
def profile(request):
    user  = request.user
    donor = None
    if user.role == 'DONOR':
        try:
            donor = Donor.objects.get(user=user)
        except Donor.DoesNotExist:
            pass

    if request.method == 'POST':
        full_name  = request.POST.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name  = name_parts[1] if len(name_parts) > 1 else ''
        user.email = request.POST.get('email')
        user.save()

        if donor:
            donor.address = request.POST.get('address')
            donor.city    = request.POST.get('city')
            donor.pincode = request.POST.get('pincode')
            donor.state   = request.POST.get('state')
            donor.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {'donor': donor})
