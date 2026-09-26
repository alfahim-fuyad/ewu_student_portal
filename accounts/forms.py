"""Forms for the accounts app — login, signup, profile editing, password change."""
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm as DjangoPasswordChangeForm,
    SetPasswordForm,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Login form with friendly Bootstrap-like styling."""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        }),
    )


class UserRegistrationForm(UserCreationForm):
    """Registration form with role selection — admins create accounts in prod,
    but the form is here for completeness / initial seeding."""

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_role(self):
        role = self.cleaned_data['role']
        # Normal self-registration can only be student or teacher
        if role == User.Role.ADMIN:
            raise ValidationError(
                'Admin accounts cannot be self-registered. Contact the system administrator.'
            )
        return role


class UserUpdateForm(forms.ModelForm):
    """Form used by all roles to update their own profile fields."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth', 'bio')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AvatarForm(forms.ModelForm):
    """Just the avatar upload field — used as a separate small form on profile page."""

    class Meta:
        model = User
        fields = ('avatar',)
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Add Bootstrap classes to the stock Django password-change form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class ForgotPasswordForm(forms.Form):
    """Password reset request form (email-only)."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your account email',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError('No account found with that email.')
        return email


class ResetPasswordForm(SetPasswordForm):
    """Final password reset form, styled."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
