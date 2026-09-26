"""
Teacher profile — linked 1:1 to the auth User.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Teacher(models.Model):
    """Teacher profile — linked 1:1 to a User of role=teacher."""

    class Designation(models.TextChoices):
        LECTURER = 'lecturer', _('Lecturer')
        SR_LECTURER = 'sr_lecturer', _('Senior Lecturer')
        ASST_PROF = 'asst_prof', _('Assistant Professor')
        ASSOC_PROF = 'assoc_prof', _('Associate Professor')
        PROFESSOR = 'professor', _('Professor')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    teacher_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='teachers',
    )
    designation = models.CharField(
        max_length=20, choices=Designation.choices,
        default=Designation.LECTURER,
    )
    specialization = models.CharField(max_length=200, blank=True)
    join_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    office_room = models.CharField(max_length=50, blank=True)
    cv_link = models.URLField(blank=True)

    class Meta:
        ordering = ['-id']
        verbose_name = _('teacher')
        verbose_name_plural = _('teachers')

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f'{name} ({self.teacher_id})'

    @property
    def full_name(self) -> str:
        return self.user.get_full_name() or self.user.username
