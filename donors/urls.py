from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.donor_search, name='donor_search'),
    path('rewards/', views.donor_rewards, name='donor_rewards'),
    path('rewards/certificate/', views.donor_family_certificate, name='donor_family_certificate'),
]

