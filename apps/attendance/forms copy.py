from django import forms
from apps.academics.models import SchoolClass, Section, Attendance

class AttendanceFilterForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Class"
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    session = forms.ChoiceField(
        choices=Attendance.SESSION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        initial='FULL_DAY'
    )

class MarkAttendanceForm(forms.Form):
    # This form will be dynamically constructed in the view to have fields for each student
    pass
