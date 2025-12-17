from django import forms
from apps.core.forms import TenantAwareModelForm
from .models import Vehicle, Route, RouteStop, TransportAllocation, TransportAttendance, MaintenanceRecord, FuelRecord

class VehicleForm(TenantAwareModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_number', 'vehicle_type', 'make', 'model', 'year', 'color',
            'fuel_type', 'seating_capacity', 'registration_number', 'registration_date',
            'registration_expiry', 'insurance_company', 'insurance_number', 'insurance_expiry',
            'fitness_certificate_number', 'fitness_expiry', 'driver', 'under_maintenance', 'is_active'
        ]
        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'registration_expiry': forms.DateInput(attrs={'type': 'date'}),
            'insurance_expiry': forms.DateInput(attrs={'type': 'date'}),
            'fitness_expiry': forms.DateInput(attrs={'type': 'date'}),
        }

class RouteForm(TenantAwareModelForm):
    class Meta:
        model = Route
        fields = [
            'name', 'code', 'start_point', 'end_point', 'total_distance',
            'estimated_duration', 'vehicle', 'driver', 'attendant', 'monthly_fee', 'is_active'
        ]

class RouteStopForm(TenantAwareModelForm):
    class Meta:
        model = RouteStop
        fields = [
            'route', 'stop_name', 'sequence', 'pickup_time',
            'drop_time', 'landmark', 'latitude', 'longitude'
        ]
        widgets = {
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'drop_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class TransportAllocationForm(TenantAwareModelForm):
    class Meta:
        model = TransportAllocation
        fields = [
            'student', 'route', 'pickup_stop', 'drop_stop', 
            'allocation_date', 'valid_until', 'monthly_fee', 
            'is_fee_paid', 'is_active'
        ]
        widgets = {
            'allocation_date': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

class TransportAttendanceForm(TenantAwareModelForm):
    class Meta:
        model = TransportAttendance
        fields = [
            'student', 'date', 'trip_type', 'status', 
            'actual_time', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'actual_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class MaintenanceRecordForm(TenantAwareModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 'maintenance_type', 'description', 'maintenance_date',
            'next_maintenance_date', 'workshop_name', 'workshop_contact',
            'labor_cost', 'parts_cost', 'odometer_reading', 'is_completed'
        ]
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }

class FuelRecordForm(TenantAwareModelForm):
    class Meta:
        model = FuelRecord
        fields = [
            'vehicle', 'date', 'fuel_type', 'quantity', 
            'rate_per_liter', 'odometer_reading', 'station_name', 'receipt_number'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
