from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.models import User, SystemConfig, AuditLog
from doctors.models import Doctor, Department
from patients.models import Patient
from appointments.models import Appointment, Feedback
from django.db.models import Avg
from datetime import date, timedelta
from accounts.api.serializers import UserSerializer
from doctors.api.serializers import DoctorSerializer, DepartmentSerializer
from patients.api.serializers import PatientSerializer
from appointments.api.serializers import AppointmentSerializer, FeedbackSerializer
from accounts.models import Announcement, Notification
from accounts.api.serializers import AnnouncementSerializer

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_doctors = Doctor.objects.count()
        total_patients = Patient.objects.count()
        total_appointments = Appointment.objects.count()
        
        booked = Appointment.objects.filter(status='booked').count()
        completed = Appointment.objects.filter(status='completed').count()
        cancelled = Appointment.objects.filter(status='cancelled').count()
        
        avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0

        # Monthly appointments (last 6 months)
        monthly = []
        today = date.today()
        for i in range(5, -1, -1):
            # approximate months
            d = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
            count = Appointment.objects.filter(
                appointment_date__year=d.year,
                appointment_date__month=d.month
            ).count()
            monthly.append({
                'month': d.strftime('%b %Y'),
                'count': count
            })

        return Response({
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'appointments_by_status': {'booked': booked, 'completed': completed, 'cancelled': cancelled},
            'avg_rating': round(float(avg_rating), 1),
            'monthly_appointments': monthly,
        }, status=status.HTTP_200_OK)


class AdminDepartmentListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        depts = Department.objects.all()
        return Response(DepartmentSerializer(depts, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response({'message': 'Department name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if Department.objects.filter(name=name).exists():
            return Response({'message': 'Department already exists'}, status=status.HTTP_409_CONFLICT)
            
        dept = Department.objects.create(
            name=name, 
            description=request.data.get('description', '')
        )
        AuditLog.objects.create(user=request.user, action=f"Created department: {dept.name}", resource='department')
        return Response(DepartmentSerializer(dept).data, status=status.HTTP_201_CREATED)


class AdminDepartmentDetailView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, dept_id):
        try:
            dept = Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        dept.name = request.data.get('name', dept.name)
        dept.description = request.data.get('description', dept.description)
        dept.save()
        return Response(DepartmentSerializer(dept).data, status=status.HTTP_200_OK)

    def delete(self, request, dept_id):
        try:
            dept = Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        dept.delete()
        return Response({'message': 'Department deleted'}, status=status.HTTP_200_OK)


class AdminDoctorListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        doctors = Doctor.objects.select_related('user').all()
        return Response(DoctorSerializer(doctors, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'message': 'Email already exists'}, status=status.HTTP_409_CONFLICT)
            
        user = User.objects.create(
            name=request.data.get('name'),
            email=email,
            username=email,
            role='doctor',
            phone=request.data.get('phone'),
            is_active=True
        )
        user.set_password(request.data.get('password', 'Doctor@123'))
        user.save()
        
        doctor = Doctor.objects.create(
            user=user,
            department_id=request.data.get('department_id'),
            specialization=request.data.get('specialization'),
            qualification=request.data.get('qualification'),
            experience_years=request.data.get('experience_years', 0),
            consultation_fee=request.data.get('consultation_fee', 0),
            bio=request.data.get('bio'),
            is_approved=True
        )
        return Response(DoctorSerializer(doctor).data, status=status.HTTP_201_CREATED)


class AdminDoctorDetailView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        doctor.specialization = request.data.get('specialization', doctor.specialization)
        doctor.qualification = request.data.get('qualification', doctor.qualification)
        doctor.experience_years = request.data.get('experience_years', doctor.experience_years)
        doctor.consultation_fee = request.data.get('consultation_fee', doctor.consultation_fee)
        doctor.department_id = request.data.get('department_id', doctor.department_id)
        doctor.bio = request.data.get('bio', doctor.bio)
        doctor.is_approved = request.data.get('is_approved', doctor.is_approved)
        doctor.save()
        
        user = doctor.user
        user.name = request.data.get('name', user.name)
        user.phone = request.data.get('phone', user.phone)
        user.save()
        
        return Response(DoctorSerializer(doctor).data, status=status.HTTP_200_OK)

    def delete(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        doctor.user.delete() # Casacades
        return Response({'message': 'Doctor deleted'}, status=status.HTTP_200_OK)


class AdminDoctorStatusView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        user = doctor.user
        user.is_active = request.data.get('is_active', not user.is_active)
        user.save()
        
        doctor.is_approved = request.data.get('is_approved', doctor.is_approved)
        doctor.save()
        
        return Response({'message': 'Updated', 'is_active': user.is_active}, status=status.HTTP_200_OK)


class AdminPatientListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        patients = Patient.objects.select_related('user').all()
        return Response(PatientSerializer(patients, many=True).data, status=status.HTTP_200_OK)


class AdminPatientDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        user = patient.user
        user.is_active = request.data.get('is_active', not user.is_active)
        user.save()
        return Response({'message': 'Updated'}, status=status.HTTP_200_OK)

    def delete(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        # Deleting the user will cascade delete the patient profile,
        # appointments, vitals, and medical documents.
        patient.user.delete()
        return Response({'message': 'Patient account and all associated records deleted'}, status=status.HTTP_200_OK)


class AdminAppointmentListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_param = request.query_params.get('status')
        q = Appointment.objects.all().order_by('-appointment_date')
        if status_param:
            q = q.filter(status=status_param)
        return Response(AppointmentSerializer(q, many=True).data, status=status.HTTP_200_OK)


from patients.services.email_service import send_cancellation_email

class AdminAppointmentCancelView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, appt_id):
        try:
            appt = Appointment.objects.get(id=appt_id)
        except Appointment.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        appt.status = 'cancelled'
        appt.save()
        
        try:
            send_cancellation_email(appt)
        except Exception:
            pass
            
        return Response({'message': 'Appointment cancelled'}, status=status.HTTP_200_OK)


class AdminFeedbackListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        feedbacks = Feedback.objects.all().order_by('-created_at')
        return Response(FeedbackSerializer(feedbacks, many=True).data, status=status.HTTP_200_OK)


class AdminFeedbackVisibilityView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, fb_id):
        try:
            fb = Feedback.objects.get(id=fb_id)
        except Feedback.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        fb.is_visible = request.data.get('is_visible', not fb.is_visible)
        fb.save()
        return Response({'message': 'Updated', 'is_visible': fb.is_visible}, status=status.HTTP_200_OK)


class AdminSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        configs = SystemConfig.objects.all()
        return Response([{'id': c.id, 'key': c.key, 'value': c.value, 'description': c.description} for c in configs], status=status.HTTP_200_OK)

    def put(self, request):
        for key, value in request.data.items():
            config, created = SystemConfig.objects.get_or_create(key=key)
            config.value = str(value)
            config.save()
        return Response({'message': 'Settings updated'}, status=status.HTTP_200_OK)

class AdminAuditLogsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        logs = AuditLog.objects.order_by('-created_at')[:200]
        return Response([{
            'id': l.id,
            'user_id': l.user_id,
            'user_name': l.user.name if l.user else 'Unknown',
            'action': l.action,
            'resource': l.resource,
            'ip_address': l.ip_address,
            'created_at': l.created_at.isoformat() if l.created_at else None,
        } for l in logs], status=status.HTTP_200_OK)

import csv
from django.http import HttpResponse

class AdminAuditLogsExportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Action', 'Resource', 'IP Address', 'Time'])

        logs = AuditLog.objects.select_related('user').order_by('-created_at')
        for l in logs:
            writer.writerow([
                l.id,
                l.user.name if l.user else 'Unknown',
                l.action,
                l.resource,
                l.ip_address,
                l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else ''
            ])

        return response


class AdminAnnouncementListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        announcements = Announcement.objects.all().order_by('-created_at')
        return Response(AnnouncementSerializer(announcements, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        title = request.data.get('title')
        content = request.data.get('content')
        target = request.data.get('target', 'All')

        if not title or not content:
            return Response({'message': 'Title and content are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Create announcement
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            target=target,
            created_by=request.user
        )

        AuditLog.objects.create(user=request.user, action=f"Created announcement to {target}", resource='announcement')

        # Generate notifications for the target demographic
        users_to_notify = []
        if target == 'Doctors':
            users_to_notify = User.objects.filter(role='doctor', is_active=True)
        elif target == 'Patients':
            users_to_notify = User.objects.filter(role='patient', is_active=True)
        else: # 'All'
            users_to_notify = User.objects.filter(is_active=True) # Exclude admin or keep admin? Kept for simplicity

        notifications = [
            Notification(
                user=user,
                title=title,
                message=content,
                type='announcement',
                related_id=announcement.id
            ) for user in users_to_notify
        ]
        
        # Insert them all quickly
        if notifications:
            Notification.objects.bulk_create(notifications)

        return Response(AnnouncementSerializer(announcement).data, status=status.HTTP_201_CREATED)


class AdminAnnouncementDetailView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, ann_id):
        try:
            ann = Announcement.objects.get(id=ann_id)
            ann.delete()
            return Response({'message': 'Announcement deleted'}, status=status.HTTP_200_OK)
        except Announcement.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
