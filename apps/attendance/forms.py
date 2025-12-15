# attendance/forms.py
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.academics.models import SchoolClass, Section, StudentAttendance
from apps.hr.models import StaffAttendance
from apps.students.models import Student


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    class_name = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(StudentAttendance._meta.get_field('status').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant)
            self.fields['section'].queryset = Section.objects.filter(
                class_name__tenant=tenant
            )


class StudentAttendanceForm(forms.ModelForm):
    """Form for marking individual student attendance"""
    class Meta:
        model = StudentAttendance
        fields = ['student', 'date', 'status', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.instance.tenant = self.tenant
            # Filter students by tenant
            self.fields['student'].queryset = Student.objects.filter(
                tenant=self.tenant,
                status='ACTIVE'
            ).select_related('current_class', 'section')
            
            # Set initial date to today
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        date = cleaned_data.get('date')
        
        if student and date:
            # Check if attendance already exists for this student and date
            existing = StudentAttendance.objects.filter(
                tenant=self.tenant,
                student=student,
                date=date
            ).exists()
            
            if existing and not self.instance.pk:
                raise ValidationError(
                    f"Attendance already marked for {student.full_name} on {date}"
                )
        
        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    class_name = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'loadSections()'})
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'loadStudents()'})
    )
    
    # This field will be populated dynamically via JavaScript
    attendance_data = forms.JSONField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['class_name'].queryset = SchoolClass.objects.filter(
                tenant=self.tenant,
                is_active=True
            )
            self.fields['section'].queryset = Section.objects.filter(
                class_name__tenant=self.tenant,
                is_active=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        class_name = cleaned_data.get('class_name')
        section = cleaned_data.get('section')
        attendance_data = cleaned_data.get('attendance_data', {})
        
        if date and class_name and section:
            # Validate that date is not in the future
            if date > timezone.now().date():
                raise ValidationError("Cannot mark attendance for future dates")
            
            # Validate attendance data
            if not attendance_data:
                raise ValidationError("No attendance data provided")
        
        return cleaned_data


class StaffBulkAttendanceForm(forms.Form):
    """Form for bulk staff attendance marking"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'loadStaff()'})
    )
    
    # This field will be populated dynamically via JavaScript
    attendance_data = forms.JSONField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        from apps.hr.models import Department
        if self.tenant:
            self.fields['department'].queryset = Department.objects.filter(
                tenant=self.tenant
            )
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        attendance_data = cleaned_data.get('attendance_data', {})
        
        if date:
            # Validate that date is not in the future
            if date > timezone.now().date():
                raise ValidationError("Cannot mark attendance for future dates")
            
            # Validate attendance data
            if not attendance_data:
                raise ValidationError("No attendance data provided")
        
        return cleaned_data