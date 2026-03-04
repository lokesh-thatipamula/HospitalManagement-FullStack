from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.api.urls')),
    path('api/admin/', include('hospital_backend.api.admin_urls')),
    path('api/doctor/', include('hospital_backend.api.doctor_urls')),
    path('api/patient/', include('hospital_backend.api.patient_urls')),
]
