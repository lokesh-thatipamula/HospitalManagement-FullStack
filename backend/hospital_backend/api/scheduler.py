from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, date
from appointments.models import Appointment
from patients.services.email_service import send_reminder_email

def send_reminders():
    """Send email reminders 24 hours before appointments."""
    tomorrow = date.today() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        appointment_date=tomorrow,
        status='booked',
        reminder_sent=False
    )

    for appt in appointments:
        try:
            send_reminder_email(appt)
            appt.reminder_sent = True
            appt.save()
        except Exception as e:
            print(f"Reminder error for appointment {appt.id}: {e}")
            
    if appointments:
        print(f"✅ Sent {len(appointments)} reminder emails")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=send_reminders,
        trigger='cron',
        hour=9,  # Run daily at 9 AM
        minute=0,
        id='appointment_reminders',
        replace_existing=True,
    )
    try:
        scheduler.start()
        print("✅ Appointment reminder scheduler started")
    except Exception as e:
        print(f"Scheduler error: {e}")
