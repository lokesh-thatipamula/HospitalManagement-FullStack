from django.db import models
from patients.models import Patient
from doctors.models import Doctor

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    slot_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment: {self.patient.user.name} with {self.doctor.user.name} on {self.appointment_date} at {self.slot_time}"


class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    medications = models.TextField(blank=True, null=True)  # Stored as JSON string potentially
    instructions = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.appointment}"


class Feedback(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='feedback')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='feedbacks')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField()  # 1-5
    comment = models.TextField(blank=True, null=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.doctor.user.name} by {self.patient.user.name} - Rating: {self.rating}"
