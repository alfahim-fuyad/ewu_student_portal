"""
Tests for the attendance app — model + permission-aware attendance viewing.
"""
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import User
from students.models import Student
from teachers.models import Teacher
from academics.models import Department, Course, Semester, Enrollment
from attendance.models import Attendance

User = get_user_model()


class AttendanceModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025)
        cls.stu_user = User.objects.create_user('s1', password='p', role='student')
        cls.stu = Student.objects.create(user=cls.stu_user, student_id='2025-1', department=cls.dept)
        cls.teach_user = User.objects.create_user('t1', password='p', role='teacher')
        cls.teacher = Teacher.objects.create(user=cls.teach_user, teacher_id='T-1', department=cls.dept)
        cls.course = Course.objects.create(
            course_code='CSE101', title='Intro to CSE', department=cls.dept,
            semester=cls.sem, instructor=cls.teacher, section='A', credits=3,
        )
        cls.enroll = Enrollment.objects.create(
            student=cls.stu, course=cls.course, semester=cls.sem,
        )

    def test_attendance_creation(self):
        a = Attendance.objects.create(
            enrollment=self.enroll, date=date(2025, 9, 1),
            status='present', marked_by=self.teach_user,
        )
        self.assertEqual(str(a), f'{self.enroll} — 2025-09-01 (present)')

    def test_unique_per_enrollment_per_date(self):
        Attendance.objects.create(
            enrollment=self.enroll, date=date(2025, 9, 1), status='present'
        )
        with self.assertRaises(Exception):
            Attendance.objects.create(
                enrollment=self.enroll, date=date(2025, 9, 1), status='absent'
            )


class AttendanceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025, is_current=True)
        cls.admin = User.objects.create_user('admin', password='p', role='admin', is_staff=True, is_superuser=True)
        cls.teacher_user = User.objects.create_user('teacher', password='p', role='teacher')
        cls.teacher = Teacher.objects.create(user=cls.teacher_user, teacher_id='T1', department=cls.dept)
        cls.stu_user = User.objects.create_user('student', password='p', role='student')
        cls.student = Student.objects.create(user=cls.stu_user, student_id='2025-S', department=cls.dept)
        cls.course = Course.objects.create(
            course_code='CSE101', title='Intro', department=cls.dept,
            semester=cls.sem, instructor=cls.teacher, section='A', credits=3,
        )
        cls.enroll = Enrollment.objects.create(student=cls.student, course=cls.course, semester=cls.sem)

    def test_student_can_view_list(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('attendance:list'))
        self.assertEqual(r.status_code, 200)

    def test_student_cannot_take_attendance(self):
        self.client.login(username='student', password='p')
        r = self.client.get(reverse('attendance:take', args=[self.course.pk]))
        self.assertEqual(r.status_code, 302)

    def test_teacher_can_take_attendance(self):
        self.client.login(username='teacher', password='p')
        r = self.client.post(reverse('attendance:take', args=[self.course.pk]), {
            'date': '2025-09-26',
            'course': self.course.pk,
            f'student_{self.enroll.pk}': 'present',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Attendance.objects.filter(enrollment=self.enroll, date='2025-09-26').exists())

    def test_report_loads(self):
        self.client.login(username='admin', password='p')
        r = self.client.get(reverse('attendance:report'))
        self.assertEqual(r.status_code, 200)
