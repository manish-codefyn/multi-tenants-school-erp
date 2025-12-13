from django.contrib import admin
from .models import (
    Hostel, Room, HostelAllocation, HostelAttendance,
    LeaveApplication, MessMenu
)

@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'hostel_type', 'warden', 'total_rooms', 'total_capacity', 'is_active')
    list_filter = ('hostel_type', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'hostel', 'floor', 'room_type', 'total_beds', 'current_occupancy', 'is_available')
    list_filter = ('hostel', 'room_type', 'is_available')
    search_fields = ('room_number', 'hostel__name')

@admin.register(HostelAllocation)
class HostelAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'hostel', 'room', 'bed_number', 'allocation_date', 'is_active')
    list_filter = ('hostel', 'is_active', 'allocation_date')
    search_fields = ('student__first_name', 'student__last_name', 'hostel__name', 'room__room_number')

@admin.register(HostelAttendance)
class HostelAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'check_in_time', 'check_out_time')
    list_filter = ('date', 'status')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'date'

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'leave_type', 'from_date', 'to_date', 'status')
    list_filter = ('status', 'leave_type', 'from_date')
    search_fields = ('student__first_name', 'student__last_name')

@admin.register(MessMenu)
class MessMenuAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'day', 'meal_type', 'effective_from', 'effective_to')
    list_filter = ('hostel', 'day', 'meal_type')
