from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, ProfileView, ChangePasswordView,
    NotificationListView, NotificationReadView, NotificationReadAllView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='auth-register'),
    path('login', LoginView.as_view(), name='auth-login'),
    path('refresh', TokenRefreshView.as_view(), name='auth-refresh'),
    path('me', ProfileView.as_view(), name='auth-me'),
    path('change-password', ChangePasswordView.as_view(), name='auth-change-password'),
    path('notifications', NotificationListView.as_view(), name='auth-notifications'),
    path('notifications/<int:notif_id>/read', NotificationReadView.as_view(), name='auth-notification-read'),
    path('notifications/read-all', NotificationReadAllView.as_view(), name='auth-notifications-read-all'),
]
