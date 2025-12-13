from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    AdmissionCycle, AdmissionProgram, OnlineApplication, 
    ApplicationDocument, ApplicationGuardian, ApplicationLog,
    MeritList, MeritListEntry, AdmissionFormConfig, AdmissionStatistics
)


@admin.register(AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'code', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'is_active', 'academic_year']
    search_fields = ['name', 'code']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdmissionProgram)
class AdmissionProgramAdmin(admin.ModelAdmin):
    list_display = ['program_type', 'admission_cycle', 'total_seats', 'filled_seats', 'is_active']
    list_filter = ['program_type', 'is_active', 'admission_cycle']
    search_fields = ['program_type', 'admission_cycle__name']
    readonly_fields = ['filled_seats', 'available_seats']


@admin.register(OnlineApplication)
class OnlineApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'full_name', 'program', 'status', 'submission_date', 'application_fee_paid']
    list_filter = ['status', 'program', 'admission_cycle', 'category', 'gender']
    search_fields = ['application_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['application_number', 'submission_date', 'review_date', 'decision_date']
    date_hierarchy = 'created_at'


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'is_verified', 'verified_by', 'verified_at']
    list_filter = ['document_type', 'is_verified']
    search_fields = ['application__application_number']


@admin.register(MeritList)
class MeritListAdmin(admin.ModelAdmin):
    list_display = ['name', 'admission_cycle', 'program', 'category', 'is_published']
    list_filter = ['is_published', 'category', 'admission_cycle']
    search_fields = ['name', 'program__course__name']


@admin.register(AdmissionStatistics)
class AdmissionStatisticsAdmin(admin.ModelAdmin):
    list_display = ['admission_cycle', 'program', 'total_applications', 'admitted_applications', 'conversion_rate']
    list_filter = ['admission_cycle']
    readonly_fields = ['last_updated', 'conversion_rate']

    def conversion_rate(self, obj):
        return f"{obj.conversion_rate:.2f}%"
    conversion_rate.short_description = _("Conversion Rate")

@admin.register(ApplicationGuardian)
class ApplicationGuardianAdmin(admin.ModelAdmin):
    list_display = ['application',  'phone', 'is_primary']
    list_filter = ['is_primary']
    search_fields = [ 'phone', 'application__application_number']

@admin.register(ApplicationLog)
class ApplicationLogAdmin(admin.ModelAdmin):
    list_display = ['application', 'action', 'created_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['application__application_number', 'description']
    readonly_fields = ['created_at']

@admin.register(MeritListEntry)
class MeritListEntryAdmin(admin.ModelAdmin):
    list_display = ['merit_list', 'application', 'rank']
    list_filter = ['merit_list']
    search_fields = ['application__application_number', 'application__first_name']

@admin.register(AdmissionFormConfig)
class AdmissionFormConfigAdmin(admin.ModelAdmin):
    list_display = ['admission_cycle', 'is_active']
    list_filter = ['is_active', 'admission_cycle']