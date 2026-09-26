"""
Result model + GPA/CGPA computation helpers.

Grade scale (standard 4.0):
    Marks range → Letter → Grade Point
    90–100       → A+     → 4.00
    80–89        → A      → 3.75
    70–79        → B      → 3.50
    60–69        → C      → 3.25
    50–59        → D      → 3.00
    <50          → F      → 0.00

GPA per semester  = Σ(point × credits) / Σ(credits)   (only completed results)
CGPA across sems  = Σ(point × credits) / Σ(credits)   over all completed results
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _


GRADE_SCALE = [
    (Decimal('90'), 'A+', Decimal('4.00')),
    (Decimal('80'), 'A',  Decimal('3.75')),
    (Decimal('70'), 'B',  Decimal('3.50')),
    (Decimal('60'), 'C',  Decimal('3.25')),
    (Decimal('50'), 'D',  Decimal('3.00')),
    (Decimal('0'),  'F',  Decimal('0.00')),
]


def grade_for_mark(marks: Decimal):
    """Return (letter, point) tuple for a given marks value (0-100)."""
    if marks is None:
        return ('N/A', Decimal('0'))
    for threshold, letter, point in GRADE_SCALE:
        if Decimal(marks) >= threshold:
            return (letter, point)
    return ('F', Decimal('0'))


class Result(models.Model):
    """A single course result for an enrollment."""

    enrollment = models.OneToOneField(
        'academics.Enrollment',
        on_delete=models.CASCADE,
        related_name='result',
    )
    marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Total marks obtained (0–100).',
    )
    grade_letter = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True,
    )
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now=True)
    remarks = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = _('result')
        verbose_name_plural = _('results')

    def __str__(self):
        return f'{self.enrollment} — {self.grade_letter} ({self.grade_point})'

    def save(self, *args, **kwargs):
        # Auto-derive grade from marks if not overridden
        letter, point = grade_for_mark(self.marks)
        if not self.grade_letter:
            self.grade_letter = letter
        if not self.grade_point:
            self.grade_point = point
        super().save(*args, **kwargs)

    @property
    def credits(self):
        return self.enrollment.course.credits


# ----------------------------------------------------------------------------
# GPA / CGPA helpers
# ----------------------------------------------------------------------------

def compute_gpa(student, semester=None):
    """Compute GPA for one student for a specific semester (or overall)."""
    qs = Result.objects.filter(
        enrollment__student=student,
        is_published=True,
    )
    if semester is not None:
        qs = qs.filter(enrollment__semester=semester)

    total_credits = Decimal('0')
    total_points = Decimal('0')
    for r in qs.select_related('enrollment', 'enrollment__course'):
        c = Decimal(r.enrollment.course.credits)
        total_credits += c
        total_points += c * (r.grade_point or Decimal('0'))

    if total_credits == 0:
        return Decimal('0')
    return (total_points / total_credits).quantize(Decimal('0.01'))


def compute_cgpa(student):
    """Compute overall CGPA across all completed results."""
    return compute_gpa(student, semester=None)


def student_transcript(student):
    """Return a list of dicts: one row per semester with courses + grade."""
    from academics.models import Enrollment
    semesters = []
    enrollments = Enrollment.objects.filter(
        student=student, status='completed',
    ).select_related('course', 'semester', 'result').order_by('semester__year', 'semester__term')

    by_sem = {}
    for e in enrollments:
        by_sem.setdefault(e.semester, []).append(e)

    for sem, enrolls in by_sem.items():
        rows = []
        total_credits = Decimal('0')
        total_points = Decimal('0')
        for e in enrolls:
            r = getattr(e, 'result', None)
            credits = Decimal(e.course.credits)
            point = r.grade_point if r else Decimal('0')
            letter = r.grade_letter if r else 'I'
            total_credits += credits
            total_points += credits * point
            rows.append({
                'course': e.course,
                'credits': credits,
                'letter': letter,
                'point': point,
                'marks': r.marks if r else None,
            })
        gpa = (total_points / total_credits).quantize(Decimal('0.01')) if total_credits else Decimal('0')
        semesters.append({
            'semester': sem,
            'rows': rows,
            'gpa': gpa,
            'total_credits': total_credits,
        })
    return semesters
