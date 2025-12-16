from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, Qualification, Designation, Staff, StaffAddress,
    StaffDocument, StaffAttendance, LeaveType, LeaveApplication,
    LeaveBalance, SalaryStructure, Payroll, Promotion,
    EmploymentHistory, TrainingProgram, TrainingParticipation,
    PerformanceReview, Recruitment, JobApplication,
    Holiday, WorkSchedule, TaxConfig, PFESIConfig
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "head_of_department", "staff_count")
    search_fields = ("name", "code")
    list_filter = ("name",)


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ("degree", "specialization", "institution", "year")
    list_filter = ("degree",)
    search_fields = ("degree", "specialization", "institution")

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = (
        "get_title_display",
        "category",
        "grade",
        "min_salary",
        "max_salary",
        "current_holders_count",
    )
    list_filter = ("category", "grade")
    search_fields = ("title", "code")
    filter_horizontal = ("qualifications",)
    readonly_fields = ("code",)

class StaffAddressInline(admin.TabularInline):
    model = StaffAddress
    extra = 1
    fields = (
        "address_type",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "pincode",
        "country",
        "is_current",
    )


class StaffDocumentInline(admin.TabularInline):
    model = StaffDocument
    extra = 0

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "full_name",
        "department",
        "designation",
        "employment_status",
        "employment_type",
    )
    list_filter = (
        "department",
        "designation",
        "employment_status",
        "employment_type",
    )
    search_fields = (
        "employee_id",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    readonly_fields = ("employee_id",)
    filter_horizontal = ("qualifications",)
    inlines = [StaffAddressInline, StaffDocumentInline]

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ("staff", "date", "status", "check_in", "check_out")
    list_filter = ("status", "date")
    search_fields = ("staff__employee_id",)

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "max_days_per_year", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "start_date", "end_date", "status")
    list_filter = ("status", "leave_type")
    search_fields = ("staff__employee_id",)


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ("staff", "effective_from", "net_salary", "is_active")
    list_filter = ("is_active",)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("staff", "salary_month", "net_salary", "status")
    list_filter = ("status", "salary_month")

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("staff", "previous_designation", "new_designation", "effective_date")


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("staff", "action", "effective_date")
    list_filter = ("action",)

@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "training_type", "start_date", "status")
    list_filter = ("training_type", "status")


@admin.register(TrainingParticipation)
class TrainingParticipationAdmin(admin.ModelAdmin):
    list_display = ("staff", "training", "status", "certificate_issued")

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ("staff", "review_type", "overall_rating", "review_date")
    list_filter = ("review_type",)

@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ("position_title", "department", "status", "posting_date")
    list_filter = ("status", "department")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "recruitment", "status", "applied_date")
    list_filter = ("status",)

