from rest_framework import serializers
from appointments.models import Appointment, Prescription, Feedback

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'medications', 'instructions', 'follow_up_date', 'created_at']

class FeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'rating', 'comment', 'is_visible', 'created_at', 'patient_name', 'doctor_name']

class AppointmentSerializer(serializers.ModelSerializer):
    slot_time = serializers.TimeField(format='%H:%M')
    doctor = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    prescription = PrescriptionSerializer(read_only=True)
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_date', 'slot_time', 'status', 'reason', 'notes', 
            'created_at', 'doctor', 'patient', 'prescription', 'feedback'
        ]

    def get_doctor(self, obj):
        if not obj.doctor:
            return None
        return {
            'id': obj.doctor.id,
            'name': obj.doctor.user.name if obj.doctor.user else None,
            'specialization': obj.doctor.specialization,
            'department': obj.doctor.department.name if obj.doctor.department else None,
        }

    def get_patient(self, obj):
        if not obj.patient:
            return None
        return {
            'id': obj.patient.id,
            'name': obj.patient.user.name if obj.patient.user else None,
            'email': obj.patient.user.email if obj.patient.user else None,
        }
