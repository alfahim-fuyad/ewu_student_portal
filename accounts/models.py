"""
User, Profile, and role-based models for the Student Portal.

The portal supports three roles via a single custom User model:
    ADMIN    — full system management
    TEACHER  — course/attendance/marks management
    STUDENT  — read-only access to own academic data + AI assistant

This keeps authentication simple while still allowing per-role permissions.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with a role field for role-based access control."""

    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        TEACHER = 'teacher', _('Teacher')
        STUDENT = 'student', _('Student')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('Determines what the user can access after login.'),
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ['username']
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    # Convenience role checks
    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    def get_profile(self):
        """Return the related Student or Teacher profile, or None."""
        if self.is_student:
            return getattr(self, 'student_profile', None)
        if self.is_teacher:
            return getattr(self, 'teacher_profile', None)
        return None
