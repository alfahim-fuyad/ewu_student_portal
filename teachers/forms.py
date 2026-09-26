"""Forms for the teachers app."""
from django import forms
from django.core.exceptions import ValidationError
from teachers.models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = (
            'user', 'teacher_id', 'department', 'designation',
            'specialization', 'join_date', 'is_active', 'office_room', 'cv_link',
        )
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'join_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cv_link': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_teacher_id(self):
        tid = self.cleaned_data['teacher_id'].strip()
        qs = Teacher.objects.filter(teacher_id=tid)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Teacher ID already exists.')
        return tid
