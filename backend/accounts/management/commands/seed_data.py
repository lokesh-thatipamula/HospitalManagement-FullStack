import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, AuditLog, SystemConfig
from doctors.models import Department, Doctor, Availability
from patients.models import Patient
from appointments.models import Appointment, Feedback, Prescription

class Command(BaseCommand):
    help = 'Seeds the database with dummy data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 0. Admin User
        admin_email = 'admin@hospital.com'
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': admin_email,
                'name': 'Admin',
                'role': 'admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin@hospital.com'))
        else:
            admin_user.name = 'Admin'
            admin_user.save()
            self.stdout.write('Admin user already exists, updated name to Admin')

        # 1. Departments
        departments = []
        dept_names = ['Cardiology', 'Neurology', 'Pediatrics', 'Orthopedics', 'Dermatology', 
                      'Gastroenterology', 'Oncology', 'Psychiatry', 'Radiology', 'Emergency']
        for name in dept_names:
            dept, created = Department.objects.get_or_create(name=name, defaults={'description': f'Expert care in {name}'})
            departments.append(dept)
        self.stdout.write(f'Created {len(departments)} departments')

        # 2. Users and Doctors
        doctors = []
        doctor_names = [
            'Gregory House', 'Meredith Grey', 'Shaun Murphy', 'Stephen Strange', 
            'Doogie Howser', 'John Dolittle', 'Leonard McCoy', 'Dana Scully', 
            'James Wilson', 'Lisa Cuddy', 'Derek Shepherd', 'Cristina Yang',
            'Alex Karev', 'Izzie Stevens', 'George O\'Malley', 'Miranda Bailey',
            'Richard Webber', 'Callie Torres', 'Arizona Robbins', 'Mark Sloan'
        ]
        
        for i, name in enumerate(doctor_names):
            email = f'doctor{i}@hospital.com'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'name': f'Dr. {name}',
                    'role': 'doctor',
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            else:
                user.name = f'Dr. {name}'
                user.save()
            
            doctor, created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'department': random.choice(departments),
                    'specialization': random.choice(['Cardiology', 'Neurology', 'Surgery', 'Pediatrics', 'Oncology', 'Dermatology']),
                    'qualification': 'MBBS, MD',
                    'experience_years': random.randint(5, 30),
                    'consultation_fee': float(random.randint(100, 1000)),
                    'bio': f'Dr. {name} is a renowned specialist dedicated to patient-centered care and clinical innovation.',
                    'is_approved': True,
                }
            )
            doctors.append(doctor)
        self.stdout.write(f'Created/Updated {len(doctors)} doctors')
        
        # 3. Users and Patients
        patients = []
        patient_names = [
            'Alice Johnson', 'Bob Williams', 'Charlie Brown', 'Diana Prince', 'Ethan Hunt',
            'Fiona Gallagher', 'George Costanza', 'Hannah Abbott', 'Ian Malcolm', 'Jane Doe',
            'Kevin Hart', 'Lara Croft', 'Michael Scott', 'Nancy Wheeler', 'Oliver Twist',
            'Peter Parker', 'Quentin Coldwater', 'Rachel Green', 'Steve Rogers', 'Tony Stark',
            'Ursula Buffay', 'Victor Von Doom', 'Wanda Maximoff', 'Xena Warrior', 'Yennefer Vengerberg',
            'Zoe Washburne', 'Arthur Dent', 'Bilbo Baggins', 'Clara Oswald', 'David Tennant'
        ]
        
        for i, name in enumerate(patient_names):
            email = f'patient{i}@example.com'
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'name': name,
                    'role': 'patient',
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            else:
                user.name = name
                user.save()
            
            patient, created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'date_of_birth': datetime.now().date() - timedelta(days=random.randint(5000, 30000)),
                    'gender': random.choice(['male', 'female', 'other']),
                    'blood_group': random.choice(['A+', 'B+', 'O+', 'AB+', 'O-', 'A-', 'B-', 'AB-']),
                    'address': f'{random.randint(1, 999)} Health Ave, Medical City',
                }
            )
            patients.append(patient)
        self.stdout.write(f'Created/Updated {len(patients)} patients')

        # 4. Availabilities
        for doc in doctors:
            for day in range(7): # Mon-Sun
                Availability.objects.get_or_create(
                    doctor=doc,
                    day_of_week=day,
                    defaults={
                        'start_time': '08:00:00',
                        'end_time': '20:00:00',
                        'slot_duration': 30,
                        'is_available': True
                    }
                )
        self.stdout.write('Created availabilities for doctors')

        # 5. Appointments, Feedbacks, Prescriptions
        feedback_comments = [
            "Excellent care and very professional staff.", "Short wait time, doctor was very thorough.",
            "The facilities are top-notch. Highly recommend.", "Great experience!",
            "Very knowledgeable doctor, explained everything clearly.", "Nurse was extremely kind and helpful.",
            "Smooth appointment process and friendly reception.", "Glad I chose this hospital.",
            "Superior treatment plan.", "Compassionate care during a difficult time.",
            "Very clean environment and modern equipment.", "Doctor took the time to answer all my questions.",
            "Easy to book an appointment.", "Great follow-up care.", "I felt very safe.",
            "The prescription was sent immediately.", "Wonderful bedside manner.",
            "Highest level of professionalism.", "Efficient and effective treatment.",
            "A world-class medical facility.", "Very impressed with the personalized care."
        ]

        # Past Appointments (100)
        for i in range(100):
            doc = random.choice(doctors)
            pat = random.choice(patients)
            days_ago = random.randint(1, 180)
            appt_date = datetime.now().date() - timedelta(days=days_ago)
            
            appt = Appointment.objects.create(
                patient=pat,
                doctor=doc,
                appointment_date=appt_date,
                slot_time=f"{random.randint(8, 19):02d}:{random.choice(['00', '30'])}:00",
                status='completed',
                reason=random.choice(['Routine Checkup', 'Follow-up', 'Consultation', 'Emergency', 'General Exam'])
            )

            Feedback.objects.create(
                appointment=appt,
                patient=pat,
                doctor=doc,
                rating=random.randint(4, 5),
                comment=random.choice(feedback_comments),
                is_visible=True
            )
            
            Prescription.objects.create(
                appointment=appt,
                medications=random.choice(['Amoxicillin', 'Paracetamol', 'Ibuprofen', 'Pantoprazole', 'Vitamin C']),
                instructions='Take twice daily after meals'
            )

        # Future Appointments (50)
        for i in range(50):
            doc = random.choice(doctors)
            pat = random.choice(patients)
            days_ahead = random.randint(0, 30)
            appt_date = datetime.now().date() + timedelta(days=days_ahead)
            
            Appointment.objects.create(
                patient=pat,
                doctor=doc,
                appointment_date=appt_date,
                slot_time=f"{random.randint(8, 19):02d}:{random.choice(['00', '30'])}:00",
                status='booked',
                reason=random.choice(['Consultation', 'Regular Visit', 'Scheduled Surgery'])
            )

        self.stdout.write('Created 150 diverse appointments with feedback and prescriptions')

        # 6. Audit Logs
        actions = ['LOGIN', 'REGISTER', 'APPOINTMENT_CREATE', 'PROFILE_UPDATE', 'SETTINGS_CHANGE', 'LOGOUT']
        for i in range(50):
            AuditLog.objects.create(
                user=random.choice(User.objects.all()),
                action=random.choice(actions),
                resource=random.choice(['Dashboard', 'Profile', 'Appointments', 'System'])
            )
        self.stdout.write('Created 50 audit logs')

        # 7. System Config
        configs = [
            ('hospital_name', 'MediCare Global'),
            ('contact_email', 'support@medicare.com'),
            ('maintenance_mode', 'false'),
            ('max_appointments_per_day', '100'),
            ('currency', 'USD'),
            ('theme', 'dark'),
            ('api_version', 'v1'),
            ('footer_text', '© 2026 MediCare Global'),
            ('logo_url', '/static/logo.png'),
            ('terms_version', '1.0')
        ]
        for key, val in configs:
            SystemConfig.objects.get_or_create(key=key, defaults={'value': val})
        self.stdout.write(f'Created system configurations')

        self.stdout.write(self.style.SUCCESS('Successfully seeded volume dummy data!'))
