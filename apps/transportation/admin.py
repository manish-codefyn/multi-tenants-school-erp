from django.contrib import admin
from .models import (
    Vehicle, Route, RouteStop, TransportAllocation,
    TransportAttendance, MaintenanceRecord, FuelRecord
)

class MaintenanceRecordInline(admin.TabularInline):
    model = MaintenanceRecord
    extra = 0

class FuelRecordInline(admin.TabularInline):
    model = FuelRecord
    extra = 0

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'vehicle_type', 'make', 'model', 'seating_capacity', 'is_active', 'under_maintenance')
    list_filter = ('vehicle_type', 'fuel_type', 'is_active', 'under_maintenance')
    search_fields = ('vehicle_number', 'registration_number', 'driver__first_name')
    inlines = [MaintenanceRecordInline, FuelRecordInline]

class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 1
    ordering = ('sequence',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_point', 'end_point', 'vehicle', 'driver', 'is_active')
    list_filter = ('is_active', 'vehicle')
    search_fields = ('name', 'code', 'driver__first_name')
    inlines = [RouteStopInline]

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ('route', 'stop_name', 'sequence', 'pickup_time', 'drop_time')
    list_filter = ('route',)
    search_fields = ('stop_name', 'route__name')

@admin.register(TransportAllocation)
class TransportAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'route', 'pickup_stop', 'drop_stop', 'is_active', 'is_fee_paid')
    list_filter = ('route', 'is_active', 'is_fee_paid')
    search_fields = ('student__first_name', 'student__last_name', 'route__name')

@admin.register(TransportAttendance)
class TransportAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'trip_type', 'status', 'actual_time')
    list_filter = ('date', 'trip_type', 'status')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'date'

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'maintenance_type', 'maintenance_date', 'total_cost', 'is_completed')
    list_filter = ('maintenance_type', 'is_completed', 'maintenance_date')
    search_fields = ('vehicle__vehicle_number', 'workshop_name')
    date_hierarchy = 'maintenance_date'

@admin.register(FuelRecord)
class FuelRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'fuel_type', 'quantity', 'total_cost', 'mileage')
    list_filter = ('fuel_type', 'date')
    search_fields = ('vehicle__vehicle_number', 'station_name')
    date_hierarchy = 'date'
