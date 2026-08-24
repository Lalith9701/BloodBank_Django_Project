from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token
import csv
import logging
import re

from inventory.models import BloodGroup, BloodStock
from donors.models import Donor
from notifications.models import Notification
from requests_app.models import BloodRequest, Donation
from .models import SecurityProfile, SECURITY_QUESTIONS, AuditLog, ContactAdminMessage

User = get_user_model()
logger = logging.getLogger('accounts')

SQ_MAX_ATTEMPTS = 3
SQ_LOCKOUT_MINS = 15


# ============================================================
# CSRF FAILURE — friendly redirect instead of yellow 403 page
# ============================================================
@requires_csrf_token
def csrf_failure(request, reason=''):
    """
    Redirect back to the referring page (or login) with a flash message
    so the user gets a fresh CSRF token instead of seeing a 403 error.
    """
    messages.warning(
        request,
        'Your session expired or the page was open too long. Please try again.'
    )
    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


def validate_strong_password(password: str) -> list[str]:
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
# LOGIN  — supports phone number OR full name
# ============================================================
def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not login_id or not password:
            return render(request, 'login.html', {
                'error': 'Please enter your login ID and password.'
            })

        # ── Helper: return deactivated response ───────────
        def deactivated_response(raw_user):
            return render(request, 'login.html', {
                'error': 'Your account has been deactivated. Contact the administrator.',
                'deactivated': True,
                'deactivated_name': raw_user.get_full_name() or raw_user.username,
                'deactivated_phone': raw_user.username,
            })

        # ── Step 1: try phone number (username) directly ──
        # Check deactivation BEFORE authenticate() so we show the right message
        try:
            raw_by_phone = User.objects.get(username=login_id)
            if raw_by_phone.check_password(password):
                if not raw_by_phone.is_active:
                    return deactivated_response(raw_by_phone)
        except User.DoesNotExist:
            raw_by_phone = None

        user = authenticate(request, username=login_id, password=password)

        # ── Step 2: try full name lookup ──────────────────
        if not user:
            normalized = ' '.join(login_id.split())
            parts      = normalized.split(' ', 1)
            first      = parts[0]
            last       = parts[1] if len(parts) > 1 else ''

            candidates = (
                User.objects.filter(first_name__iexact=first, last_name__iexact=last)
                if last else
                User.objects.filter(first_name__iexact=first)
            )

            for candidate in candidates:
                if candidate.check_password(password):
                    # Found the right user by full name — check deactivation first
                    if not candidate.is_active:
                        return deactivated_response(candidate)
                    result = authenticate(request, username=candidate.username, password=password)
                    if result:
                        user = result
                        break

        # ── Step 3: handle result ─────────────────────────
        if user:
            # Final guard — never log in an inactive user
            if not user.is_active:
                return deactivated_response(user)
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url if next_url else 'dashboard')

        return render(request, 'login.html', {
            'error': 'Invalid credentials. Use your phone number or full name.'
        })

    return render(request, 'login.html')


