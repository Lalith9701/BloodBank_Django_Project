from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from requests_app.models import BloodRequest
from agents.models import AgentExecutionLog
from agents.services.emergency_agent import run_emergency_dispatch_agent


@login_required
def agent_dashboard(request):
    """
    Staff dashboard displaying AI Agent execution logs, reasoning summaries, and metrics.
    """
    if not request.user.is_staff:
        messages.error(request, "Access restricted to Staff and Admins.")
        return redirect('dashboard')

    logs = AgentExecutionLog.objects.select_related('blood_request', 'blood_request__user').all()

    total_runs = logs.count()
    total_notified = logs.aggregate(Sum('donors_notified_count'))['donors_notified_count__sum'] or 0
    auto_runs = logs.filter(trigger_type='AUTOMATIC').count()
    manual_runs = logs.filter(trigger_type='MANUAL_ADMIN').count()

    context = {
        'logs': logs,
        'total_runs': total_runs,
        'total_notified': total_notified,
        'auto_runs': auto_runs,
        'manual_runs': manual_runs,
    }
    return render(request, 'agent_dashboard.html', context)


@login_required
def trigger_agent(request, request_id):
    """
    Manually triggers the Emergency Match & Dispatch Agent for a specific Blood Request.
    """
    if not request.user.is_staff:
        messages.error(request, "Only staff members can trigger the AI Agent.")
        return redirect('dashboard')

    blood_request = get_object_or_404(BloodRequest, id=request_id)

    try:
        log_entry = run_emergency_dispatch_agent(blood_request.id, trigger_type='MANUAL_ADMIN')
        messages.success(
            request,
            f"🤖 Emergency Agent successfully executed for Request #{blood_request.id}! "
            f"Notified {log_entry.donors_notified_count} compatible donor(s)."
        )
    except Exception as e:
        messages.error(request, f"Failed to execute AI Agent: {str(e)}")

    next_url = request.META.get('HTTP_REFERER') or 'agent_dashboard'
    return redirect(next_url)
