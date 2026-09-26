"""Forms for the academics app."""
from django import forms
from academics.models import Department, Course, Semester, Enrollment


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ('code', 'name', 'description', 'head', 'is_active')
        widgets = {
            'head': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for n, f in self.fields.items():
            if 'class' not in f.widget.attrs:
                f.widget.attrs.setdefault('class', 'form-control')


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ('term', 'year', 'is_current', 'start_date', 'end_date', 'registration_deadline')
        widgets = {
            'term': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'registration_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for n, f in self.fields.items():
            if 'class' not in f.widget.attrs:
                f.widget.attrs.setdefault('class', 'form-control')


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            'course_code', 'title', 'description', 'department', 'credits',
            'semester', 'instructor', 'section', 'schedule', 'room',
            'capacity', 'is_active',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'term_choice': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for n, f in self.fields.items():
            if 'class' not in f.widget.attrs:
                f.widget.attrs.setdefault('class', 'form-control')


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ('student', 'course', 'semester', 'status')
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
