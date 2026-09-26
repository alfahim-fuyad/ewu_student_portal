"""
Students app views — CRUD for admin, read-only detail for student/teacher.

Students can only view their own profile; teachers can view all students;
admins can create / edit / delete.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib import messages

from accounts.models import User
from students.models import Student
from students.forms import StudentForm


class AdminOrTeacherMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow admin and teacher roles to access."""
    login_url = 'accounts:login'

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_admin_role or user.is_teacher)

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to view that page.')
        return redirect('dashboard')


class AdminOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('dashboard')


# ----------------------------------------------------------------------------
# List & detail — admin/teacher can list all, students can list/browse
# ----------------------------------------------------------------------------

class StudentListView(AdminOrTeacherMixin, ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    paginate_by = 15

    def get_queryset(self):
        qs = Student.objects.select_related('user', 'department', 'current_semester')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                student_id__icontains=q,
            ) | qs.filter(
                user__first_name__icontains=q,
            ) | qs.filter(
                user__last_name__icontains=q,
            )
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/detail.html'
    context_object_name = 'student'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Students can only view their own profile
        if self.request.user.is_student:
            if not self.request.user.get_profile() or self.request.user.get_profile().pk != obj.pk:
                from django.contrib import messages
                messages.error(self.request, 'You can only view your own profile.')
                return redirect('dashboard')
        return obj


# ----------------------------------------------------------------------------
# Create / update / delete — admin only
# ----------------------------------------------------------------------------

class StudentCreateView(AdminOnlyMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/add.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, f'Student {form.instance.student_id} created.')
        return super().form_valid(form)


class StudentUpdateView(AdminOnlyMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/edit.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, 'Student profile updated.')
        return super().form_valid(form)


class StudentDeleteView(AdminOnlyMixin, DeleteView):
    model = Student
    template_name = 'students/delete.html'
    success_url = reverse_lazy('students:list')
    context_object_name = 'student'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Student profile deleted.')
        return super().delete(request, *args, **kwargs)


# ----------------------------------------------------------------------------
# Student self-view of their own profile
# ----------------------------------------------------------------------------

@login_required
def my_profile(request):
    """Redirect to current user's student profile detail."""
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        messages.error(request, 'You do not have a student profile yet.')
        return redirect('dashboard')
    return redirect('students:detail', pk=profile.pk)
