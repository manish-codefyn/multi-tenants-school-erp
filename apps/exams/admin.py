from django.contrib import admin
from .models import (
    ExamType, Exam, ExamSubject, GradingSystem, Grade,
    ExamResult, SubjectResult, MarkSheet
)

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'weightage', 'is_final', 'is_active')
    list_filter = ('is_final', 'is_active')
    search_fields = ('name', 'code')

class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'exam_type', 'academic_year', 'class_name', 'start_date', 'status', 'is_published')
    list_filter = ('status', 'is_published', 'exam_type', 'academic_year', 'class_name')
    search_fields = ('name', 'code')
    inlines = [ExamSubjectInline]
    date_hierarchy = 'start_date'

@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('exam', 'subject', 'exam_date', 'start_time', 'max_marks', 'pass_marks')
    list_filter = ('exam', 'subject', 'exam_date')
    search_fields = ('exam__name', 'subject__name')

class GradeInline(admin.TabularInline):
    model = Grade
    extra = 1

@admin.register(GradingSystem)
class GradingSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'is_default')
    list_filter = ('is_active', 'is_default')
    inlines = [GradeInline]

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('grading_system', 'grade', 'min_percentage', 'max_percentage', 'grade_point')
    list_filter = ('grading_system',)

class SubjectResultInline(admin.TabularInline):
    model = SubjectResult
    extra = 0

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'total_marks_obtained', 'percentage', 'overall_grade', 'result_status', 'rank')
    list_filter = ('result_status', 'exam', 'overall_grade')
    search_fields = ('student__first_name', 'student__last_name', 'exam__name')
    inlines = [SubjectResultInline]

@admin.register(SubjectResult)
class SubjectResultAdmin(admin.ModelAdmin):
    list_display = ('exam_result', 'exam_subject', 'total_marks_obtained', 'grade', 'is_pass')
    list_filter = ('is_pass', 'grade')
    search_fields = ('exam_result__student__first_name', 'exam_subject__subject__name')

@admin.register(MarkSheet)
class MarkSheetAdmin(admin.ModelAdmin):
    list_display = ('mark_sheet_number', 'exam_result', 'issue_date', 'is_issued')
    list_filter = ('is_issued', 'issue_date')
    search_fields = ('mark_sheet_number', 'exam_result__student__first_name')
