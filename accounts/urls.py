from django.urls import path
from .views import login_view, register, dashboard, logout_view

urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
]
