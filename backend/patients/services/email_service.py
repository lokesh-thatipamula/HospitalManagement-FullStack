from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading
from django.conf import settings

def send_async_email(subject, body, from_email, recipient_list, html_message):
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        print(f"Email error: {e}")

def send_email(to, subject, body, html=None):
    from_email = settings.DEFAULT_FROM_EMAIL
    thread = threading.Thread(
        target=send_async_email, 
        args=(subject, body, from_email, [to], html)
    )
    thread.daemon = True
    thread.start()


# ─── Email Templates ──────────────────────────────────────────────────────────

def send_registration_email(user):
    subject = "Welcome to MediCare Hospital Portal"
    body = f"""
Dear {user.name},

Thank you for registering with MediCare Hospital Portal.

Your account has been created successfully with the email: {user.email}
Role: {user.role.capitalize()}

You can now log in and start using the portal.

Best regards,
MediCare Team
"""
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#1e40af;padding:20px;border-radius:8px 8px 0 0">
    <h2 style="color:white;margin:0">🏥 MediCare Hospital Portal</h2>
  </div>
  <div style="padding:24px;border:1px solid #e5e7eb;border-radius:0 0 8px 8px">
    <p>Dear <strong>{user.name}</strong>,</p>
    <p>Welcome to MediCare Hospital Portal! Your account has been created.</p>
    <table style="background:#f0f9ff;padding:16px;border-radius:8px;width:100%">
      <tr><td><strong>Email:</strong></td><td>{user.email}</td></tr>
      <tr><td><strong>Role:</strong></td><td>{user.role.capitalize()}</td></tr>
    </table>
    <p style="margin-top:20px">Best regards,<br><strong>MediCare Team</strong></p>
  </div>
</div>
"""
    send_email(user.email, subject, body, html)


def send_appointment_confirmation(appointment):
    patient = appointment.patient
    doctor = appointment.doctor
    if not patient or not patient.user or not doctor or not doctor.user:
        return
    
    # Basic check for a "real" looking email (contains @ and .)
    if '@' not in patient.user.email or '.' not in patient.user.email:
        print(f"Skipping email to invalid address: {patient.user.email}")
        return

    subject = f"Appointment Confirmation: {appointment.appointment_date} — Antigravity Hospital"
    
    body = f"""
Dear {patient.user.name},

This is an official confirmation of your upcoming medical appointment at Antigravity Hospital.

Appointment Details:
-------------------
Reference ID: #APT-{appointment.id}
Practitioner: Dr. {doctor.user.name}
Department: {doctor.department.name if doctor.department else 'General Medicine'}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Scheduled Time: {appointment.slot_time.strftime('%I:%M %p')}
Reason for Visit: {appointment.reason or 'Scheduled Consultation'}

Instructions for Patients:
1. Please arrive at the facility at least 15 minutes prior to your scheduled time for registration.
2. Ensure you have your identification and any previous medical records relevant to this visit.
3. If you need to reschedule or cancel, please do so through the patient portal at least 24 hours in advance.

Thank you for choosing Antigravity Hospital for your healthcare needs.

Regards,

The Administration Team
Antigravity Hospital Technical Services
"""

    html = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; color: #1e293b; line-height: 1.6;">
  <div style="background: #1e40af; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px; letter-spacing: 1px;">ANTIGRAVITY HOSPITAL</h1>
    <p style="color: #bfdbfe; margin: 10px 0 0 0; font-size: 14px; font-weight: 500;">Official Appointment Confirmation</p>
  </div>
  
  <div style="padding: 40px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; background: #ffffff;">
    <p style="font-size: 16px;">Dear <strong>{patient.user.name}</strong>,</p>
    <p>This is a formal confirmation of your scheduled appointment. Please find the clinical details below:</p>
    
    <div style="background: #f8fafc; padding: 25px; border-radius: 12px; margin: 25px 0; border: 1px solid #f1f5f9;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Practitioner</td>
          <td style="padding: 8px 0; color: #0f172a; font-weight: 600;">Dr. {doctor.user.name}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Department</td>
          <td style="padding: 8px 0; color: #0f172a;">{doctor.department.name if doctor.department else 'General Medicine'}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Date</td>
          <td style="padding: 8px 0; color: #0f172a;">{appointment.appointment_date.strftime('%B %d, %Y')}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Time</td>
          <td style="padding: 8px 0; color: #0f172a;">{appointment.slot_time.strftime('%I:%M %p')}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Ref ID</td>
          <td style="padding: 8px 0; color: #0f172a; font-family: monospace;">#APT-{appointment.id}</td>
        </tr>
      </table>
    </div>
    
    <h3 style="font-size: 14px; text-transform: uppercase; color: #1e40af; margin-bottom: 15px;">Patient Instructions</h3>
    <ul style="padding-left: 20px; font-size: 14px; color: #475569;">
      <li style="margin-bottom: 8px;">Please arrive 15 minutes before your scheduled appointment time.</li>
      <li style="margin-bottom: 8px;">Kindly carry a valid form of identification.</li>
      <li style="margin-bottom: 8px;">Bring any previous medical reports or diagnostic results.</li>
    </ul>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 13px; color: #94a3b8; text-align: center;">
      This is an automated message from Antigravity Hospital Systems.<br>
      Please do not reply to this email.
    </p>
  </div>
</div>
"""
    send_email(patient.user.email, subject, body, html)


