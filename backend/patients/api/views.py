from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.models import User, Notification
from doctors.models import Doctor, Department, Availability
from appointments.models import Appointment, Feedback
from patients.models import Patient, Vital, MedicalDocument
from doctors.api.serializers import DoctorSerializer, DepartmentSerializer
from patients.api.serializers import PatientSerializer, VitalSerializer, MedicalDocumentSerializer
from appointments.api.serializers import AppointmentSerializer
from patients.services.email_service import send_appointment_confirmation, send_cancellation_email
from datetime import datetime, timedelta

class IsPatientUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'patient'

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'

class IsAdminOrPatient(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in ['admin', 'patient']

def get_patient(user):
    try:
        return user.patient_profile
    except Patient.DoesNotExist:
        return None

class PatientDoctorSearchView(APIView):
    permission_classes = [IsPatientUser]

    def get(self, request):
        name = request.query_params.get('name', '').strip()
        department_id = request.query_params.get('department_id')
        min_rating = request.query_params.get('min_rating')

        q = Doctor.objects.select_related('user').filter(
            is_approved=True, 
            user__is_active=True
        )

        if name:
            q = q.filter(user__name__icontains=name)
        if department_id:
            q = q.filter(department_id=int(department_id))

        doctors = list(q.all())
        if min_rating:
            try:
                min_r = float(min_rating)
                doctors = [d for d in doctors if d.avg_rating >= min_r]
            except ValueError:
                pass

        return Response(DoctorSerializer(doctors, many=True).data, status=status.HTTP_200_OK)


class PatientDepartmentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        depts = Department.objects.all()
        return Response(DepartmentSerializer(depts, many=True).data, status=status.HTTP_200_OK)


class PatientDoctorSlotsView(APIView):
    permission_classes = [IsPatientUser]

    def get(self, request, doctor_id):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'message': 'Date parameter required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'message': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        day_of_week = appt_date.weekday()

        availability = Availability.objects.filter(
            doctor_id=doctor_id,
            day_of_week=day_of_week,
            is_available=True
        ).first()

        if not availability:
            return Response({'slots': [], 'message': 'No availability on this day'}, status=status.HTTP_200_OK)

        slots = []
        start = datetime.combine(appt_date, availability.start_time)
        end = datetime.combine(appt_date, availability.end_time)
        delta_mins = availability.slot_duration

        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=appt_date,
        ).exclude(status='cancelled')
        
        booked_times = {a.slot_time.strftime('%H:%M') for a in booked_appointments}

        current = start
        while current < end:
            slot_str = current.strftime('%H:%M')
            slots.append({
                'time': slot_str,
                'available': slot_str not in booked_times
            })
            current += timedelta(minutes=delta_mins)

        return Response({'slots': slots}, status=status.HTTP_200_OK)


