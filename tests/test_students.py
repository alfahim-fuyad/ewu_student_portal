"""
Tests for the students app — Student model + views + permission enforcement.
"""
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import User
from students.models import Student
from academics.models import Department, Semester

User = get_user_model()


class StudentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='Department of CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025, is_current=True)
        cls.user = User.objects.create_user(
            username='stud1', password='pass123',
            email='stud1@example.com', role=User.Role.STUDENT,
        )
        cls.student = Student.objects.create(
            user=cls.user, student_id='2025-001',
            department=cls.dept, current_semester=cls.sem,
        )

    def test_student_str(self):
        s = str(self.student)
        self.assertIn('2025-001', s)

    def test_student_full_name(self):
        self.user.first_name = 'Test'
        self.user.last_name = 'Student'
        self.user.save()
        self.assertEqual(self.student.full_name, 'Test Student')

    def test_unique_student_id(self):
        from django.db import IntegrityError
        user2 = User.objects.create_user(
            username='stud2', password='pass123',
            email='stud2@example.com', role=User.Role.STUDENT,
        )
        with self.assertRaises(Exception):
            Student.objects.create(user=user2, student_id='2025-001')


class StudentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025)
        cls.admin = User.objects.create_user(
            username='admin', password='pass123',
            role=User.Role.ADMIN, is_staff=True, is_superuser=True,
        )
        cls.teacher = User.objects.create_user(
            username='teacher', password='pass123',
            role=User.Role.TEACHER,
        )
        cls.student_user = User.objects.create_user(
            username='student', password='pass123',
            role=User.Role.STUDENT,
        )
        cls.student = Student.objects.create(
            user=cls.student_user, student_id='2025-100',
            department=cls.dept, current_semester=cls.sem,
        )

    def test_student_list_requires_login(self):
        r = self.client.get(reverse('students:list'))
        self.assertEqual(r.status_code, 302)

    def test_student_list_for_admin(self):
        self.client.login(username='admin', password='pass123')
        r = self.client.get(reverse('students:list'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '2025-100')

    def test_student_cannot_access_add(self):
        self.client.login(username='student', password='pass123')
        r = self.client.get(reverse('students:add'))
        # Student should be redirected away
        self.assertEqual(r.status_code, 302)

    def test_admin_can_create_student(self):
        self.client.login(username='admin', password='pass123')
        u = User.objects.create_user(
            username='newstudent', password='pass123',
            email='new@example.com', role=User.Role.STUDENT,
        )
        r = self.client.post(reverse('students:add'), {
            'user': u.pk,
            'student_id': '2025-200',
            'department': self.dept.pk,
            'program': 'BSC_CSE',
            'batch': '2025-26',
            'is_active': 'on',
            'address': '',
            'guardian_name': '',
            'guardian_phone': '',
        })
        self.assertRedirects(r, reverse('students:list'))
        self.assertTrue(Student.objects.filter(student_id='2025-200').exists())
