from django.urls import path
from . import views   # 🔥 THIS LINE IS IMPORTANT

urlpatterns = [
    path('blood-stock/', views.blood_stock, name='blood_stock'),
    path('add-blood-group/', views.add_blood_group, name='add_blood_group'),
    path('add-blood-stock/', views.add_blood_stock, name='add_blood_stock'),
]