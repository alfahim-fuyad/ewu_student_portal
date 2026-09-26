"""
Results views — list/add/edit/transcript.

Students can only see their own results + GPA/CGPA.
Teachers/admins can add/edit results for courses they manage.
"""
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from accounts.models import User
from academics.models import Enrollment
from results.models import Result, compute_gpa, compute_cgpa, student_transcript
from results.forms import ResultForm


class ResultListView(LoginRequiredMixin, ListView):
    model = Result
    template_name = 'results/result_list.html'
    context_object_name = 'results'
    paginate_by = 20
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Result.objects.select_related(
            'enrollment', 'enrollment__student', 'enrollment__student__user',
            'enrollment__course', 'enrollment__semester',
        )
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            qs = qs.filter(enrollment__student=profile) if profile else qs.none()
        elif self.request.user.is_teacher:
            profile = getattr(self.request.user, 'teacher_profile', None)
            qs = qs.filter(enrollment__course__instructor=profile) if profile else qs.none()
        return qs


class TeacherOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_teacher or u.is_admin_role)

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission for that page.')
        return redirect('dashboard')


class ResultCreateView(TeacherOrAdminMixin, CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/add_result.html'
    success_url = reverse_lazy('results:list')

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['initial'] = kw.get('initial', {})
        if 'enrollment' in self.request.GET:
            kw['initial']['enrollment'] = self.request.GET['enrollment']
        return kw

    def form_valid(self, form):
        messages.success(self.request, 'Result added.')
        return super().form_valid(form)


class ResultUpdateView(TeacherOrAdminMixin, UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/edit_result.html'
    success_url = reverse_lazy('results:list')

    def form_valid(self, form):
        messages.success(self.request, 'Result updated.')
        return super().form_valid(form)


class TranscriptView(LoginRequiredMixin, DetailView):
    """Transcript for a specific student."""
    model = Enrollment
    template_name = 'results/transcript.html'
    context_object_name = 'enrollment'
    login_url = 'accounts:login'

    def get_object(self, queryset=None):
        # Always operate on the logged-in student's profile
        user = self.request.user
        profile = getattr(user, 'student_profile', None)
        if not profile:
            messages.error(user, 'No student profile attached to this account.')
            return None
        return profile

    def get(self, request, *args, **kwargs):
        student = self.get_object()
        if student is None:
            return redirect('dashboard')
        semesters = student_transcript(student)
        cgpa = compute_cgpa(student)
        return render(request, self.template, {
            'student': student,
            'semesters': semesters,
            'cgpa': cgpa,
        })
