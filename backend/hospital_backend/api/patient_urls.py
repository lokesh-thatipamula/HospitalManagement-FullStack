from django.urls import path
from patients.api.views import (
    PatientDoctorSearchView, PatientDepartmentListView, PatientDoctorSlotsView,
    PatientAppointmentView, PatientAppointmentCancelView, PatientFeedbackView,
    PatientProfileView, PatientVitalView, PatientMedicalDocumentView
)

urlpatterns = [
    path('doctors', PatientDoctorSearchView.as_view(), name='patient-doctors'),
    path('departments', PatientDepartmentListView.as_view(), name='patient-departments'),
    path('doctors/<int:doctor_id>/slots', PatientDoctorSlotsView.as_view(), name='patient-doctor-slots'),
    path('appointments', PatientAppointmentView.as_view(), name='patient-appointments'),
    path('appointments/<int:appt_id>', PatientAppointmentCancelView.as_view(), name='patient-appointments-cancel'),
    path('appointments/<int:appt_id>/feedback', PatientFeedbackView.as_view(), name='patient-appointments-feedback'),
    path('profile', PatientProfileView.as_view(), name='patient-profile'),
    path('vitals', PatientVitalView.as_view(), name='patient-vitals'),
    path('vault', PatientMedicalDocumentView.as_view(), name='patient-vault'),
    path('vault/<int:doc_id>', PatientMedicalDocumentView.as_view(), name='patient-vault-delete'),
]
