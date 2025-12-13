from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.utils.tenant import get_current_tenant
from .models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, Attendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher
)
from apps.core.forms import BaseForm as BaseForm


class AcademicYearForm(BaseForm):
    """Form for AcademicYear model"""
    
    class Meta:
        model = AcademicYear
        fields = ['name', 'code', 'description', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024-2025'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., AY2425'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            self.fields['is_current'].help_text = 'Checking this will unset current status from other academic years'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError('End date must be after start date')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class TermForm(BaseForm):
    """Form for Term model"""
    
    class Meta:
        model = Term
        fields = ['name', 'code', 'academic_year', 'description', 
                 'start_date', 'end_date', 'order', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., First Term'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., T1'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
        
        if self.instance.pk:
            self.fields['is_current'].help_text = 'Checking this will unset current status from other terms in this academic year'
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        academic_year = cleaned_data.get('academic_year')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError('End date must be after start date')
            
            if academic_year:
                if start_date < academic_year.start_date or end_date > academic_year.end_date:
                    raise ValidationError('Term dates must be within academic year dates')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class SchoolClassForm(BaseForm):
    """Form for SchoolClass model"""
    
    class Meta:
        model = SchoolClass
        fields = ['name', 'code', 'description', 'level', 'order', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Grade 10'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., G10'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class SectionForm(BaseForm):
    """Form for Section model"""
    
    class Meta:
        model = Section
        fields = ['name', 'code', 'class_name', 'description', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Section A'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SEC_A'}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class SubjectForm(BaseForm):
    """Form for Subject model"""
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'subject_type', 'is_core', 'is_elective', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mathematics'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MATH'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subject_type': forms.Select(attrs={'class': 'form-control'}),
            'is_core': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_elective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class ClassSubjectForm(BaseForm):
    """Form for ClassSubject model"""
    
    class Meta:
        model = ClassSubject
        fields = ['class_name', 'subject', 'academic_year', 'teacher', 'is_optional', 'order']
        widgets = {
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'is_optional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            self.fields['subject'].queryset = Subject.objects.filter(tenant=tenant, is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
            
            # Get teachers (assuming Staff model exists)
            try:
                from apps.hr.models import Staff
                staff_qs = Staff.objects.filter(tenant=tenant, is_active=True, user__role='teacher')
                self.fields['teacher'].queryset = staff_qs
            except ImportError:
                self.fields['teacher'].queryset = self.fields['teacher'].queryset.none()
    
    def clean(self):
        cleaned_data = super().clean()
        class_name = cleaned_data.get('class_name')
        subject = cleaned_data.get('subject')
        academic_year = cleaned_data.get('academic_year')
        
        if class_name and subject and academic_year:
            # Check for duplicate class-subject assignment in same academic year
            existing = ClassSubject.objects.filter(
                tenant=get_current_tenant(),
                class_name=class_name,
                subject=subject,
                academic_year=academic_year
            )
            
            if self.instance.pk:
                existing = existing.exclude(id=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'This subject is already assigned to {class_name} for {academic_year}'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class TimeTableForm(BaseForm):
    """Form for TimeTable model"""
    
    class Meta:
        model = TimeTable
        fields = ['class_name', 'section', 'subject', 'academic_year', 'teacher',
                 'day', 'period_number', 'start_time', 'end_time', 'room_number']
        widgets = {
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'period_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Room 101'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
            
            # Get teachers (assuming Staff model exists)
            try:
                from apps.hr.models import Staff
                staff_qs = Staff.objects.filter(tenant=tenant, is_active=True, user__role='teacher')
                self.fields['teacher'].queryset = staff_qs
            except ImportError:
                self.fields['teacher'].queryset = self.fields['teacher'].queryset.none()
            
            # Filter sections and subjects based on selected class (done via AJAX)
            self.fields['section'].queryset = Section.objects.none()
            self.fields['subject'].queryset = Subject.objects.none()
            
            if self.instance.pk:
                if self.instance.class_name:
                    self.fields['section'].queryset = Section.objects.filter(
                        tenant=tenant,
                        class_name=self.instance.class_name,
                        is_active=True
                    )
                
                if self.instance.academic_year and self.instance.class_name:
                    # Get subjects assigned to this class for the academic year
                    class_subjects = ClassSubject.objects.filter(
                        tenant=tenant,
                        class_name=self.instance.class_name,
                        academic_year=self.instance.academic_year
                    )
                    self.fields['subject'].queryset = Subject.objects.filter(
                        id__in=class_subjects.values_list('subject_id', flat=True)
                    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day = cleaned_data.get('day')
        period_number = cleaned_data.get('period_number')
        class_name = cleaned_data.get('class_name')
        section = cleaned_data.get('section')
        academic_year = cleaned_data.get('academic_year')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('End time must be after start time')
        
        # Check for timetable conflicts
        if all([day, period_number, class_name, section, academic_year]):
            conflicting = TimeTable.objects.filter(
                tenant=get_current_tenant(),
                day=day,
                period_number=period_number,
                class_name=class_name,
                section=section,
                academic_year=academic_year
            )
            
            if self.instance.pk:
                conflicting = conflicting.exclude(id=self.instance.pk)
            
            if conflicting.exists():
                raise ValidationError(
                    'There is already a class scheduled for this period. '
                    f'Current: {conflicting.first().subject}'
                )
            
            # Check teacher availability
            teacher = cleaned_data.get('teacher')
            if teacher:
                teacher_conflict = TimeTable.objects.filter(
                    tenant=get_current_tenant(),
                    day=day,
                    period_number=period_number,
                    teacher=teacher,
                    academic_year=academic_year
                )
                
                if self.instance.pk:
                    teacher_conflict = teacher_conflict.exclude(id=self.instance.pk)
                
                if teacher_conflict.exists():
                    conflict = teacher_conflict.first()
                    raise ValidationError(
                        f'Teacher is already assigned to {conflict.subject} '
                        f'for {conflict.class_name} during this period'
                    )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class AttendanceForm(BaseForm):
    """Form for Attendance model"""
    
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'class_name', 'section', 'status', 
                 'session', 'remarks', 'marked_by']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'marked_by': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        today = timezone.now().date()
        self.fields['date'].initial = today
        
        if self.request:
            tenant = get_current_tenant()
            
            # Get current user as marked_by
            self.fields['marked_by'].initial = self.request.user
            self.fields['marked_by'].queryset = self.fields['marked_by'].queryset.filter(id=self.request.user.id)
            
            # Get classes and sections
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            
            # Get students (assuming Student model exists)
            try:
                from apps.students.models import Student
                self.fields['student'].queryset = Student.objects.filter(tenant=tenant, is_active=True)
            except ImportError:
                self.fields['student'].queryset = self.fields['student'].queryset.none()
            
            # Initially empty sections
            self.fields['section'].queryset = Section.objects.none()
            
            if self.instance.pk:
                if self.instance.class_name:
                    self.fields['section'].queryset = Section.objects.filter(
                        tenant=tenant,
                        class_name=self.instance.class_name,
                        is_active=True
                    )
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        student = cleaned_data.get('student')
        session = cleaned_data.get('session')
        
        # Check for duplicate attendance for same student, date, and session
        if date and student and session:
            existing = Attendance.objects.filter(
                tenant=get_current_tenant(),
                student=student,
                date=date,
                session=session
            )
            
            if self.instance.pk:
                existing = existing.exclude(id=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'Attendance for {student} on {date} ({session}) already exists'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance entry"""
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    class_name = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    session = forms.ChoiceField(
        choices=Attendance.SESSION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        today = timezone.now().date()
        self.fields['date'].initial = today
        self.fields['session'].initial = 'FULL_DAY'
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)


class HolidayForm(BaseForm):
    """Form for Holiday model"""
    
    class Meta:
        model = Holiday
        fields = ['name', 'description', 'holiday_type', 'start_date', 
                 'end_date', 'academic_year', 'is_recurring']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Diwali Holiday'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'holiday_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError('End date must be on or after start date')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class StudyMaterialForm(BaseForm):
    """Form for StudyMaterial model"""
    
    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'class_name', 'subject', 'material_type',
                 'file', 'tags', 'is_published', 'publish_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Algebra Basics'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'material_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., algebra, basics, math'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'publish_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            self.fields['subject'].queryset = Subject.objects.filter(tenant=tenant, is_active=True)
        
        # Make publish_date optional
        self.fields['publish_date'].required = False
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise ValidationError(f'File size must be less than 10MB. Current size: {file.size} bytes')
            
            # Validate file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', 
                                 '.xls', '.xlsx', '.txt', '.zip', '.jpg', 
                                 '.jpeg', '.png', '.mp4', '.mp3']
            
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise ValidationError(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}')
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            instance.uploaded_by = self.request.user
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class SyllabusForm(BaseForm):
    """Form for Syllabus model"""
    
    class Meta:
        model = Syllabus
        fields = ['title', 'description', 'class_name', 'subject', 'academic_year',
                 'file', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Grade 10 Mathematics Syllabus'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            self.fields['subject'].queryset = Subject.objects.filter(tenant=tenant, is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
    
    def clean(self):
        cleaned_data = super().clean()
        class_name = cleaned_data.get('class_name')
        subject = cleaned_data.get('subject')
        academic_year = cleaned_data.get('academic_year')
        
        # Check for duplicate syllabus
        if class_name and subject and academic_year:
            existing = Syllabus.objects.filter(
                tenant=get_current_tenant(),
                class_name=class_name,
                subject=subject,
                academic_year=academic_year
            )
            
            if self.instance.pk:
                existing = existing.exclude(id=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'Syllabus for {subject} ({class_name}) already exists for {academic_year}'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            instance.uploaded_by = self.request.user
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class HouseForm(BaseForm):
    """Form for House model"""
    
    class Meta:
        model = House
        fields = ['name', 'code', 'motto', 'description', 'color', 'logo', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Red House'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., RED'}),
            'motto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Excellence through Dedication'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class HousePointsForm(BaseForm):
    """Form for HousePoints model"""
    
    class Meta:
        model = HousePoints
        fields = ['house', 'student', 'points', 'point_type', 'reason', 'awarded_date']
        widgets = {
            'house': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'point_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'awarded_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        today = timezone.now().date()
        self.fields['awarded_date'].initial = today
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['house'].queryset = House.objects.filter(tenant=tenant, is_active=True)
            
            # Get students (assuming Student model exists)
            try:
                from apps.students.models import Student
                self.fields['student'].queryset = Student.objects.filter(tenant=tenant, is_active=True)
            except ImportError:
                self.fields['student'].queryset = self.fields['student'].queryset.none()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            instance.awarded_by = self.request.user
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class StreamForm(BaseForm):
    """Form for Stream model"""
    
    class Meta:
        model = Stream
        fields = ['name', 'code', 'class_name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Science Stream'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SCI'}),
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class ClassTeacherForm(BaseForm):
    """Form for ClassTeacher model"""
    
    class Meta:
        model = ClassTeacher
        fields = ['class_name', 'section', 'teacher', 'academic_year', 'is_active']
        widgets = {
            'class_name': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request:
            tenant = get_current_tenant()
            self.fields['class_name'].queryset = SchoolClass.objects.filter(tenant=tenant, is_active=True)
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(tenant=tenant)
            
            # Get teachers (assuming Staff model exists)
            try:
                from apps.hr.models import Staff
                staff_qs = Staff.objects.filter(tenant=tenant, is_active=True, user__role='teacher')
                self.fields['teacher'].queryset = staff_qs
            except ImportError:
                self.fields['teacher'].queryset = self.fields['teacher'].queryset.none()
            
            # Initially empty sections
            self.fields['section'].queryset = Section.objects.none()
            
            if self.instance.pk and self.instance.class_name:
                self.fields['section'].queryset = Section.objects.filter(
                    tenant=tenant,
                    class_name=self.instance.class_name,
                    is_active=True
                )
    
    def clean(self):
        cleaned_data = super().clean()
        class_name = cleaned_data.get('class_name')
        section = cleaned_data.get('section')
        academic_year = cleaned_data.get('academic_year')
        teacher = cleaned_data.get('teacher')
        
        # Check for duplicate class teacher assignment
        if class_name and section and academic_year:
            existing = ClassTeacher.objects.filter(
                tenant=get_current_tenant(),
                class_name=class_name,
                section=section,
                academic_year=academic_year
            )
            
            if self.instance.pk:
                existing = existing.exclude(id=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'Class teacher for {class_name} - {section} already assigned for {academic_year}'
                )
        
        # Check if teacher is already assigned to another class/section in same academic year
        if teacher and academic_year:
            teacher_conflict = ClassTeacher.objects.filter(
                tenant=get_current_tenant(),
                teacher=teacher,
                academic_year=academic_year
            )
            
            if self.instance.pk:
                teacher_conflict = teacher_conflict.exclude(id=self.instance.pk)
            
            if teacher_conflict.exists():
                conflict = teacher_conflict.first()
                raise ValidationError(
                    f'Teacher is already assigned to {conflict.class_name} - {conflict.section} for {academic_year}'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.request:
            tenant = get_current_tenant()
            instance.tenant = tenant
            
            if not instance.pk:
                instance.created_by = self.request.user
        
        if commit:
            instance.save()
        
        return instance