from django.urls import path
from . import views

urlpatterns = [
    path('rate/<int:request_id>/', views.rate_blood_request, name='rate_blood_request'),
]
