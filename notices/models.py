"""
Notice model — announcements visible to students/teachers/admins.

Audience filtering allows notices to be:
    - global (audience='all')
    - student-only (audience='student')
    - teacher-only (audience='teacher')
    - department-scoped (audience='department')
    - course-scoped (audience='course')
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notice(models.Model):
    class Audience(models.TextChoices):
        ALL = 'all', _('Everyone')
        STUDENT = 'student', _('Students')
        TEACHER = 'teacher', _('Teachers')
        ADMIN = 'admin', _('Admins')
        DEPARTMENT = 'department', _('Department')
        COURSE = 'course', _('Course')

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(
        max_length=20, choices=Audience.choices,
        default=Audience.ALL,
    )
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notices',
        help_text='Required only when audience=department.',
    )
    course = models.ForeignKey(
        'academics.Course',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notices',
        help_text='Required only when audience=course.',
    )
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    publish_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    posted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posted_notices',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = _('notice')
        verbose_name_plural = _('notices')

    def __str__(self):
        return self.title

    @staticmethod
    def visible_to(user):
        """Return queryset of notices visible to the given user."""
        from django.db.models import Q
        from django.utils.timezone import now
        qs = Notice.objects.filter(is_active=True).filter(
            Q(publish_at__isnull=True) | Q(publish_at__lte=now())
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now())
        )
        if not user.is_authenticated:
            return qs.none()
        if user.is_admin_role:
            return qs
        if user.is_student:
            profile = getattr(user, 'student_profile', None)
            dept = profile.department if profile else None
            return qs.filter(
                Q(audience='all') | Q(audience='student')
                | (Q(audience='department') & Q(department=dept))
            )
        if user.is_teacher:
            profile = getattr(user, 'teacher_profile', None)
            dept = profile.department if profile else None
            return qs.filter(
                Q(audience='all') | Q(audience='teacher')
                | (Q(audience='department') & Q(department=dept))
            )
        return qs
