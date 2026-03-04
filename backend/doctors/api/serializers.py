from rest_framework import serializers
from doctors.models import Department, Doctor, Availability

class DepartmentSerializer(serializers.ModelSerializer):
    doctor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'doctor_count', 'created_at']
        
    def get_doctor_count(self, obj):
        return obj.doctors.count()

class AvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()
    start_time = serializers.TimeField(format='%H:%M')
    end_time = serializers.TimeField(format='%H:%M')

    class Meta:
        model = Availability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'slot_duration', 'is_available']
        
    def get_day_name(self, obj):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if 0 <= obj.day_of_week <= 6:
            return days[obj.day_of_week]
        return ''

class DoctorSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 
            'bio', 'is_approved', 'avg_rating', 'name', 'email', 'phone', 'is_active', 'department'
        ]
        
    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr['total_feedback'] = instance.feedbacks.count()
        return repr
