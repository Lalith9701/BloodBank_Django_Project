from .models import Notification

def unread_notifications_count(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}
