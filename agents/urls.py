from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('trigger/<int:request_id>/', views.trigger_agent, name='trigger_agent'),
]
