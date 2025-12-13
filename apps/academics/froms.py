# apps/academics/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, Attendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher
)
from apps.core.forms import BaseForm as BaseForm



class AcademicYearForm(BaseForm):
    class Meta:
        model = AcademicYear
        fields = [
            'tenant', 'name', 'code', 'start_date', 'end_date',
            'is_current', 'has_terms'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TermForm(BaseForm):
    class Meta:
        model = Term
        fields = [
            'tenant', 'academic_year', 'name', 'term_type', 'order',
            'start_date', 'end_date', 'is_current'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SchoolClassForm(BaseForm):
    class Meta:
        model = SchoolClass
        fields = [
            'tenant', 'name', 'numeric_name', 'code', 'level', 'order',
            'pass_percentage', 'max_strength', 'tuition_fee',
            'class_teacher', 'is_active'
        ]
        widgets = {
            'pass_percentage': forms.NumberInput(attrs={'step': '0.01'}),
            'tuition_fee': forms.NumberInput(attrs={'step': '0.01'}),
        }


class SectionForm(BaseForm):
    class Meta:
        model = Section
        fields = [
            'tenant', 'class_name', 'name', 'code', 'max_strength',
            'section_incharge', 'room_number', 'is_active'
        ]


class HouseForm(BaseForm):
    class Meta:
        model = House
        fields = [
            'tenant', 'name', 'code', 'color', 'motto', 'description',
            'house_master', 'total_points', 'logo'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class HousePointsForm(BaseForm):
    class Meta:
        model = HousePoints
        fields = [
            'tenant', 'house', 'points', 'activity', 'description',
            'date_awarded', 'awarded_by'
        ]
        widgets = {
            'date_awarded': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class SubjectForm(BaseForm):
    class Meta:
        model = Subject
        fields = [
            'tenant', 'name', 'code', 'subject_type', 'subject_group',
            'description', 'has_practical', 'has_project', 'is_scoring',
            'credit_hours', 'max_marks', 'pass_marks', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ClassSubjectForm(BaseForm):
    class Meta:
        model = ClassSubject
        fields = [
            'tenant', 'class_name', 'subject', 'is_compulsory',
            'periods_per_week', 'teacher', 'academic_year'
        ]


class TimeTableForm(BaseForm):
    class Meta:
        model = TimeTable
        fields = [
            'tenant', 'class_name', 'section', 'academic_year', 'day',
            'period_number', 'start_time', 'end_time', 'subject',
            'teacher', 'room', 'period_type'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class AttendanceForm(BaseForm):
    class Meta:
        model = Attendance
        fields = [
            'tenant', 'student', 'date', 'status', 'class_name',
            'section', 'session', 'remarks', 'marked_by'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=_("Date")
    )
    session = forms.ChoiceField(
        choices=Attendance._meta.get_field('session').choices,
        initial='FULL_DAY',
        label=_("Session")
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.class_name = kwargs.pop('class_name', None)
        self.section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)


class HolidayForm(BaseForm):
    class Meta:
        model = Holiday
        fields = [
            'tenant', 'name', 'holiday_type', 'start_date', 'end_date',
            'description', 'academic_year', 'affected_classes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class StudyMaterialForm(BaseForm):
    class Meta:
        model = StudyMaterial
        fields = [
            'tenant', 'title', 'material_type', 'description', 'class_name',
            'subject', 'file', 'uploaded_by', 'is_published', 'publish_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class SyllabusForm(BaseForm):
    class Meta:
        model = Syllabus
        fields = [
            'tenant', 'class_name', 'subject', 'academic_year',
            'topics', 'recommended_books', 'reference_materials',
            'assessment_pattern'
        ]
        widgets = {
            'topics': forms.Textarea(attrs={'rows': 5}),
            'recommended_books': forms.Textarea(attrs={'rows': 3}),
            'reference_materials': forms.Textarea(attrs={'rows': 3}),
            'assessment_pattern': forms.Textarea(attrs={'rows': 5}),
        }


class StreamForm(BaseForm):
    class Meta:
        model = Stream
        fields = [
            'tenant', 'name', 'code', 'description', 'available_from_class',
            'subjects', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ClassTeacherForm(BaseForm):
    class Meta:
        model = ClassTeacher
        fields = [
            'tenant', 'class_name', 'section', 'teacher', 'academic_year',
            'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }