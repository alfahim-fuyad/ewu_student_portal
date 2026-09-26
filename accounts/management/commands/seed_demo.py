"""
Seed demo data for the Student Portal.

Usage:
    python manage.py seed_demo

This creates:
    - 1 admin user (admin / admin)
    - 2 teachers (teacher1 / teacher1, teacher2 / teacher2)
    - 3 students (student1 / student1, student2 / student2, student3 / student3)
    - 1 department (CSE)
    - 1 current semester (Fall 2025)
    - 3 courses
    - Enrollments + attendance + results + fees + notices
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import User
from students.models import Student
from teachers.models import Teacher
from academics.models import Department, Course, Semester, Enrollment
from attendance.models import Attendance
from results.models import Result
from fees.models import Fee
from notices.models import Notice

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with demo data for development.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding demo data...'))

        # ---- Users ----
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'password': 'admin',
                'email': 'admin@example.com',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User',
            },
        )
        if not admin.check_password('admin'):
            admin.set_password('admin')
            admin.save()

        teacher_user1, _ = User.objects.get_or_create(
            username='teacher1',
            defaults={'email': 't1@example.com', 'role': User.Role.TEACHER, 'first_name': 'T1', 'last_name': 'Faculty'},
        )
        teacher_user1.set_password('teacher1')
        teacher_user1.save()

        teacher_user2, _ = User.objects.get_or_create(
            username='teacher2',
            defaults={'email': 't2@example.com', 'role': User.Role.TEACHER, 'first_name': 'T2', 'last_name': 'Faculty'},
        )
        teacher_user2.set_password('teacher2')
        teacher_user2.save()

        student_users_data = [
            ('student1', 'S1', 'Student'),
            ('student2', 'S2', 'Student'),
            ('student3', 'S3', 'Student'),
        ]
        student_users = []
        for username, first, last in student_users_data:
            u, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com', 'role': User.Role.STUDENT,
                          'first_name': first, 'last_name': last},
            )
            u.set_password(username)
            u.save()
            student_users.append(u)

        # ---- Department + semester ----
        dept, _ = Department.objects.get_or_create(
            code='CSE',
            defaults={'name': 'Department of Computer Science & Engineering', 'is_active': True},
        )
        sem, _ = Semester.objects.get_or_create(
            term='fall', year=2025,
            defaults={'is_current': True, 'start_date': date(2025, 9, 1), 'end_date': date(2026, 1, 15)},
        )

        # ---- Teachers ----
        t1, _ = Teacher.objects.get_or_create(
            teacher_id='T-001', defaults={'user': teacher_user1, 'department': dept, 'designation': 'asst_prof', 'specialization': 'Algorithms'},
        )
        t2, _ = Teacher.objects.get_or_create(
            teacher_id='T-002', defaults={'user': teacher_user2, 'department': dept, 'designation': 'lecturer', 'specialization': 'Databases'},
        )

        # ---- Students ----
        student_data = [
            ('2025-001', student_users[0]),
            ('2025-002', student_users[1]),
            ('2025-003', student_users[2]),
        ]
        students = []
        for sid, user in student_data:
            s, _ = Student.objects.get_or_create(
                student_id=sid,
                defaults={'user': user, 'department': dept, 'current_semester': sem,
                          'program': Student.Program.BSC_CSE, 'batch': '2025-26',
                          'admission_date': date(2025, 9, 1)},
            )
            students.append(s)

        # ---- Courses ----
        courses_data = [
            ('CSE110', 'Programming Language I', t1, 3, 'A'),
            ('CSE111', 'Programming Language I Lab', t1, 1, 'A'),
            ('CSE220', 'Data Structures', t2, 3, 'A'),
        ]
        courses = []
        for code, title, instructor, credits, section in courses_data:
            c, _ = Course.objects.get_or_create(
                course_code=code, section=section, semester=sem,
                defaults={'title': title, 'department': dept, 'credits': Decimal(credits),
                          'instructor': instructor, 'is_active': True,
                          'schedule': 'Sun-Tue-Thu 10:00-11:30', 'room': 'A-201'},
            )
            courses.append(c)

        # ---- Enrollments + attendance + results ----
        for s in students:
            for c in courses:
                e, created = Enrollment.objects.get_or_create(
                    student=s, course=c, semester=sem,
                    defaults={'status': 'enrolled'},
                )
                if created:
                    # Mark attendance for 4 random past dates
                    for i in range(4):
                        Attendance.objects.get_or_create(
                            enrollment=e,
                            date=date.today() - timedelta(days=i*2),
                            defaults={'status': 'present' if i % 3 != 0 else 'absent',
                                      'marked_by': teacher_user1},
                        )

        # Create results for 1 student on first course
        Result.objects.update_or_create(
            enrollment=Enrollment.objects.get(student=students[0], course=courses[0]),
            defaults={'marks': Decimal('85'), 'is_published': True},
        )
        Result.objects.update_or_create(
            enrollment=Enrollment.objects.get(student=students[1], course=courses[0]),
            defaults={'marks': Decimal('72'), 'is_published': True},
        )

        # ---- Fees ----
        for s in students:
            Fee.objects.get_or_create(
                student=s, semester=sem, fee_type='tuition',
                defaults={'amount': Decimal('45000'), 'status': 'unpaid',
                          'description': 'Fall 2025 tuition', 'due_date': date(2025, 10, 15)},
            )

        # ---- Notices ----
        Notice.objects.get_or_create(
            title='Welcome to the Student Portal!',
            defaults={
                'body': 'Welcome to your new university student portal. Use the floating 🤖 button at the bottom-right to ask the AI Assistant about your courses, CGPA, attendance, or fees.',
                'audience': 'all', 'is_pinned': True, 'is_active': True,
                'posted_by': admin,
            },
        )
        Notice.objects.get_or_create(
            title='Mid-term exam schedule published',
            defaults={
                'body': 'The mid-term examination schedule has been published. Check your course pages for date and room details.',
                'audience': 'student', 'is_active': True, 'posted_by': admin,
            },
        )
        Notice.objects.get_or_create(
            title='CSE department seminar — Friday 3 PM',
            defaults={
                'body': 'A research seminar will be held in the main auditorium this Friday at 3 PM. All CSE students are welcome.',
                'audience': 'department', 'department': dept, 'is_active': True,
                'posted_by': admin,
            },
        )

        # Done
        self.stdout.write(self.style.SUCCESS(
            '\n✅ Seed complete!\n'
            f'  Users:  {User.objects.count()}\n'
            f'  Teachers: {Teacher.objects.count()}\n'
            f'  Students: {Student.objects.count()}\n'
            f'  Courses:  {Course.objects.count()}\n'
            f'  Notices:  {Notice.objects.count()}\n\n'
            'Demo logins (password = username):\n'
            '  admin / admin\n'
            '  teacher1 / teacher1\n'
            '  student1 / student1\n'
            '  student2 / student2\n'
            '  student3 / student3'
        ))
