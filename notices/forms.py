"""Forms for the notices app."""
from django import forms
from notices.models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = (
            'title', 'body', 'audience', 'department',
            'course', 'is_pinned', 'is_active',
            'publish_at', 'expires_at',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'audience': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'publish_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
