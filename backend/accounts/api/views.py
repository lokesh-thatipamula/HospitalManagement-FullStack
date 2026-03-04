from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer
from accounts.models import User, AuditLog, Notification
from accounts.api.serializers import NotificationSerializer
from doctors.models import Doctor
from patients.models import Patient

def log_audit(user, action, resource='auth'):
    AuditLog.objects.create(user=user, action=action, resource=resource)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            error_data = serializer.errors
            # Get the first error message
            first_field = next(iter(error_data))
            first_error = error_data[first_field][0]
            error_msg = str(first_error)
            
            print(f"REGISTRATION FAILED: {error_msg} (Errors: {error_data})")
            return Response({
                'message': error_msg, 
                'errors': error_data
            }, status=status.HTTP_400_BAD_REQUEST)
            
        print(f"REGISTRATION SUCCESS for {serializer.validated_data.get('email')}")
        role = serializer.validated_data.get('role')
        if role not in ('doctor', 'patient'):
            return Response({'message': 'Invalid role for self-registration'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = serializer.save()
        log_audit(user, 'REGISTER')
        
        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'message': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)

        if not user:
            return Response({'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'message': 'Account is deactivated'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        log_audit(user, 'LOGIN')

        user_data = UserSerializer(user).data
        if user.role == 'doctor' and hasattr(user, 'doctor_profile'):
            user_data['doctor_id'] = user.doctor_profile.id
            user_data['is_approved'] = user.doctor_profile.is_approved
        if user.role == 'patient' and hasattr(user, 'patient_profile'):
            user_data['patient_id'] = user.patient_profile.id

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_data
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data
        
        # We simulate the exact Flask responses 
        if user.role == 'doctor' and hasattr(user, 'doctor_profile'):
            profile = user.doctor_profile
            data['profile'] = {
                'id': profile.id,
                'specialization': profile.specialization,
                'qualification': profile.qualification,
                'experience_years': profile.experience_years,
                'consultation_fee': profile.consultation_fee,
                'bio': profile.bio,
                'is_approved': profile.is_approved,
            }
        elif user.role == 'patient' and hasattr(user, 'patient_profile'):
            profile = user.patient_profile
            data['profile'] = {
                'id': profile.id,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                'gender': profile.gender,
                'blood_group': profile.blood_group,
                'address': profile.address,
                'emergency_contact': profile.emergency_contact,
                'medical_history': profile.medical_history,
            }
            
        return Response(data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({'message': 'Incorrect current password'}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch only recent unread notifications, or a mix. 
        # For a bell, typically we want unread, but we can fetch top 50
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
        return Response(NotificationSerializer(notifications, many=True).data, status=status.HTTP_200_OK)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notif_id):
        try:
            notif = Notification.objects.get(id=notif_id, user=request.user)
            notif.is_read = True
            notif.save()
            return Response({'message': 'Marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        return self._mark_all_read(request)

    def post(self, request):
        return self._mark_all_read(request)

    def _mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)
