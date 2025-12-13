# apps/students/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Student, Guardian, StudentAddress, StudentDocument,
    StudentMedicalInfo, StudentAcademicHistory, StudentIdentification
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'admission_number', 'full_name', 'personal_email',
        'current_class', 'status', 'created_at'
    ]
    list_filter = ['status', 'gender', 'current_class', 'academic_year']
    search_fields = [
        'admission_number', 'first_name', 'last_name',
        'personal_email', 'mobile_primary'
    ]
    readonly_fields = ['created_at', 'updated_at', 'status_changed_date']
    fieldsets = (
        (_('Personal Information'), {
            'fields': (
                'first_name', 'middle_name', 'last_name',
                'date_of_birth', 'gender', 'blood_group',
                'nationality', 'marital_status'
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'personal_email', 'institutional_email',
                'mobile_primary', 'mobile_secondary'
            )
        }),
        (_('Academic Information'), {
            'fields': (
                'admission_number', 'roll_number', 'university_reg_no',
                'admission_type', 'enrollment_date', 'academic_year',
                'current_class', 'section', 'current_semester'
            )
        }),
        (_('Academic Performance'), {
            'fields': (
                'total_credits_earned', 'cumulative_grade_point'
            )
        }),
        (_('Status'), {
            'fields': (
                'status', 'status_changed_date', 'graduation_date'
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'category', 'religion', 'is_minority',
                'is_physically_challenged', 'annual_family_income',
                'fee_category', 'scholarship_type'
            )
        }),
    )


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'relation', 'student', 'is_primary', 'phone_primary']
    list_filter = ['relation', 'is_primary', 'occupation']
    search_fields = ['full_name', 'phone_primary', 'email', 'student__admission_number']


@admin.register(StudentAddress)
class StudentAddressAdmin(admin.ModelAdmin):
    list_display = ['student', 'address_type', 'city', 'state', 'is_current']
    list_filter = ['address_type', 'is_current', 'is_verified']
    search_fields = ['student__admission_number', 'city', 'state']


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'doc_type', 'status', 'is_verified', 'created_at']
    list_filter = ['doc_type', 'status', 'is_verified']
    search_fields = ['student__admission_number', 'file_name']
    readonly_fields = ['file_size', 'file_hash', 'version']


@admin.register(StudentMedicalInfo)
class StudentMedicalInfoAdmin(admin.ModelAdmin):
    list_display = ['student', 'blood_group', 'has_disability', 'has_medical_insurance']
    search_fields = ['student__admission_number']
    readonly_fields = ['bmi']


@admin.register(StudentAcademicHistory)
class StudentAcademicHistoryAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'class_name', 'result', 'percentage']
    list_filter = ['academic_year', 'result']
    search_fields = ['student__admission_number']


@admin.register(StudentIdentification)
class StudentIdentificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'aadhaar_verified', 'pan_verified']
    search_fields = ['student__admission_number']