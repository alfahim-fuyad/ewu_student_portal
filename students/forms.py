"""Forms for the students app."""
from django import forms
from django.core.exceptions import ValidationError
from students.models import Student


class StudentForm(forms.ModelForm):
    """Form for admins to create/edit student profiles."""

    class Meta:
        model = Student
        fields = (
            'user', 'student_id', 'department', 'program',
            'batch', 'current_semester', 'admission_date',
            'is_active', 'address', 'guardian_name', 'guardian_phone',
        )
        widgets = {
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'current_semester': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-control')
            field.required = False

    def clean_student_id(self):
        sid = self.cleaned_data['student_id'].strip()
        qs = Student.objects.filter(student_id=sid)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('This student ID is already taken.')
        return sid
