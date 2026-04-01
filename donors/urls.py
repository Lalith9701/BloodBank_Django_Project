from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.donor_search, name='donor_search'),
]
