"""
Attendance model — records whether a student was present/absent/late for a
specific date and course.

Each attendance row belongs to one Enrollment. This makes it easy to compute
per-course and overall attendance percentages.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Attendance(models.Model):
    """One attendance record for a student in a course on a given date."""

    class Status(models.TextChoices):
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        LATE = 'late', _('Late')
        EXCUSED = 'excused', _('Excused (with prior notice)')

    enrollment = models.ForeignKey(
        'academics.Enrollment',
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.PRESENT,
    )
    note = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='marked_attendance',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = _('attendance')
        verbose_name_plural = _('attendance records')
        unique_together = ('enrollment', 'date')

    def __str__(self):
        return f'{self.enrollment} — {self.date} ({self.status})'
