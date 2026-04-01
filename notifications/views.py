from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    # Mark as read when visited? Or maybe just have a separate mark-as-read action.
    # Let's just list them.
    return render(request, 'notifications.html', {
        'notifications': notifications
    })

@login_required
def mark_as_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_view')

@login_required
def mark_all_as_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications_view')
