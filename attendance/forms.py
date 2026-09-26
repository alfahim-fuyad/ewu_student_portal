"""Forms for the attendance app."""
from django import forms
from attendance.models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('enrollment', 'date', 'status', 'note')
        widgets = {
            'enrollment': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BulkAttendanceForm(forms.Form):
    """Form for taking attendance for all students of one course at once.

    A separate BooleanField is added dynamically for each enrollment."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    course = forms.IntegerField(
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, enrollments=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollments = enrollments or []
        for enrollment in self.enrollments:
            self.fields[f'student_{enrollment.pk}'] = forms.ChoiceField(
                choices=Attendance.Status.choices,
                initial=Attendance.Status.PRESENT,
                widget=forms.Select(attrs={'class': 'form-select'}),
                label=str(enrollment.student),
            )
