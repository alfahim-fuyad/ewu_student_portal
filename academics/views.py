"""
Academics views — list/detail views for departments, courses, semesters,
enrollments. CRUD is admin-only.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View,
)

from academics.models import Department, Course, Semester, Enrollment
from academics.forms import DepartmentForm, CourseForm, SemesterForm, EnrollmentForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('dashboard')


# ----------------------------------------------------------------------------
# Departments
# ----------------------------------------------------------------------------

class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'academics/departments.html'
    context_object_name = 'departments'
    login_url = 'accounts:login'


class DepartmentCreateView(AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'academics/department_form.html'
    success_url = reverse_lazy('academics:departments')

    def form_valid(self, form):
        messages.success(self.request, 'Department created.')
        return super().form_valid(form)


class DepartmentUpdateView(AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'academics/department_form.html'
    success_url = reverse_lazy('academics:departments')

    def form_valid(self, form):
        messages.success(self.request, 'Department updated.')
        return super().form_valid(form)


class DepartmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Department
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:departments')


# ----------------------------------------------------------------------------
# Semesters
# ----------------------------------------------------------------------------

class SemesterListView(LoginRequiredMixin, ListView):
    model = Semester
    template_name = 'academics/semesters.html'
    context_object_name = 'semesters'
    login_url = 'accounts:login'


class SemesterCreateView(AdminRequiredMixin, CreateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'academics/semester_form.html'
    success_url = reverse_lazy('academics:semesters')


class SemesterUpdateView(AdminRequiredMixin, UpdateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'academics/semester_form.html'
    success_url = reverse_lazy('academics:semesters')


class SemesterDeleteView(AdminRequiredMixin, DeleteView):
    model = Semester
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:semesters')


# ----------------------------------------------------------------------------
# Courses
# ----------------------------------------------------------------------------

class CourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'academics/courses.html'
    context_object_name = 'courses'
    paginate_by = 15
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Course.objects.select_related('department', 'semester', 'instructor', 'instructor__user')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(course_code__icontains=q) | Q(title__icontains=q)
            )
        dept = self.request.GET.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['departments'] = Department.objects.all()
        return ctx


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'academics/course_detail.html'
    context_object_name = 'course'
    login_url = 'accounts:login'


class CourseCreateView(AdminRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'academics/course_form.html'
    success_url = reverse_lazy('academics:courses')

    def form_valid(self, form):
        messages.success(self.request, 'Course created.')
        return super().form_valid(form)


class CourseUpdateView(AdminRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'academics/course_form.html'
    success_url = reverse_lazy('academics:courses')


class CourseDeleteView(AdminRequiredMixin, DeleteView):
    model = Course
    template_name = 'academics/confirm_delete.html'
    success_url = reverse_lazy('academics:courses')


# ----------------------------------------------------------------------------
# Enrollments
# ----------------------------------------------------------------------------

class EnrollmentListView(LoginRequiredMixin, ListView):
    model = Enrollment
    template_name = 'academics/enrollment.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Enrollment.objects.select_related(
            'student', 'student__user', 'course', 'course__department', 'semester'
        )
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            if profile:
                qs = qs.filter(student=profile)
            else:
                qs = qs.none()
        return qs


class EnrollmentCreateView(AdminRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'academics/enrollment_form.html'
    success_url = reverse_lazy('academics:enrollment')

    def form_valid(self, form):
        messages.success(self.request, 'Student enrolled.')
        return super().form_valid(form)
