from django.contrib import admin
from .models import (
    AcademicYear, Term, SchoolClass, Section, House, HousePoints,
    Subject, ClassSubject, TimeTable, StudentAttendance, Holiday,
    StudyMaterial, Syllabus, Stream
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_date', 'end_date', 'is_current', 'has_terms')
    list_filter = ('is_current', 'has_terms')
    search_fields = ('name', 'code')

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'term_type', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'term_type', 'is_current')
    search_fields = ('name',)

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'level', 'class_teacher', 'is_active')
    list_filter = ('level', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_name', 'code', 'section_incharge', 'is_active')
    list_filter = ('class_name', 'is_active')
    search_fields = ('name', 'code')

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color', 'house_master', 'total_points')
    search_fields = ('name', 'code')

@admin.register(HousePoints)
class HousePointsAdmin(admin.ModelAdmin):
    list_display = ('house', 'points', 'activity', 'date_awarded', 'awarded_by')
    list_filter = ('house', 'date_awarded')
    search_fields = ('activity',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'subject_type', 'subject_group', 'is_active')
    list_filter = ('subject_type', 'subject_group', 'is_active')
    search_fields = ('name', 'code')

@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'subject', 'teacher', 'is_compulsory', 'academic_year')
    list_filter = ('class_name', 'subject', 'is_compulsory', 'academic_year')

@admin.register(TimeTable)
class TimeTableAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'section', 'day', 'period_number', 'subject', 'teacher', 'start_time', 'end_time')
    list_filter = ('class_name', 'section', 'day')

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'class_name', 'section', 'session')
    list_filter = ('date', 'status', 'class_name', 'section')
    search_fields = ('student__first_name', 'student__last_name')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'holiday_type', 'start_date', 'end_date', 'academic_year')
    list_filter = ('holiday_type', 'academic_year')
    search_fields = ('name',)

@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'material_type', 'class_name', 'subject', 'uploaded_by', 'is_published')
    list_filter = ('material_type', 'class_name', 'subject', 'is_published')
    search_fields = ('title',)

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'subject', 'academic_year')
    list_filter = ('class_name', 'subject', 'academic_year')

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'available_from_class', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
