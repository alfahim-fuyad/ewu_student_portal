"""
Attendance views:
- Teachers/admins can take attendance for a course (single or bulk)
- Students see their own per-course attendance summary
- Reports give a percentage breakdown
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, View

from academics.models import Course, Enrollment
from attendance.models import Attendance
from attendance.forms import BulkAttendanceForm


class TeacherOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_teacher or u.is_admin_role)

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission for that page.')
        return redirect('dashboard')


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'records'
    paginate_by = 25
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'enrollment', 'enrollment__student', 'enrollment__student__user',
            'enrollment__course', 'marked_by',
        )
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            qs = qs.filter(enrollment__student=profile) if profile else qs.none()
        elif self.request.user.is_teacher:
            profile = getattr(self.request.user, 'teacher_profile', None)
            qs = qs.filter(enrollment__course__instructor=profile) if profile else qs.none()
        return qs


class TakeAttendanceView(TeacherOrAdminMixin, View):
    """Bulk-take attendance for one course on one date."""

    template = 'attendance/take_attendance.html'

    def get(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        enrollments = Enrollment.objects.filter(course=course, status='enrolled').select_related(
            'student', 'student__user'
        )
        form = BulkAttendanceForm(enrollments=enrollments)
        return render(request, self.template, {'course': course, 'form': form, 'enrollments': enrollments})

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        enrollments = Enrollment.objects.filter(course=course, status='enrolled')
        form = BulkAttendanceForm(request.POST, enrollments=enrollments)
        if not form.is_valid():
            return render(request, self.template, {'course': course, 'form': form, 'enrollments': enrollments})

        date = form.cleaned_data['date']
        created = 0
        for enrollment in enrollments:
            status = form.cleaned_data[f'student_{enrollment.pk}']
            Attendance.objects.update_or_create(
                enrollment=enrollment,
                date=date,
                defaults={'status': status, 'marked_by': request.user},
            )
            created += 1
        messages.success(request, f'Attendance saved for {created} students on {date}.')
        return redirect('attendance:list')


@login_required
def attendance_report(request):
    """Course-wise attendance summary — admins/teachers see all, students see own."""
    user = request.user
    if user.is_student:
        profile = getattr(user, 'student_profile', None)
        if not profile:
            messages.error(request, 'No student profile found.')
            return redirect('dashboard')
        records = Attendance.objects.filter(enrollment__student=profile)
    elif user.is_teacher:
        profile = getattr(user, 'teacher_profile', None)
        records = Attendance.objects.filter(enrollment__course__instructor=profile) if profile else Attendance.objects.none()
    else:
        records = Attendance.objects.all()

    summary = records.values('enrollment__course__course_code', 'enrollment__course__title').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late')),
    ).order_by('enrollment__course__course_code')

    for row in summary:
        row['pct'] = round((row['present'] / row['total'] * 100) if row['total'] else 0, 1)

    return render(request, 'attendance/report.html', {'summary': summary})
