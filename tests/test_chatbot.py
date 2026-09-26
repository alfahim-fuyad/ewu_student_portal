"""
Tests for the chatbot app — intent detection, permission filtering, history.

These tests verify the CORE permission rules:
    ✅ Student can ask about THEIR OWN attendance / results / fees / courses
    ✅ Anyone can ask about public course / department / teacher info
    ❌ Student CANNOT ask about another student's private data
"""
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import User
from students.models import Student
from teachers.models import Teacher
from academics.models import Department, Course, Semester, Enrollment
from attendance.models import Attendance
from results.models import Result
from fees.models import Fee
from notices.models import Notice
from datetime import date
from decimal import Decimal

from chatbot.services import (
    detect_intent,
    asks_about_other_student,
    fetch_allowed_context,
    respond,
)

User = get_user_model()


class IntentDetectionTests(TestCase):
    def test_detect_my_cgpa(self):
        self.assertEqual(detect_intent('what is my CGPA?'), 'my_cgpa')

    def test_detect_my_cgpa_bangla(self):
        self.assertEqual(detect_intent('আমার cgpa কত?'), 'my_cgpa')

    def test_detect_my_attendance(self):
        self.assertEqual(detect_intent('how is my attendance?'), 'my_attendance')

    def test_detect_my_courses(self):
        self.assertEqual(detect_intent('what are my courses?'), 'my_courses')

    def test_detect_public_courses(self):
        self.assertEqual(detect_intent('list all CSE courses'), 'public_courses')

    def test_detect_general(self):
        self.assertEqual(detect_intent('Hello there'), 'general')

    def test_detect_empty_question(self):
        self.assertEqual(detect_intent(''), 'general')


class OtherStudentDetectionTests(TestCase):
    def test_other_student_english(self):
        self.assertTrue(asks_about_other_student('What is Rahim\'s CGPA?'))

    def test_other_student_bangla(self):
        self.assertTrue(asks_about_other_student('Rahim-er CGPA কত?'))

    def test_own_question_not_flagged(self):
        self.assertFalse(asks_about_other_student('What is my CGPA?'))


class PermissionRuleTests(TestCase):
    """
    The hard rules:
        Student asking about another student's private data → BLOCKED.
        Student asking about own data → ALLOWED.
    """

    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025, is_current=True)

        # Student A
        cls.user_a = User.objects.create_user('studA', password='p', role='student', first_name='Stud', last_name='A')
        cls.stu_a = Student.objects.create(user=cls.user_a, student_id='2025-A', department=cls.dept, current_semester=cls.sem)

        # Student B
        cls.user_b = User.objects.create_user('studB', password='p', role='student')
        cls.stu_b = Student.objects.create(user=cls.user_b, student_id='2025-B', department=cls.dept, current_semester=cls.sem)

        # Teacher
        cls.teacher_user = User.objects.create_user('teach', password='p', role='teacher')
        cls.teacher = Teacher.objects.create(user=cls.teacher_user, teacher_id='T1', department=cls.dept)

        cls.course = Course.objects.create(
            course_code='CSE101', title='Intro', department=cls.dept,
            semester=cls.sem, section='A', credits=3, instructor=cls.teacher,
        )
        cls.enroll_a = Enrollment.objects.create(student=cls.stu_a, course=cls.course, semester=cls.sem)
        Attendance.objects.create(enrollment=cls.enroll_a, date=date(2025, 9, 1), status='present')
        Attendance.objects.create(enrollment=cls.enroll_a, date=date(2025, 9, 2), status='absent')

        Result.objects.create(enrollment=cls.enroll_a, marks=Decimal('95'))

        Fee.objects.create(student=cls.stu_a, semester=cls.sem, fee_type='tuition', amount=Decimal('10000'))

    # --- Allow rules ----------------------------------------------------

    def test_student_can_ask_own_cgpa(self):
        r = fetch_allowed_context(self.user_a, 'what is my CGPA?', 'my_cgpa')
        self.assertTrue(r.allowed)
        self.assertIn('cgpa', r.context)

    def test_student_can_ask_own_attendance(self):
        r = fetch_allowed_context(self.user_a, 'my attendance?', 'my_attendance')
        self.assertTrue(r.allowed)
        self.assertEqual(r.context['total_classes'], 2)
        self.assertEqual(r.context['present'], 1)

    def test_student_can_ask_own_fees(self):
        r = fetch_allowed_context(self.user_a, 'my fees?', 'my_fees')
        self.assertTrue(r.allowed)
        self.assertEqual(r.context['unpaid_count'], 1)

    def test_anyone_can_ask_public_courses(self):
        r = fetch_allowed_context(self.user_a, 'CSE courses?', 'public_courses')
        self.assertTrue(r.allowed)
        self.assertIn('departments', r.context)

    # --- Deny rules -----------------------------------------------------

    def test_student_cannot_ask_another_student_cgpa(self):
        r = fetch_allowed_context(self.user_a, 'What is Rahim\'s CGPA?', 'my_cgpa')
        self.assertFalse(r.allowed)
        self.assertEqual(r.context, {})
        self.assertIn('Permission denied', r.reason)

    def test_student_question_is_denied_for_other_student(self):
        # Even if intent is "my_cgpa", when the user mentions another student, blocked
        result = respond(self.user_a, "What is Rahim's CGPA?")
        self.assertFalse(result['allowed'])
        self.assertIn('cannot share', result['reply'].lower())

    def test_anonymous_user_gets_general_context(self):
        from django.contrib.auth.models import AnonymousUser
        r = fetch_allowed_context(AnonymousUser(), 'hello', 'general')
        self.assertTrue(r.allowed)
        self.assertEqual(r.reason, 'anonymous')


class ChatEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025, is_current=True)
        cls.user = User.objects.create_user('stud', password='p', role='student')
        cls.stu = Student.objects.create(user=cls.user, student_id='2025-S', department=cls.dept, current_semester=cls.sem)

    def test_endpoint_requires_login(self):
        c = Client()
        r = c.post(reverse('chatbot:chat'), {'question': 'hi'}, content_type='application/json')
        self.assertEqual(r.status_code, 302)  # redirects to login

    def test_endpoint_rejects_empty_question(self):
        c = Client()
        c.login(username='stud', password='p')
        r = c.post(reverse('chatbot:chat'), {'question': ''}, content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_endpoint_returns_response(self):
        c = Client()
        c.login(username='stud', password='p')
        r = c.post(reverse('chatbot:chat'), {'question': 'Hello'}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('reply', data)
        self.assertIn('intent', data)

    def test_endpoint_denies_other_student_request(self):
        c = Client()
        c.login(username='stud', password='p')
        r = c.post(reverse('chatbot:chat'),
                   {'question': "What is Rahim's CGPA?"},
                   content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data['allowed'])

    def test_history_endpoint(self):
        c = Client()
        c.login(username='stud', password='p')
        # Send a message first
        c.post(reverse('chatbot:chat'), {'question': 'Hello'}, content_type='application/json')
        r = c.get(reverse('chatbot:history'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('history', r.json())


class ChatHistoryModelTests(TestCase):
    def test_chat_history_saved_on_respond(self):
        from chatbot.models import ChatHistory
        user = User.objects.create_user('u', password='p', role='student')
        respond(user, 'Hello there')
        # Two rows: user question + assistant reply
        self.assertEqual(ChatHistory.objects.filter(user=user).count(), 2)
