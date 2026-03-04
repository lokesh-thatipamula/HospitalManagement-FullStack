from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from doctors.models import Doctor, Availability
from appointments.models import Appointment, Prescription, Feedback
from doctors.api.serializers import AvailabilitySerializer, DoctorSerializer
from appointments.api.serializers import AppointmentSerializer, FeedbackSerializer
from patients.services.email_service import send_prescription_email
from datetime import datetime

class IsDoctorUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'doctor'

def get_doctor(user):
    try:
        return user.doctor_profile
    except Doctor.DoesNotExist:
        return None

class DoctorAvailabilityView(APIView):
    permission_classes = [IsDoctorUser]

    def get(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        availabilities = doctor.availabilities.all()
        return Response(AvailabilitySerializer(availabilities, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if not isinstance(data, list):
            data = [data]

        # Clear existing
        doctor.availabilities.all().delete()

        for slot in data:
            try:
                start = datetime.strptime(slot['start_time'], '%H:%M').time()
                end = datetime.strptime(slot['end_time'], '%H:%M').time()
            except ValueError:
                continue # Skip invalid times
                
            Availability.objects.create(
                doctor=doctor,
                day_of_week=slot.get('day_of_week', 0),
                start_time=start,
                end_time=end,
                slot_duration=slot.get('slot_duration', 30),
                is_available=slot.get('is_available', True)
            )

        return Response({'message': 'Availability updated'}, status=status.HTTP_200_OK)


class DoctorAppointmentListView(APIView):
    permission_classes = [IsDoctorUser]

    def get(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

        status_param = request.query_params.get('status')
        date_str = request.query_params.get('date')

        q = Appointment.objects.filter(doctor=doctor)
        if status_param:
            q = q.filter(status=status_param)
        if date_str:
            try:
                appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                q = q.filter(appointment_date=appt_date)
            except ValueError:
                pass

        appointments = q.order_by('appointment_date')
        return Response(AppointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)


class DoctorAppointmentDetailView(APIView):
    permission_classes = [IsDoctorUser]

    def patch(self, request, appt_id):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            appt = Appointment.objects.get(id=appt_id, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({'message': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

        appt.status = request.data.get('status', appt.status)
        appt.notes = request.data.get('notes', appt.notes)
        appt.save()
        return Response(AppointmentSerializer(appt).data, status=status.HTTP_200_OK)


class DoctorPrescriptionView(APIView):
    permission_classes = [IsDoctorUser]

    def post(self, request, appt_id):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            appt = Appointment.objects.get(id=appt_id, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({'message': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

        follow_up = None
        if request.data.get('follow_up_date'):
            try:
                follow_up = datetime.strptime(request.data['follow_up_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        # Use hasattr since it's a OneToOneField
        if hasattr(appt, 'prescription'):
            prescription = appt.prescription
            prescription.medications = request.data.get('medications', prescription.medications)
            prescription.instructions = request.data.get('instructions', prescription.instructions)
            prescription.follow_up_date = follow_up
            prescription.save()
        else:
            prescription = Prescription.objects.create(
                appointment=appt,
                medications=request.data.get('medications'),
                instructions=request.data.get('instructions'),
                follow_up_date=follow_up
            )
            
        appt.status = 'completed'
        appt.save()
        
        try:
            send_prescription_email(appt)
        except Exception:
            pass

        return Response({
            'message': 'Prescription saved', 
            'prescription': {
                'id': prescription.id,
                'medications': prescription.medications,
                'instructions': prescription.instructions,
                'follow_up_date': prescription.follow_up_date.isoformat() if prescription.follow_up_date else None,
            }
        }, status=status.HTTP_201_CREATED)


class DoctorFeedbackListView(APIView):
    permission_classes = [IsDoctorUser]

    def get(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        feedbacks = Feedback.objects.filter(doctor=doctor, is_visible=True).order_by('-created_at')
        return Response(FeedbackSerializer(feedbacks, many=True).data, status=status.HTTP_200_OK)


class DoctorProfileView(APIView):
    permission_classes = [IsDoctorUser]

    def get(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DoctorSerializer(doctor).data, status=status.HTTP_200_OK)

    def put(self, request):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        doctor.specialization = request.data.get('specialization', doctor.specialization)
        doctor.qualification = request.data.get('qualification', doctor.qualification)
        doctor.experience_years = request.data.get('experience_years', doctor.experience_years)
        doctor.consultation_fee = request.data.get('consultation_fee', doctor.consultation_fee)
        doctor.bio = request.data.get('bio', doctor.bio)
        doctor.save()

        user = doctor.user
        user.name = request.data.get('name', user.name)
        user.phone = request.data.get('phone', user.phone)
        user.save()
        
        return Response(DoctorSerializer(doctor).data, status=status.HTTP_200_OK)


class DoctorPatientHistoryView(APIView):
    permission_classes = [IsDoctorUser]

    def get(self, request, patient_id):
        doctor = get_doctor(request.user)
        if not doctor:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        appointments = Appointment.objects.filter(
            doctor=doctor, 
            patient_id=patient_id
        ).order_by('-appointment_date')
        return Response(AppointmentSerializer(appointments, many=True).data, status=status.HTTP_200_OK)
