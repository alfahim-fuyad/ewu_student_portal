"""
Tests for the results app — model + GPA/CGPA computation logic.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import User
from students.models import Student
from teachers.models import Teacher
from academics.models import Department, Course, Semester, Enrollment
from results.models import Result, compute_gpa, compute_cgpa, grade_for_mark

User = get_user_model()


class GradeLogicTests(TestCase):
    def test_grade_for_mark_a_plus(self):
        letter, point = grade_for_mark(Decimal('95'))
        self.assertEqual(letter, 'A+')
        self.assertEqual(point, Decimal('4.00'))

    def test_grade_for_mark_f(self):
        letter, point = grade_for_mark(Decimal('40'))
        self.assertEqual(letter, 'F')
        self.assertEqual(point, Decimal('0.00'))

    def test_grade_for_mark_boundary(self):
        letter, _ = grade_for_mark(Decimal('50'))
        self.assertEqual(letter, 'D')


class ResultModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(code='CSE', name='CSE')
        cls.sem = Semester.objects.create(term='fall', year=2025)
        cls.user = User.objects.create_user('s', password='p', role='student')
        cls.stu = Student.objects.create(user=cls.user, student_id='2025-1', department=cls.dept)
        cls.teach_user = User.objects.create_user('t', password='p', role='teacher')
        cls.teacher = Teacher.objects.create(user=cls.teach_user, teacher_id='T1', department=cls.dept)
        cls.c1 = Course.objects.create(course_code='CSE101', title='Intro', department=cls.dept, semester=cls.sem, section='A', credits=3, instructor=cls.teacher)
        cls.c2 = Course.objects.create(course_code='CSE102', title='Lab', department=cls.dept, semester=cls.sem, section='A', credits=1, instructor=cls.teacher)
        cls.e1 = Enrollment.objects.create(student=cls.stu, course=cls.c1, semester=cls.sem, status='completed')
        cls.e2 = Enrollment.objects.create(student=cls.stu, course=cls.c2, semester=cls.sem, status='completed')

    def test_result_save_autosets_grade(self):
        r = Result.objects.create(enrollment=self.e1, marks=Decimal('95'))
        self.assertEqual(r.grade_letter, 'A+')
        self.assertEqual(r.grade_point, Decimal('4.00'))

    def test_cgpa_computation(self):
        # c1: 3 credits × A+ (4.0) = 12 points
        # c2: 1 credit × B (3.5) = 3.5 points
        # Total: 15.5 / 4 = 3.875 → 3.88
        Result.objects.create(enrollment=self.e1, marks=Decimal('95'))
        Result.objects.create(enrollment=self.e2, marks=Decimal('75'))
        cgpa = compute_cgpa(self.stu)
        self.assertEqual(cgpa, Decimal('3.88'))

    def test_gpa_with_no_results(self):
        cgpa = compute_cgpa(self.stu)
        self.assertEqual(cgpa, Decimal('0'))
