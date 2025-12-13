from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.utils.tenant import get_current_tenant
from .models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, Attendance, Holiday,
    StudyMaterial, Syllabus, Stream, ClassTeacher
)


# Academic Year Form
class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'code', 'start_date', 'end_date', 'is_current', 'has_terms']
        exclude = ['tenant']


# Term Form
class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'term_type', 'academic_year', 'start_date', 'end_date', 'order', 'is_current']
        exclude = ['tenant']


# School Class Form
class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'numeric_name', 'code', 'level', 'order', 'pass_percentage', 'max_strength', 'tuition_fee', 'class_teacher', 'is_active']
        exclude = ['tenant']


# Section Form
class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'code', 'class_name', 'max_strength', 'section_incharge', 'room_number', 'is_active']
        exclude = ['tenant']


# House Form
class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'code', 'color', 'motto', 'description', 'house_master', 'logo']
        exclude = ['tenant', 'total_points']


# House Points Form
class HousePointsForm(forms.ModelForm):
    class Meta:
        model = HousePoints
        fields = ['house', 'points', 'activity', 'description', 'date_awarded']
        exclude = ['tenant', 'awarded_by']


# Subject Form
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'subject_type', 'subject_group', 'description', 'has_practical', 'has_project', 'is_scoring', 'credit_hours', 'max_marks', 'pass_marks', 'is_active']
        exclude = ['tenant']


# Class Subject Form
class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ['class_name', 'subject', 'is_compulsory', 'periods_per_week', 'teacher', 'academic_year']
        exclude = ['tenant']


# TimeTable Form
class TimeTableForm(forms.ModelForm):
    class Meta:
        model = TimeTable
        fields = ['class_name', 'section', 'academic_year', 'day', 'period_number', 'start_time', 'end_time', 'subject', 'teacher', 'room', 'period_type']
        exclude = ['tenant']


# Attendance Form
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'class_name', 'section', 'session', 'remarks', 'marked_by']
        exclude = ['tenant']


# Bulk Attendance Form
class BulkAttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    class_name = forms.ModelChoiceField(queryset=SchoolClass.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    section = forms.ModelChoiceField(queryset=Section.objects.none(), widget=forms.Select(attrs={'class': 'form-control'}))
    session = forms.ChoiceField(
        choices=(
            ("MORNING", "Morning"),
            ("AFTERNOON", "Afternoon"),
            ("FULL_DAY", "Full Day"),
        ), 
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# Holiday Form
class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'holiday_type', 'start_date', 'end_date', 'description', 'academic_year', 'affected_classes']
        exclude = ['tenant']


# Study Material Form
class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'material_type', 'description', 'class_name', 'subject', 'file', 'is_published', 'publish_date']
        exclude = ['tenant', 'file_size', 'uploaded_by']


# Syllabus Form
class SyllabusForm(forms.ModelForm):
    class Meta:
        model = Syllabus
        fields = ['class_name', 'subject', 'academic_year', 'topics', 'recommended_books', 'reference_materials', 'assessment_pattern']
        exclude = ['tenant']


# Stream Form
class StreamForm(forms.ModelForm):
    class Meta:
        model = Stream
        fields = ['name', 'code', 'description', 'available_from_class', 'subjects', 'is_active']
        exclude = ['tenant']


# Class Teacher Form
class ClassTeacherForm(forms.ModelForm):
    class Meta:
        model = ClassTeacher
        fields = ['class_name', 'section', 'teacher', 'academic_year', 'start_date', 'end_date', 'is_active']
        exclude = ['tenant']