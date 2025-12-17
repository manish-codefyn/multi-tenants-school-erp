from django.urls import reverse_lazy
from django.db.models import Count, Sum
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from apps.core.utils.tenant import get_current_tenant
from .models import Vehicle, Route, RouteStop, TransportAllocation, TransportAttendance, MaintenanceRecord, FuelRecord
from .forms import (
    VehicleForm, RouteForm, RouteStopForm, TransportAllocationForm, 
    TransportAttendanceForm, MaintenanceRecordForm, FuelRecordForm
)

class TransportationDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'transportation/dashboard.html'
    permission_required = 'transportation.view_vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Stats
        context['total_vehicles'] = Vehicle.objects.filter(tenant=tenant, is_active=True).count()
        context['total_routes'] = Route.objects.filter(tenant=tenant, is_active=True).count()
        context['total_allocations'] = TransportAllocation.objects.filter(tenant=tenant, is_active=True).count()
        context['maintenance_vehicles'] = Vehicle.objects.filter(tenant=tenant, under_maintenance=True).count()
        
        # Recent Activities
        context['recent_maintenance'] = MaintenanceRecord.objects.filter(tenant=tenant).select_related('vehicle').order_by('-maintenance_date')[:5]
        context['recent_fuel'] = FuelRecord.objects.filter(tenant=tenant).select_related('vehicle').order_by('-date')[:5]
        
        return context

# ==================== VEHICLE ====================

class VehicleListView(BaseListView):
    model = Vehicle
    template_name = 'transportation/vehicle_list.html'
    context_object_name = 'vehicles'
    permission_required = 'transportation.view_vehicle'
    search_fields = ['vehicle_number', 'registration_number', 'make', 'model']
    filter_fields = ['vehicle_type', 'fuel_type', 'status', 'is_active']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add import URL if vehicle import view exists, otherwise leave blank or create one later
        return context

