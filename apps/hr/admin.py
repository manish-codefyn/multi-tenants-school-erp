from django.contrib import admin
from .models import (
    Department, Designation, Staff, StaffAddress, StaffDocument,
    StaffAttendance, LeaveType, LeaveApplication, LeaveBalance
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head_of_department', 'email', 'phone')
    search_fields = ('name', 'code')

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'category', 'grade', 'reports_to')
    list_filter = ('category',)
    search_fields = ('title', 'code')

class StaffAddressInline(admin.StackedInline):
    model = StaffAddress
    extra = 0

class StaffDocumentInline(admin.TabularInline):
    model = StaffDocument
    extra = 0

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'department', 'designation', 'employment_type', 'employment_status', 'joining_date')
    list_filter = ('employment_status', 'employment_type', 'department', 'designation')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email')
    inlines = [StaffAddressInline, StaffDocumentInline]
    date_hierarchy = 'joining_date'

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'status', 'check_in', 'check_out', 'total_hours')
    list_filter = ('date', 'status', 'staff__department')
    search_fields = ('staff__user__first_name', 'staff__user__last_name', 'staff__employee_id')
    date_hierarchy = 'date'

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'max_days_per_year', 'is_active')
    list_filter = ('is_active',)

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('staff', 'leave_type', 'start_date', 'end_date', 'total_days', 'status')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('staff__user__first_name', 'staff__user__last_name')
    date_hierarchy = 'start_date'

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'leave_type', 'year', 'total_entitled', 'used_days', 'available_days')
    list_filter = ('year', 'leave_type')
    search_fields = ('staff__user__first_name', 'staff__user__last_name')