def send_cancellation_email(appointment):
    patient = appointment.patient
    doctor = appointment.doctor
    if not patient or not patient.user or not doctor or not doctor.user:
        return
    
    # Basic check for a "real" looking email
    if '@' not in patient.user.email or '.' not in patient.user.email:
        return

    subject = f"Appointment Cancellation: #APT-{appointment.id} — Antigravity Hospital"
    
    body = f"""
Dear {patient.user.name},

This is an official notification regarding the cancellation of your scheduled appointment at Antigravity Hospital.

Cancelled Appointment Details:
-----------------------------
Reference ID: #APT-{appointment.id}
Practitioner: Dr. {doctor.user.name}
Department: {doctor.department.name if doctor.department else 'General Medicine'}
Original Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Scheduled Time: {appointment.slot_time.strftime('%I:%M %p')}

We apologize for any inconvenience this may cause. If you wish to reschedule your visit, please log in to the Antigravity Hospital Patient Portal to view available slots.

If you have any urgent medical concerns, please contact our emergency department immediately.

Regards,

The Administration Team
Antigravity Hospital Technical Services
"""

    html = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; color: #1e293b; line-height: 1.6;">
  <div style="background: #ef4444; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 24px; letter-spacing: 1px;">ANTIGRAVITY HOSPITAL</h1>
    <p style="color: #fee2e2; margin: 10px 0 0 0; font-size: 14px; font-weight: 500;">Official Cancellation Notification</p>
  </div>
  
  <div style="padding: 40px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; background: #ffffff;">
    <p style="font-size: 16px;">Dear <strong>{patient.user.name}</strong>,</p>
    <p>This is a formal notification that your scheduled appointment has been cancelled. Details of the cancelled session are provided below:</p>
    
    <div style="background: #fffbfa; padding: 25px; border-radius: 12px; margin: 25px 0; border: 1px solid #fef2f2;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 8px 0; color: #991b1b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Practitioner</td>
          <td style="padding: 8px 0; color: #0f172a; font-weight: 600;">Dr. {doctor.user.name}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #991b1b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Date</td>
          <td style="padding: 8px 0; color: #0f172a;">{appointment.appointment_date.strftime('%B %d, %Y')}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #991b1b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Time</td>
          <td style="padding: 8px 0; color: #0f172a;">{appointment.slot_time.strftime('%I:%M %p')}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #991b1b; font-size: 13px; font-weight: 600; text-transform: uppercase;">Ref ID</td>
          <td style="padding: 8px 0; color: #0f172a; font-family: monospace;">#APT-{appointment.id}</td>
        </tr>
      </table>
    </div>
    
    <p style="font-size: 14px; color: #475569;">To reschedule this appointment, please visit the portal or contact our reception desk during business hours.</p>
    
    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
    
    <p style="font-size: 13px; color: #94a3b8; text-align: center;">
      This is an automated message from Antigravity Hospital Systems.<br>
      Please do not reply to this email.
    </p>
  </div>
</div>
"""
    send_email(patient.user.email, subject, body, html)


def send_reminder_email(appointment):
    patient = appointment.patient
    doctor = appointment.doctor
    if not patient or not patient.user or not doctor or not doctor.user:
        return
    subject = "Appointment Reminder — MediCare (24 hours)"
    body = f"Reminder: Your appointment with Dr. {doctor.user.name} is tomorrow at {appointment.slot_time}."
    send_email(patient.user.email, subject, body)


def send_prescription_email(appointment):
    patient = appointment.patient
    if not patient or not patient.user:
        return
    subject = "Prescription Available — MediCare"
    body = f"Dear {patient.user.name},\n\nYour prescription from your appointment on {appointment.appointment_date} is now available in the portal.\n\nMediCare Team"
    send_email(patient.user.email, subject, body)
