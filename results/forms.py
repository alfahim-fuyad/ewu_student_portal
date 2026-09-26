"""Forms for the results app."""
from django import forms
from results.models import Result


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ('enrollment', 'marks', 'is_published', 'remarks')
        widgets = {
            'enrollment': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
