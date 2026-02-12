from django.urls import path
from .views import blood_stock, add_blood_group, add_blood_stock

urlpatterns = [
    path('stock/', blood_stock, name='blood_stock'),
    path('add-group/', add_blood_group, name='add_blood_group'),
    path('add-stock/', add_blood_stock, name='add_blood_stock'),
]