class VehicleCreateView(BaseCreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transportation/vehicle_form.html'
    permission_required = 'transportation.add_vehicle'
    success_url = reverse_lazy('transportation:vehicle_list')

class VehicleUpdateView(BaseUpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'transportation/vehicle_form.html'
    permission_required = 'transportation.change_vehicle'
    success_url = reverse_lazy('transportation:vehicle_list')

class VehicleDeleteView(BaseDeleteView):
    model = Vehicle
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_vehicle'
    success_url = reverse_lazy('transportation:vehicle_list')

# ==================== ROUTE ====================

class RouteListView(BaseListView):
    model = Route
    template_name = 'transportation/route_list.html'
    context_object_name = 'routes'
    permission_required = 'transportation.view_route'
    search_fields = ['name', 'code', 'start_point', 'end_point']
    filter_fields = ['is_active']

class RouteCreateView(BaseCreateView):
    model = Route
    form_class = RouteForm
    template_name = 'transportation/route_form.html'
    permission_required = 'transportation.add_route'
    success_url = reverse_lazy('transportation:route_list')

class RouteUpdateView(BaseUpdateView):
    model = Route
    form_class = RouteForm
    template_name = 'transportation/route_form.html'
    permission_required = 'transportation.change_route'
    success_url = reverse_lazy('transportation:route_list')

class RouteDeleteView(BaseDeleteView):
    model = Route
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_route'
    success_url = reverse_lazy('transportation:route_list')

# ==================== ROUTE STOP ====================

class RouteStopListView(BaseListView):
    model = RouteStop
    template_name = 'transportation/stop_list.html'
    context_object_name = 'stops'
    permission_required = 'transportation.view_routestop'
    search_fields = ['stop_name', 'route__name']

class RouteStopCreateView(BaseCreateView):
    model = RouteStop
    form_class = RouteStopForm
    template_name = 'transportation/stop_form.html'
    permission_required = 'transportation.add_routestop'
    success_url = reverse_lazy('transportation:stop_list')

class RouteStopUpdateView(BaseUpdateView):
    model = RouteStop
    form_class = RouteStopForm
    template_name = 'transportation/stop_form.html'
    permission_required = 'transportation.change_routestop'
    success_url = reverse_lazy('transportation:stop_list')

class RouteStopDeleteView(BaseDeleteView):
    model = RouteStop
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_routestop'
    success_url = reverse_lazy('transportation:stop_list')

# ==================== ALLOCATION ====================

class TransportAllocationListView(BaseListView):
    model = TransportAllocation
    template_name = 'transportation/allocation_list.html'
    context_object_name = 'allocations'
    permission_required = 'transportation.view_transportallocation'
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number', 'route__name']
    filter_fields = ['is_active', 'is_fee_paid']

class TransportAllocationCreateView(BaseCreateView):
    model = TransportAllocation
    form_class = TransportAllocationForm
    template_name = 'transportation/allocation_form.html'
    permission_required = 'transportation.add_transportallocation'
    success_url = reverse_lazy('transportation:allocation_list')

class TransportAllocationUpdateView(BaseUpdateView):
    model = TransportAllocation
    form_class = TransportAllocationForm
    template_name = 'transportation/allocation_form.html'
    permission_required = 'transportation.change_transportallocation'
    success_url = reverse_lazy('transportation:allocation_list')

class TransportAllocationDeleteView(BaseDeleteView):
    model = TransportAllocation
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_transportallocation'
    success_url = reverse_lazy('transportation:allocation_list')


# ==================== ATTENDANCE ====================

class TransportAttendanceListView(BaseListView):
    model = TransportAttendance
    template_name = 'transportation/attendance_list.html'
    context_object_name = 'attendances'
    permission_required = 'transportation.view_transportattendance'
    search_fields = ['student__first_name', 'student__last_name']
    filter_fields = ['status', 'trip_type', 'date']

class TransportAttendanceCreateView(BaseCreateView):
    model = TransportAttendance
    form_class = TransportAttendanceForm
    template_name = 'transportation/attendance_form.html'
    permission_required = 'transportation.add_transportattendance'
    success_url = reverse_lazy('transportation:attendance_list')
    
    def form_valid(self, form):
        form.instance.marked_by = self.request.user
        return super().form_valid(form)

class TransportAttendanceUpdateView(BaseUpdateView):
    model = TransportAttendance
    form_class = TransportAttendanceForm
    template_name = 'transportation/attendance_form.html'
    permission_required = 'transportation.change_transportattendance'
    success_url = reverse_lazy('transportation:attendance_list')

class TransportAttendanceDeleteView(BaseDeleteView):
    model = TransportAttendance
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_transportattendance'
    success_url = reverse_lazy('transportation:attendance_list')


# ==================== MAINTENANCE ====================

class MaintenanceListView(BaseListView):
    model = MaintenanceRecord
    template_name = 'transportation/maintenance_list.html'
    context_object_name = 'records'
    permission_required = 'transportation.view_maintenancerecord'
    search_fields = ['vehicle__vehicle_number', 'workshop_name']
    filter_fields = ['maintenance_type', 'is_completed']

class MaintenanceCreateView(BaseCreateView):
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'transportation/maintenance_form.html'
    permission_required = 'transportation.add_maintenancerecord'
    success_url = reverse_lazy('transportation:maintenance_list')

class MaintenanceUpdateView(BaseUpdateView):
    model = MaintenanceRecord
    form_class = MaintenanceRecordForm
    template_name = 'transportation/maintenance_form.html'
    permission_required = 'transportation.change_maintenancerecord'
    success_url = reverse_lazy('transportation:maintenance_list')

class MaintenanceDeleteView(BaseDeleteView):
    model = MaintenanceRecord
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_maintenancerecord'
    success_url = reverse_lazy('transportation:maintenance_list')


# ==================== FUEL ====================

class FuelListView(BaseListView):
    model = FuelRecord
    template_name = 'transportation/fuel_list.html'
    context_object_name = 'records'
    permission_required = 'transportation.view_fuelrecord'
    search_fields = ['vehicle__vehicle_number', 'station_name']
    filter_fields = ['fuel_type']

class FuelCreateView(BaseCreateView):
    model = FuelRecord
    form_class = FuelRecordForm
    template_name = 'transportation/fuel_form.html'
    permission_required = 'transportation.add_fuelrecord'
    success_url = reverse_lazy('transportation:fuel_list')

class FuelUpdateView(BaseUpdateView):
    model = FuelRecord
    form_class = FuelRecordForm
    template_name = 'transportation/fuel_form.html'
    permission_required = 'transportation.change_fuelrecord'
    success_url = reverse_lazy('transportation:fuel_list')

class FuelDeleteView(BaseDeleteView):
    model = FuelRecord
    template_name = 'transportation/confirm_delete.html'
    permission_required = 'transportation.delete_fuelrecord'
    success_url = reverse_lazy('transportation:fuel_list')
