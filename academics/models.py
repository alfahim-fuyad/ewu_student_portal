"""
Academic models: Department, Course, Semester, Enrollment.

These together describe the academic structure of the university.

    Department  1----*  Course
                1----*  Student
                1----*  Teacher

    Semester   1----*  Course (offered in a specific semester)

    Enrollment ties a Student to a Course in a Semester.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """University department, e.g., Department of CSE."""

    code = models.CharField(max_length=10, unique=True, help_text='e.g., CSE')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='headed_departments',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = _('department')
        verbose_name_plural = _('departments')

    def __str__(self):
        return f'{self.code} — {self.name}'


class Semester(models.Model):
    """A term — e.g., Fall 2024, Spring 2025."""

    class Term(models.TextChoices):
        SPRING = 'spring', _('Spring')
        SUMMER = 'summer', _('Summer')
        FALL = 'fall', _('Fall')

    term = models.CharField(max_length=10, choices=Term.choices)
    year = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    registration_deadline = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-year', 'term']
        verbose_name = _('semester')
        verbose_name_plural = _('semesters')
        unique_together = ('term', 'year')

    def __str__(self):
        return f'{self.get_term_display()} {self.year}'

    @property
    def code(self) -> str:
        return f'{self.term[:2].upper()}{self.year}'


class Course(models.Model):
    """A course offering — combines catalog course + offering semester + instructor."""

    course_code = models.CharField(max_length=15, help_text='e.g., CSE110')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses',
    )
    credits = models.DecimalField(max_digits=3, decimal_places=1, default=3.0)
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='courses',
    )
    instructor = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_courses',
    )
    section = models.CharField(max_length=10, blank=True, default='A')
    schedule = models.CharField(max_length=200, blank=True, help_text='e.g., Sun-Tue 10:00-11:30')
    room = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course_code', 'section']
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        unique_together = ('course_code', 'section', 'semester')

    def __str__(self):
        return f'{self.course_code} — {self.title} ({self.section})'

    @property
    def enrollment_count(self) -> int:
        return self.enrollments.count()


class Enrollment(models.Model):
    """Ties a student to a course for a specific semester."""

    class Status(models.TextChoices):
        ENROLLED = 'enrolled', _('Enrolled')
        DROPPED = 'dropped', _('Dropped')
        COMPLETED = 'completed', _('Completed')

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.ENROLLED,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-enrolled_at']
        verbose_name = _('enrollment')
        verbose_name_plural = _('enrollments')
        unique_together = ('student', 'course', 'semester')

    def __str__(self):
        return f'{self.student} → {self.course}'