class PatientAppointmentView(APIView):
    permission_classes = [IsPatientUser]

    def get(self, request):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
        return Response(AppointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        doctor_id = data.get('doctor_id')
        appt_date_str = data.get('appointment_date')
        slot_time_str = data.get('slot_time')

        if not all([doctor_id, appt_date_str, slot_time_str]):
            return Response({'message': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appt_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
            slot_time = datetime.strptime(slot_time_str, '%H:%M').time()
        except ValueError:
            return Response({'message': 'Invalid date or time format'}, status=status.HTTP_400_BAD_REQUEST)

        existing = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=appt_date,
            slot_time=slot_time
        ).exclude(status='cancelled').first()

        if existing:
            return Response({'message': 'This slot is already booked'}, status=status.HTTP_409_CONFLICT)

        appt = Appointment.objects.create(
            patient=patient,
            doctor_id=doctor_id,
            appointment_date=appt_date,
            slot_time=slot_time,
            reason=data.get('reason'),
            status='booked'
        )

        try:
            send_appointment_confirmation(appt)
        except Exception:
            pass

        # Generate Notification for Doctor
        try:
            Notification.objects.create(
                user=appt.doctor.user,
                title="New Appointment Booking",
                message=f"A new appointment has been scheduled by {patient.user.name} for {appt_date.strftime('%b %d, %Y')} at {slot_time.strftime('%I:%M %p')}.",
                type="appointment",
                related_id=appt.id
            )
        except Exception as e:
            print("Failed to create notification for doctor:", str(e))
        
        return Response(AppointmentSerializer(appt).data, status=status.HTTP_201_CREATED)

class PatientAppointmentCancelView(APIView):
    permission_classes = [IsPatientUser]

    def delete(self, request, appt_id):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            appt = Appointment.objects.get(id=appt_id, patient=patient)
        except Appointment.DoesNotExist:
            return Response({'message': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if appt.status != 'booked':
            return Response({'message': 'Only booked appointments can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        appt.status = 'cancelled'
        appt.save()

        try:
            send_cancellation_email(appt)
        except Exception:
            pass

        return Response({'message': 'Appointment cancelled'}, status=status.HTTP_200_OK)

class PatientFeedbackView(APIView):
    permission_classes = [IsPatientUser]

    def post(self, request, appt_id):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            appt = Appointment.objects.get(id=appt_id, patient=patient, status='completed')
        except Appointment.DoesNotExist:
            return Response({'message': 'Completed appointment not found'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(appt, 'feedback'):
            return Response({'message': 'Feedback already submitted'}, status=status.HTTP_409_CONFLICT)

        rating = request.data.get('rating')
        if rating is None or not (1 <= int(rating) <= 5):
            return Response({'message': 'Rating must be between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)

        feedback = Feedback.objects.create(
            appointment=appt,
            patient=patient,
            doctor=appt.doctor,
            rating=int(rating),
            comment=request.data.get('comment')
        )
        
        return Response({
            'message': 'Feedback created', 
            'feedback_id': feedback.id
        }, status=status.HTTP_201_CREATED)


class PatientProfileView(APIView):
    permission_classes = [IsPatientUser]

    def get(self, request):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(PatientSerializer(patient).data, status=status.HTTP_200_OK)

    def put(self, request):
        patient = get_patient(request.user)
        if not patient:
            return Response({'message': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        data = request.data
        patient.gender = data.get('gender', patient.gender)
        patient.blood_group = data.get('blood_group', patient.blood_group)
        patient.address = data.get('address', patient.address)
        patient.emergency_contact = data.get('emergency_contact', patient.emergency_contact)
        patient.medical_history = data.get('medical_history', patient.medical_history)
        
        if data.get('date_of_birth'):
            try:
                patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        patient.save()

        user = patient.user
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.save()

        return Response(PatientSerializer(patient).data, status=status.HTTP_200_OK)

class PatientVitalView(APIView):
    permission_classes = [IsAdminOrPatient]

    def get(self, request):
        # If patient, get their own. If admin, expect patient_id in query params.
        if request.user.role == 'patient':
            patient = get_patient(request.user)
        else:
            patient_id = request.query_params.get('patient_id')
            if not patient_id:
                return Response({'message': 'patient_id required for admin'}, status=status.HTTP_400_BAD_REQUEST)
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({'message': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        vitals = Vital.objects.filter(patient=patient)
        return Response(VitalSerializer(vitals, many=True).data)

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'message': 'Only admins can log vitals'}, status=status.HTTP_403_FORBIDDEN)
        
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({'message': 'patient_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response({'message': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = VitalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientMedicalDocumentView(APIView):
    permission_classes = [IsAdminOrPatient]

    def get(self, request):
        if request.user.role == 'patient':
            patient = get_patient(request.user)
        else:
            patient_id = request.query_params.get('patient_id')
            if not patient_id:
                return Response({'message': 'patient_id required for admin'}, status=status.HTTP_400_BAD_REQUEST)
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({'message': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        docs = MedicalDocument.objects.filter(patient=patient)
        return Response(MedicalDocumentSerializer(docs, many=True).data)

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'message': 'Only admins can upload documents'}, status=status.HTTP_403_FORBIDDEN)
        
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({'message': 'patient_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response({'message': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MedicalDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, doc_id):
        if request.user.role != 'admin':
            return Response({'message': 'Only admins can delete documents'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            doc = MedicalDocument.objects.get(id=doc_id)
            doc.delete()
            return Response({'message': 'Document deleted'}, status=status.HTTP_200_OK)
        except MedicalDocument.DoesNotExist:
            return Response({'message': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
