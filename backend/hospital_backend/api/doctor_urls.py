from django.urls import path
from doctors.api.views import (
    DoctorAvailabilityView, DoctorAppointmentListView, DoctorAppointmentDetailView,
    DoctorPrescriptionView, DoctorFeedbackListView, DoctorProfileView, DoctorPatientHistoryView
)

urlpatterns = [
    path('availability', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('appointments', DoctorAppointmentListView.as_view(), name='doctor-appointments'),
    path('appointments/<int:appt_id>', DoctorAppointmentDetailView.as_view(), name='doctor-appointment-detail'),
    path('prescriptions/<int:appt_id>', DoctorPrescriptionView.as_view(), name='doctor-prescription'),
    path('feedback', DoctorFeedbackListView.as_view(), name='doctor-feedback'),
    path('profile', DoctorProfileView.as_view(), name='doctor-profile'),
    path('patients/<int:patient_id>/history', DoctorPatientHistoryView.as_view(), name='doctor-patient-history'),
]
