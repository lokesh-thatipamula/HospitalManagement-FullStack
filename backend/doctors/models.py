from django.db import models
from accounts.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
    specialization = models.CharField(max_length=150, blank=True, null=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    experience_years = models.IntegerField(default=0)
    consultation_fee = models.FloatField(default=0.0)
    bio = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name

    @property
    def avg_rating(self):
        feedbacks = self.feedbacks.all()
        if not feedbacks:
            return 0
        return round(sum(f.rating for f in feedbacks) / len(feedbacks), 1)


class Availability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField()  # 0=Mon, 6=Sun
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(default=30)  # minutes
    is_available = models.BooleanField(default=True)

    def __str__(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = days[self.day_of_week] if 0 <= self.day_of_week <= 6 else str(self.day_of_week)
        return f"{self.doctor.user.name} - {day_name} ({self.start_time} to {self.end_time})"
