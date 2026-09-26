"""
Accounts views — authentication (login/logout/register), profile, password
change, forgot-password request, and the role-aware dashboard view.

The dashboard is the post-login landing page for every role. It is included
in `accounts.urls` under the namespace `core` so that LOGIN_REDIRECT_URL
(`core:dashboard`) resolves cleanly.
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import View, UpdateView

from accounts.models import User
from accounts.forms import (
    LoginForm,
    UserRegistrationForm,
    UserUpdateForm,
    AvatarForm,
    PasswordChangeForm,
    ForgotPasswordForm,
)


# ----------------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------------

def login_view(request):
    """Log the user in and redirect to the role-aware dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
        return redirect('dashboard')
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


def register_view(request):
    """Self-registration for student/teacher only."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, 'Account created. Please log in.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


# ----------------------------------------------------------------------------
# Dashboard (role-aware)
# ----------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Render a dashboard tailored to the user's role."""
    user = request.user
    context = {
        'user': user,
        'now': timezone.now(),
        'is_student_view': user.is_student,
        'is_teacher_view': user.is_teacher,
        'is_admin_view': user.is_admin_role,
    }

    # Role-specific context
    if user.is_student:
        profile = getattr(user, 'student_profile', None)
        context.update(_student_dashboard_context(profile))
    elif user.is_teacher:
        profile = getattr(user, 'teacher_profile', None)
        context.update(_teacher_dashboard_context(profile))

    return render(request, 'dashboard.html', context)


def _student_dashboard_context(profile):
    from academics.models import Enrollment
    from attendance.models import Attendance
    from results.models import Result
    from fees.models import Fee
    from notices.models import Notice

    if not profile:
        return {'profile': None}

    enrollments = Enrollment.objects.filter(student=profile, status='enrolled')
    today_attendance = Attendance.objects.filter(enrollment__student=profile).count()
    present_count = Attendance.objects.filter(enrollment__student=profile, status='present').count()
    attendance_pct = (present_count / today_attendance * 100) if today_attendance else 0

    unpaid_fees = Fee.objects.filter(student=profile, status='unpaid').count()
    total_due = sum(f.amount for f in Fee.objects.filter(student=profile, status='unpaid'))

    recent_results = Result.objects.filter(enrollment__student=profile).order_by('-id')[:5]

    notices = Notice.objects.filter(
        is_active=True,
    ).filter(
        models_Q_visibility(profile)
    )[:5]

    return {
        'profile': profile,
        'current_courses': enrollments,
        'attendance_pct': round(attendance_pct, 1),
        'unpaid_fees': unpaid_fees,
        'total_due': total_due,
        'recent_results': recent_results,
        'recent_notices': notices,
    }


def _teacher_dashboard_context(profile):
    from academics.models import Course
    from notices.models import Notice

    if not profile:
        return {'profile': None}

    assigned_courses = Course.objects.filter(instructor=profile)
    notices = Notice.objects.filter(is_active=True).order_by('-id')[:5]
    return {
        'profile': profile,
        'assigned_courses': assigned_courses,
        'recent_notices': notices,
    }


# Avoid top-level import of Q + Notice to keep functions self-contained
from django.db.models import Q as _Q  # noqa


def models_Q_visibility(profile):
    """Build a Q filter for notices visible to a given student profile."""
    return _Q(audience='all') | _Q(audience='student') | _Q(
        audience='department', department=profile.department
    )


# ----------------------------------------------------------------------------
# Profile management
# ----------------------------------------------------------------------------

class ProfileView(LoginRequiredMixin, View):
    """View own profile + edit account fields + avatar upload."""

    template = 'accounts/profile.html'
    login_url = 'accounts:login'

    def get(self, request):
        return render(request, self.template, {
            'profile_form': UserUpdateForm(instance=request.user),
            'avatar_form': AvatarForm(instance=request.user),
        })

    def post(self, request):
        # If user submitted the avatar form, only update avatar
        if 'avatar' in request.FILES:
            avatar_form = AvatarForm(request.POST, request.FILES, instance=request.user)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Profile picture updated.')
            return redirect('accounts:profile')

        profile_form = UserUpdateForm(request.POST, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
        return render(request, self.template, {
            'profile_form': profile_form,
            'avatar_form': AvatarForm(instance=request.user),
        })


class ChangePasswordView(LoginRequiredMixin, View):
    """Allow the logged-in user to change their own password."""

    template = 'accounts/change_password.html'
    login_url = 'accounts:login'

    def get(self, request):
        form = PasswordChangeForm(request.user)
        return render(request, self.template, {'form': form})

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: keep the user logged in after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been updated.')
            return redirect('accounts:profile')
        return render(request, self.template, {'form': form})


def forgot_password(request):
    """Simple forgot-password request form.

    In a real production system this would send a reset email. Here it just
    acknowledges the request — see README for how to wire up real email.
    """
    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        messages.info(
            request,
            'If that email exists in our system, a reset link has been sent.',
        )
        return redirect('accounts:login')
    return render(request, 'accounts/forgot_password.html', {'form': form})


# ----------------------------------------------------------------------------
# Template context processor — makes the user profile available everywhere
# ----------------------------------------------------------------------------

def user_profile_context(request):
    """Expose small role info to templates (e.g., navbar highlight logic)."""
    if not request.user.is_authenticated:
        return {}
    user = request.user
    return {
        'current_role': user.role,
        'is_student': user.is_student,
        'is_teacher': user.is_teacher,
        'is_admin_role': user.is_admin_role,
        'profile': user.get_profile(),
    }
