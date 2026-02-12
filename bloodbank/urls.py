from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('inventory/', include('inventory.urls')),
    path('requests/', include('requests_app.urls')),
]
