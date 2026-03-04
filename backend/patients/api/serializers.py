from rest_framework import serializers
from patients.models import Patient, Vital, MedicalDocument

class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = ['id', 'heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'temperature', 'weight', 'recorded_at']

class MedicalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalDocument
        fields = ['id', 'name', 'file_url', 'size', 'doc_type', 'uploaded_at']

class PatientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'date_of_birth', 'gender', 'blood_group', 'address', 'emergency_contact', 
            'medical_history', 'name', 'email', 'phone', 'is_active'
        ]
