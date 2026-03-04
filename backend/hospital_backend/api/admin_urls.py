from django.urls import path
from accounts.api.admin_views import (
    AdminDashboardView, AdminDepartmentListView, AdminDepartmentDetailView,
    AdminDoctorListView, AdminDoctorDetailView, AdminDoctorStatusView,
    AdminPatientListView, AdminPatientDetailView, AdminAppointmentListView,
    AdminAppointmentCancelView, AdminFeedbackListView, AdminFeedbackVisibilityView,
    AdminAuditLogsView, AdminAuditLogsExportView, AdminSettingsView,
    AdminAnnouncementListView, AdminAnnouncementDetailView
)

urlpatterns = [
    path('dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('departments', AdminDepartmentListView.as_view(), name='admin-departments'),
    path('departments/<int:dept_id>', AdminDepartmentDetailView.as_view(), name='admin-dept-detail'),
    path('doctors', AdminDoctorListView.as_view(), name='admin-doctors'),
    path('doctors/<int:doctor_id>', AdminDoctorDetailView.as_view(), name='admin-doctor-detail'),
    path('doctors/<int:doctor_id>/status', AdminDoctorStatusView.as_view(), name='admin-doctor-status'),
    path('patients', AdminPatientListView.as_view(), name='admin-patients'),
    path('patients/<int:patient_id>', AdminPatientDetailView.as_view(), name='admin-patient-detail'),
    path('appointments', AdminAppointmentListView.as_view(), name='admin-appointments'),
    path('appointments/<int:appt_id>/cancel', AdminAppointmentCancelView.as_view(), name='admin-appt-cancel'),
    path('feedback', AdminFeedbackListView.as_view(), name='admin-feedback'),
    path('feedback/<int:fb_id>/visibility', AdminFeedbackVisibilityView.as_view(), name='admin-feedback-visibility'),
    path('audit-logs', AdminAuditLogsView.as_view(), name='admin-audit-logs'),
    path('audit-logs/export', AdminAuditLogsExportView.as_view(), name='admin-audit-logs-export'),
    path('settings', AdminSettingsView.as_view(), name='admin-settings'),
    path('announcements', AdminAnnouncementListView.as_view(), name='admin-announcements'),
    path('announcements/<int:ann_id>', AdminAnnouncementDetailView.as_view(), name='admin-announcement-detail'),
]
