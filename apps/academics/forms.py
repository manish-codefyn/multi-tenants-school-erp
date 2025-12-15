"""
Academic Forms
"""
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.forms import TenantAwareModelForm
from apps.academics.models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, StudentAttendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher, GradingSystem, Grade
)


class AcademicYearForm(TenantAwareModelForm):
    """Form for Academic Year"""
    class Meta:
        model = AcademicYear
        fields = ['name', 'code', 'start_date', 'end_date', 'is_current', 'has_terms']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            # Check for overlapping academic years
            overlapping_years = AcademicYear.objects.filter(
                tenant=self.tenant,
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Explicitly exclude the current instance if it exists (for updates)
            if self.instance and self.instance.pk:
                overlapping_years = overlapping_years.exclude(id=self.instance.pk)
            
            if overlapping_years.exists():
                raise ValidationError("Academic year overlaps with existing year")
        
        return cleaned_data


class TermForm(TenantAwareModelForm):
    """Form for Term"""
    class Meta:
        model = Term
        fields = ['academic_year', 'name', 'term_type', 'order', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        academic_year = cleaned_data.get('academic_year')
        
        if start_date and end_date and academic_year:
            # Check if dates are within academic year
            if start_date < academic_year.start_date or end_date > academic_year.end_date:
                raise ValidationError("Term dates must be within academic year dates")
            
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
        
        return cleaned_data


class SchoolClassForm(TenantAwareModelForm):
    """Form for School Class"""
    class Meta:
        model = SchoolClass
        fields = [
            'name', 'numeric_name', 'code', 'level', 'order',
            'pass_percentage', 'max_strength', 'tuition_fee',
            'class_teacher', 'is_active'
        ]


class SectionForm(TenantAwareModelForm):
    """Form for Section"""
    class Meta:
        model = Section
        fields = [
            'class_name', 'name', 'code', 'max_strength',
            'section_incharge', 'room_number', 'is_active'
        ]


class HouseForm(TenantAwareModelForm):
    """Form for House"""
    class Meta:
        model = House
        fields = [
            'name', 'code', 'color', 'motto', 'description',
            'house_master', 'logo'
        ]


class HousePointsForm(TenantAwareModelForm):
    """Form for House Points"""
    class Meta:
        model = HousePoints
        fields = ['house', 'points', 'activity', 'description', 'date_awarded', 'awarded_by']
        widgets = {
            'date_awarded': forms.DateInput(attrs={'type': 'date'}),
        }


class SubjectForm(TenantAwareModelForm):
    """Form for Subject"""
    class Meta:
        model = Subject
        fields = [
            'name', 'code', 'subject_type', 'subject_group', 'description',
            'has_practical', 'has_project', 'is_scoring',
            'credit_hours', 'max_marks', 'pass_marks', 'is_active'
        ]


class ClassSubjectForm(TenantAwareModelForm):
    """Form for Class Subject"""
    class Meta:
        model = ClassSubject
        fields = [
            'class_name', 'subject', 'is_compulsory',
            'periods_per_week', 'teacher', 'academic_year'
        ]


class TimeTableForm(TenantAwareModelForm):
    """Form for Time Table"""
    class Meta:
        model = TimeTable
        fields = [
            'class_name', 'section', 'academic_year', 'day', 'period_number',
            'start_time', 'end_time', 'subject', 'teacher', 'room', 'period_type'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Default: Empty querysets for dependent fields if no class selected
        # (Only if we are not editing an existing instance with data, but simpler to start empty and fill)
        # But TenantAwareModelForm sets initial tenant-filtered querysets.
        
        # We need to filter further based on class_name
        self.fields['section'].queryset = Section.objects.none()
        self.fields['subject'].queryset = ClassSubject.objects.none()
        
        # Get class_id from bound data or instance
        class_id = None
        if 'class_name' in self.data:
            class_id = self.data.get('class_name')
        elif self.instance.pk:
            class_id = self.instance.class_name_id
            
        # Apply filters if class is selected
        if class_id:
            try:
                # Ensure we filter by tenant as well (inherited from TenantAwareModelForm logic)
                tenant_filter = {'tenant': self.tenant} if self.tenant else {}
                
                self.fields['section'].queryset = Section.objects.filter(
                    class_name_id=class_id, 
                    **tenant_filter
                ).order_by('name')
                
                self.fields['subject'].queryset = ClassSubject.objects.filter(
                    class_name_id=class_id, 
                    **tenant_filter
                ).order_by('subject__name')
                
            except (ValueError, TypeError):
                pass  # Invalid class_id, leave querysets empty


class StudentAttendanceForm(TenantAwareModelForm):
    """Form for Student Attendance"""
    class Meta:
        model = StudentAttendance
        fields = [
            'student', 'date', 'status', 'class_name', 'section',
            'session', 'remarks', 'marked_by'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class HolidayForm(TenantAwareModelForm):
    """Form for Holiday"""
    class Meta:
        model = Holiday
        fields = [
            'name', 'holiday_type', 'start_date', 'end_date',
            'description', 'academic_year', 'affected_classes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudyMaterialForm(TenantAwareModelForm):
    """Form for Study Material"""
    class Meta:
        model = StudyMaterial
        fields = [
            'title', 'material_type', 'description',
            'class_name', 'subject', 'file', 'is_published'
        ]


class SyllabusForm(TenantAwareModelForm):
    """Form for Syllabus"""
    class Meta:
        model = Syllabus
        fields = [
            'class_name', 'subject', 'academic_year',
            'topics', 'recommended_books', 'reference_materials',
            'assessment_pattern'
        ]


class StreamForm(TenantAwareModelForm):
    """Form for Stream"""
    class Meta:
        model = Stream
        fields = [
            'name', 'code', 'description',
            'available_from_class', 'subjects', 'is_active'
        ]


class ClassTeacherForm(TenantAwareModelForm):
    """Form for Class Teacher"""
    class Meta:
        model = ClassTeacher
        fields = [
            'class_name', 'section', 'teacher',
            'academic_year', 'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class GradingSystemForm(TenantAwareModelForm):
    """Form for Grading System"""
    class Meta:
        model = GradingSystem
        fields = ['name', 'code', 'description', 'is_active', 'is_default']


class GradeForm(TenantAwareModelForm):
    """Form for Grade"""
    class Meta:
        model = Grade
        fields = [
            'grading_system', 'grade', 'description',
            'min_percentage', 'max_percentage', 'grade_point',
            'remarks', 'order'
        ]