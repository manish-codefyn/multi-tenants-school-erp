from django import forms
from apps.core.forms import TenantAwareModelForm
from .models import ExamType, Exam, GradingSystem, ExamSubject, Grade

class ExamTypeForm(TenantAwareModelForm):
    class Meta:
        model = ExamType
        fields = ['name', 'code', 'description', 'weightage', 'is_final', 'order', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExamForm(TenantAwareModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'code', 'exam_type', 'academic_year', 'class_name', 'start_date', 
                  'end_date', 'exam_mode', 'total_marks', 'pass_percentage', 'grace_marks', 
                  'status', 'instructions', 'is_published']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }

class GradingSystemForm(TenantAwareModelForm):
    class Meta:
        model = GradingSystem
        fields = ['name', 'code', 'description', 'is_active', 'is_default']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class GradeForm(TenantAwareModelForm):
    class Meta:
        model = Grade
        fields = ['grade', 'grade_point', 'min_percentage', 'max_percentage', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
