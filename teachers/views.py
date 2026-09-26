"""
Teachers app views — CRUD for admin, read-only list/detail for teachers/students.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from teachers.models import Teacher
from teachers.forms import TeacherForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('dashboard')


class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = 'teachers/list.html'
    context_object_name = 'teachers'
    paginate_by = 15
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Teacher.objects.select_related('user', 'department')
        q = self.request.GET.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(teacher_id__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
            )
        return qs


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'teachers/detail.html'
    context_object_name = 'teacher'
    login_url = 'accounts:login'


class TeacherCreateView(AdminRequiredMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/add.html'
    success_url = reverse_lazy('teachers:list')

    def form_valid(self, form):
        messages.success(self.request, f'Teacher {form.instance.teacher_id} created.')
        return super().form_valid(form)


class TeacherUpdateView(AdminRequiredMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/edit.html'
    success_url = reverse_lazy('teachers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Teacher profile updated.')
        return super().form_valid(form)


class TeacherDeleteView(AdminRequiredMixin, DeleteView):
    model = Teacher
    template_name = 'teachers/delete.html'
    success_url = reverse_lazy('teachers:list')
    context_object_name = 'teacher'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Teacher profile deleted.')
        return super().delete(request, *args, **kwargs)