# ============================================================
# REGISTER
# ============================================================
def register(request):
    blood_groups = BloodGroup.objects.all()

    if request.method == 'POST':
        full_name         = request.POST.get('full_name', '').strip()
        parts             = full_name.split(' ', 1)
        first_name        = parts[0].strip()
        last_name         = parts[1].strip() if len(parts) > 1 else ''
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
        health_document   = request.FILES.get('health_document')

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
            first_name__iexact=first_name, last_name__iexact=last_name
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

        has_health_issue = (health_issue == "True")
        if has_health_issue and health_document:
            allowed = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
            if health_document.content_type not in allowed:
                field_errors['health_document'] = 'Only JPG, PNG, or PDF files are allowed.'
            elif health_document.size > 5 * 1024 * 1024:
                field_errors['health_document'] = 'File size must not exceed 5 MB.'

        if field_errors:
            return render(request, 'register.html', {
                'blood_groups': blood_groups,
                'security_questions': SECURITY_QUESTIONS,
                'field_errors': field_errors,
                'form_data': request.POST,
            })

        eligibility = 'PENDING' if has_health_issue else 'ELIGIBLE'

        try:
            with transaction.atomic():
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
                    health_document=health_document if has_health_issue else None,
                    eligibility_status=eligibility,
                    address=address, pincode=pincode,
                    city=city, state=state, nation=nation
                )
                sp = SecurityProfile(user=user, question_key=question_key)
                sp.set_answer(sq_answer)
                sp.save()
        except IntegrityError as e:
            err_str = str(e).lower()
            if 'email' in err_str:
                field_errors['email'] = 'This email is already registered.'
            elif 'phone' in err_str or 'username' in err_str:
                field_errors['phone'] = 'This mobile number is already registered.'
            else:
                field_errors['__all__'] = 'Registration failed due to a conflict. Please check your details.'
            return render(request, 'register.html', {
                'blood_groups': blood_groups,
                'security_questions': SECURITY_QUESTIONS,
                'field_errors': field_errors,
                'form_data': request.POST,
            })

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

    if not user.role:
        return redirect('login')

    if user.role == 'ADMIN':
        from agents.models import AgentExecutionLog
        from django.db.models import Sum

        ai_logs = AgentExecutionLog.objects.select_related('blood_request', 'blood_request__user')
        ai_total_runs = ai_logs.count()
        ai_donors_notified = ai_logs.aggregate(Sum('donors_notified_count'))['donors_notified_count__sum'] or 0
        pending_prescriptions = BloodRequest.objects.filter(status='PENDING').exclude(prescription_document='').count()

        stats = {
            'total_donors':          Donor.objects.count(),
            'total_requests':        BloodRequest.objects.count(),
            'pending_requests':      BloodRequest.objects.filter(status='PENDING').count(),
            'pending_health':        Donor.objects.filter(eligibility_status='PENDING').count(),
            'total_donations':       Donation.objects.count(),
            'low_stock':             BloodStock.objects.filter(units_available__lt=5).count(),
            'unread_messages':       ContactAdminMessage.objects.filter(is_read=False).count(),
            'ai_total_runs':         ai_total_runs,
            'ai_donors_notified':    ai_donors_notified,
            'pending_prescriptions': pending_prescriptions,
        }
        recent_ai_logs = ai_logs[:5]
        return render(request, 'admin_dashboard.html', {
            'stats': stats,
            'recent_ai_logs': recent_ai_logs,
        })

    elif user.role == 'DONOR':
        has_emergency = BloodRequest.objects.filter(
            status='PENDING', urgency='EMERGENCY'
        ).exists()
        try:
            donor = Donor.objects.get(user=user)
        except Donor.DoesNotExist:
            donor = None
        return render(request, 'donor_dashboard.html', {
            'has_emergency': has_emergency,
            'donor': donor,
        })

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
# FORGOT PASSWORD — Step 1
# ============================================================
def sq_lookup(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        user = (User.objects.filter(username=identifier).first() or
                User.objects.filter(email__iexact=identifier).first())

        if not user:
            logger.warning(f"SQ lookup for unknown: {identifier}")
            return render(request, 'sq_lookup.html', {
                'error': 'No account found with that phone number or email.'
            })

        try:
            sp = user.security_profile
        except SecurityProfile.DoesNotExist:
            return render(request, 'sq_lookup.html', {
                'error': 'This account has no security question set. Contact support.'
            })

        if sp.locked_until and timezone.now() < sp.locked_until:
            remaining = int((sp.locked_until - timezone.now()).total_seconds() // 60) + 1
            return render(request, 'sq_lookup.html', {
                'error': f'Account locked. Try again in {remaining} minute(s).'
            })

        request.session['sq_username'] = user.username
        return redirect('sq_answer')

    return render(request, 'sq_lookup.html')


# ============================================================
# FORGOT PASSWORD — Step 2
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
            return redirect('sq_reset_password')
        else:
            sp.reset_attempts += 1
            remaining = SQ_MAX_ATTEMPTS - sp.reset_attempts
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
# FORGOT PASSWORD — Step 3
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
                AuditLog.objects.create(
                    actor=request.user, action='Health Approved',
                    target=f'Donor: {donor.user.get_full_name() or donor.user.username}'
                )
            elif action == 'reject':
                donor.eligibility_status = 'REJECTED'
                donor.save()
                Notification.objects.create(
                    user=donor.user, title='Health Status Rejected',
                    message='Your health eligibility has been rejected by the admin.',
                    notif_type='danger'
                )
                AuditLog.objects.create(
                    actor=request.user, action='Health Rejected',
                    target=f'Donor: {donor.user.get_full_name() or donor.user.username}'
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
            f"{d.user.first_name} {d.user.last_name}".strip(),
            d.phone, d.user.email,
            d.blood_group.blood_group, d.city or '', d.eligibility_status
        ])
    return response


# ============================================================
# ADMIN AUDIT LOG
# ============================================================
@login_required
def audit_log(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    logs = AuditLog.objects.select_related('actor').all()[:200]
    return render(request, 'audit_log.html', {'logs': logs})


# ============================================================
# ACCOUNT DEACTIVATION / REACTIVATION
# ============================================================
@login_required
def toggle_donor_active(request, donor_id):
    if not request.user.is_staff:
        return redirect('dashboard')
    try:
        donor = Donor.objects.select_related('user').get(id=donor_id)
        donor.user.is_active = not donor.user.is_active
        donor.user.save()
        action = 'Activated' if donor.user.is_active else 'Deactivated'
        AuditLog.objects.create(
            actor=request.user,
            action=f'Account {action}',
            target=f'Donor: {donor.user.get_full_name() or donor.user.username}',
            detail=f'is_active set to {donor.user.is_active}'
        )
        Notification.objects.create(
            user=donor.user,
            title=f'Account {action}',
            message=f'Your account has been {action.lower()} by an administrator.',
            notif_type='success' if donor.user.is_active else 'warning'
        )
        messages.success(request, f'Account {action.lower()} successfully.')
    except Donor.DoesNotExist:
        messages.error(request, 'Donor not found.')
    return redirect('admin_all_donors')


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
        parts      = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name  = parts[1] if len(parts) > 1 else ''
        user.email = request.POST.get('email', '').strip().lower()
        user.save()

        if donor:
            donor.address = request.POST.get('address')
            donor.city    = request.POST.get('city')
            donor.pincode = request.POST.get('pincode')
            donor.state   = request.POST.get('state')
            donor.nation  = request.POST.get('nation')
            donor.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'profile.html', {'donor': donor})


# ============================================================
# CONTACT ADMIN — deactivated user sends a message
# ============================================================
def contact_admin(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()

        if not name or not phone or not message:
            return render(request, 'contact_admin.html', {
                'error': 'All fields are required.',
                'form_data': request.POST,
            })

        ContactAdminMessage.objects.create(name=name, phone=phone, message=message)
        return render(request, 'contact_admin.html', {'success': True})

    name  = request.GET.get('name', '')
    phone = request.GET.get('phone', '')
    return render(request, 'contact_admin.html', {'prefill_name': name, 'prefill_phone': phone})


# ============================================================
# ADMIN — view all contact messages
# ============================================================
@login_required
def admin_contact_messages(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        msg_id = request.POST.get('msg_id')
        action = request.POST.get('action')
        try:
            msg = ContactAdminMessage.objects.get(id=msg_id)
            if action == 'read':
                msg.is_read = True
                msg.save()
            elif action == 'delete':
                msg.delete()
        except ContactAdminMessage.DoesNotExist:
            pass
        return redirect('admin_contact_messages')

    msgs = ContactAdminMessage.objects.all()
    return render(request, 'admin_contact_messages.html', {
        'messages_list': msgs,
        'unread_count': msgs.filter(is_read=False).count(),
    })
