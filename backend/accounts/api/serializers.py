from rest_framework import serializers
from accounts.models import User
from doctors.models import Doctor
from patients.models import Patient

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'phone', 'is_active', 'date_joined']
        read_only_fields = ['id', 'is_active', 'date_joined']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # Extra fields for doctor/patient registration
    department_id = serializers.IntegerField(required=False, allow_null=True)
    specialization = serializers.CharField(required=False, max_length=150, allow_blank=True, allow_null=True)
    qualification = serializers.CharField(required=False, max_length=200, allow_blank=True, allow_null=True)
    experience_years = serializers.IntegerField(required=False, allow_null=True)
    consultation_fee = serializers.FloatField(required=False, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(required=False, max_length=10, allow_blank=True, allow_null=True)
    blood_group = serializers.CharField(required=False, max_length=10, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'role', 'phone', 
                  'department_id', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'bio',
                  'gender', 'blood_group', 'address', 'date_of_birth']

    def to_internal_value(self, data):
        # Create a mutable copy of the data
        if hasattr(data, 'copy'):
            data = data.copy()
        else:
            data = dict(data)

        # Convert empty strings to None for fields that expect numbers or dates
        for field in ['department_id', 'experience_years', 'consultation_fee', 'date_of_birth']:
            if field in data and data[field] == '':
                data[field] = None
        return super().to_internal_value(data)

    def create(self, validated_data):
        # Force role to patient for public registration
        role = 'patient'
        user_data = {
            'name': validated_data.get('name'),
            'email': validated_data.get('email'),
            'username': validated_data.get('email'), # using email as username
            'role': role,
            'phone': validated_data.get('phone'),
            'is_active': True
        }
        
        user = User.objects.create(**user_data)
        user.set_password(validated_data.get('password'))
        user.save()

        # Only create patient profile since role is forced to patient
        Patient.objects.create(
            user=user,
            gender=validated_data.get('gender'),
            blood_group=validated_data.get('blood_group'),
            address=validated_data.get('address'),
            date_of_birth=validated_data.get('date_of_birth')
        )
            
        return user


from accounts.models import Notification, Announcement

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at', 'type', 'related_id']


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'target', 'created_at', 'created_by_name']
