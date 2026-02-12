from django.urls import path
from . import views

urlpatterns = [
    path('add-donation/', views.add_donation, name='add_donation'),
    path('my-donations/', views.my_donations, name='my_donations'),
    path('request-blood/', views.request_blood, name='request_blood'),
    path('my-requests/', views.my_requests, name='my_requests'),
]
