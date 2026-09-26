"""
Tests for the accounts app — login/logout, role-based access, profile updates.

Run:  python manage.py test tests.test_accounts
"""
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import User

User = get_user_model()


class BaseDataMixin:
    """Common setup for accounts tests."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='admin', password='adminpass',
            email='admin@example.com', role=User.Role.ADMIN,
            is_staff=True, is_superuser=True,
        )
        cls.teacher_user = User.objects.create_user(
            username='teacher', password='teacherpass',
            email='teacher@example.com', role=User.Role.TEACHER,
        )
        cls.student_user = User.objects.create_user(
            username='student', password='studentpass',
            email='student@example.com', role=User.Role.STUDENT,
        )


class LoginViewTests(BaseDataMixin, TestCase):
    def test_login_page_loads(self):
        c = Client()
        r = c.get(reverse('accounts:login'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Sign in')

    def test_student_can_login(self):
        c = Client()
        r = c.post(reverse('accounts:login'), {
            'username': 'student', 'password': 'studentpass',
        })
        self.assertRedirects(r, reverse('dashboard'))

    def test_admin_can_login(self):
        c = Client()
        r = c.post(reverse('accounts:login'), {
            'username': 'admin', 'password': 'adminpass',
        })
        self.assertRedirects(r, reverse('dashboard'))

    def test_invalid_login_rejected(self):
        c = Client()
        r = c.post(reverse('accounts:login'), {
            'username': 'student', 'password': 'wrongpassword',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'enter a correct username')

    def test_logout_redirects_to_login(self):
        c = Client()
        c.login(username='student', password='studentpass')
        r = c.get(reverse('accounts:logout'))
        self.assertRedirects(r, reverse('accounts:login'))


class RoleAccessTests(BaseDataMixin, TestCase):
    def test_dashboard_requires_login(self):
        c = Client()
        r = c.get(reverse('dashboard'))
        self.assertRedirects(r, f"{reverse('accounts:login')}?next={reverse('dashboard')}")

    def test_student_role_flag(self):
        self.assertTrue(self.student_user.is_student)
        self.assertFalse(self.student_user.is_teacher)
        self.assertFalse(self.student_user.is_admin_role)

    def test_teacher_role_flag(self):
        self.assertTrue(self.teacher_user.is_teacher)
        self.assertFalse(self.teacher_user.is_student)

    def test_admin_role_flag(self):
        self.assertTrue(self.admin.is_admin_role)


class ProfileViewTests(BaseDataMixin, TestCase):
    def test_student_can_view_own_profile(self):
        c = Client()
        c.login(username='student', password='studentpass')
        r = c.get(reverse('accounts:profile'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'student@example.com')

    def test_student_can_update_first_name(self):
        c = Client()
        c.login(username='student', password='studentpass')
        r = c.post(reverse('accounts:profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'student@example.com',
            'phone': '',
            'address': '',
            'date_of_birth': '',
            'bio': '',
        })
        self.assertRedirects(r, reverse('accounts:profile'))
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'Updated')


class ForgotPasswordTests(TestCase):
    def test_form_loads(self):
        c = Client()
        r = c.get(reverse('accounts:forgot_password'))
        self.assertEqual(r.status_code, 200)

    def test_unknown_email_returns_error(self):
        c = Client()
        r = c.post(reverse('accounts:forgot_password'), {'email': 'nonexistent@example.com'})
        # The form should re-render with an error
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No account found')
