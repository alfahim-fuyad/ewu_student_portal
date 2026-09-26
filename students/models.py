"""
Student profile model — linked 1:1 to the auth User.

The Student model carries academic identity (student ID, department, program,
admission batch, current semester) and is the central record that the
AI assistant needs permission-filtered access to.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Student(models.Model):
    """Student profile — linked 1:1 to a User of role=student."""

    class Program(models.TextChoices):
        BSC_CSE = 'BSC_CSE', _('B.Sc. in CSE')
        BSC_EEE = 'BSC_EEE', _('B.Sc. in EEE')
        BBA = 'BBA', _('Bachelor of Business Administration')
        MBA = 'MBA', _('Master of Business Administration')
        BSC_CE = 'BSC_CE', _('B.Sc. in Civil Engineering')
        MSC_CSE = 'MSC_CSE', _('M.Sc. in CSE')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
    )
    student_id = models.CharField(
        max_length=20, unique=True,
        help_text='Official university student ID, e.g., 2023-1-60-123.',
    )
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='students',
    )
    program = models.CharField(
        max_length=20, choices=Program.choices,
        default=Program.BSC_CSE,
    )
    batch = models.CharField(max_length=20, blank=True, help_text='e.g., 2023-24')
    current_semester = models.ForeignKey(
        'academics.Semester',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        help_text='Currently-enrolled semester.',
    )
    admission_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-id']
        verbose_name = _('student')
        verbose_name_plural = _('students')

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f'{name} ({self.student_id})'

    @property
    def full_name(self) -> str:
        return self.user.get_full_name() or self.user.username

    @property
    def email(self) -> str:
        return self.user.email
