"""
Tests for the teachers app — model + admin-only access rules.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import User
from teachers.models import Teacher
from academics.models import Department

User = get_user_model()


class TeacherModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='EEE', name='Department of EEE')
        cls.user = User.objects.create_user(
            username='teach1', password='pass123',
            email='teach1@example.com', role=User.Role.TEACHER,
        )
        cls.teacher = Teacher.objects.create(
            user=cls.user, teacher_id='T-001',
            department=cls.dept, designation=Teacher.Designation.LECTURER,
        )

    def test_str(self):
        self.assertIn('T-001', str(self.teacher))

    def test_unique_teacher_id(self):
        u2 = User.objects.create_user(
            username='teach2', password='pass123',
            email='teach2@example.com', role=User.Role.TEACHER,
        )
        with self.assertRaises(Exception):
            Teacher.objects.create(user=u2, teacher_id='T-001', department=self.dept)


class TeacherViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin', password='pass123',
            role=User.Role.ADMIN, is_staff=True, is_superuser=True,
        )
        cls.teacher = User.objects.create_user(
            username='teacher', password='pass123', role=User.Role.TEACHER,
        )
        cls.student = User.objects.create_user(
            username='student', password='pass123', role=User.Role.STUDENT,
        )

    def test_list_requires_login(self):
        r = self.client.get(reverse('teachers:list'))
        self.assertEqual(r.status_code, 302)

    def test_student_can_see_list(self):
        self.client.login(username='student', password='pass123')
        r = self.client.get(reverse('teachers:list'))
        self.assertEqual(r.status_code, 200)

    def test_student_cannot_add_teacher(self):
        self.client.login(username='student', password='pass123')
        r = self.client.get(reverse('teachers:add'))
        self.assertEqual(r.status_code, 302)

    def test_admin_can_add_teacher(self):
        self.client.login(username='admin', password='pass123')
        new_user = User.objects.create_user(
            username='newteach', password='pass123',
            email='newt@example.com', role=User.Role.TEACHER,
        )
        dept = Department.objects.create(code='CSE', name='CSE')
        r = self.client.post(reverse('teachers:add'), {
            'user': new_user.pk,
            'teacher_id': 'T-100',
            'department': dept.pk,
            'designation': 'lecturer',
            'is_active': 'on',
        })
        self.assertRedirects(r, reverse('teachers:list'))
        self.assertTrue(Teacher.objects.filter(teacher_id='T-100').exists())
