from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_view, name='notifications_view'),
    path('mark-read/<int:notif_id>/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),
]
