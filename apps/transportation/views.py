from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Vehicle, Route, TransportAllocation

class TransportationDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'transportation/dashboard.html'
    permission_required = 'transportation.view_vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_vehicles'] = Vehicle.objects.filter(tenant=tenant, is_active=True).count()
        context['total_routes'] = Route.objects.filter(tenant=tenant, is_active=True).count()
        context['total_allocations'] = TransportAllocation.objects.filter(tenant=tenant, is_active=True).count()
        context['under_maintenance'] = Vehicle.objects.filter(tenant=tenant, under_maintenance=True).count()
        
        return context

# ==================== VEHICLE ====================

class VehicleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Vehicle
    template_name = 'transportation/vehicle_list.html'
    context_object_name = 'vehicles'
    permission_required = 'transportation.view_vehicle'

class VehicleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Vehicle
    fields = ['vehicle_number', 'vehicle_type', 'make', 'model', 'year', 'color', 
              'fuel_type', 'seating_capacity', 'registration_number', 'registration_date', 
              'registration_expiry', 'insurance_company', 'insurance_number', 'insurance_expiry', 
              'fitness_certificate_number', 'fitness_expiry', 'driver', 'is_active']
    template_name = 'transportation/vehicle_form.html'
    success_url = reverse_lazy('transportation:vehicle_list')
    permission_required = 'transportation.add_vehicle'

    def form_valid(self, form):
        messages.success(self.request, "Vehicle created successfully.")
        return super().form_valid(form)

class VehicleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Vehicle
    fields = ['vehicle_number', 'vehicle_type', 'make', 'model', 'year', 'color', 
              'fuel_type', 'seating_capacity', 'registration_number', 'registration_date', 
              'registration_expiry', 'insurance_company', 'insurance_number', 'insurance_expiry', 
              'fitness_certificate_number', 'fitness_expiry', 'driver', 'is_active', 'under_maintenance']
    template_name = 'transportation/vehicle_form.html'
    success_url = reverse_lazy('transportation:vehicle_list')
    permission_required = 'transportation.change_vehicle'

    def form_valid(self, form):
        messages.success(self.request, "Vehicle updated successfully.")
        return super().form_valid(form)

class VehicleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'transportation/confirm_delete.html'
    success_url = reverse_lazy('transportation:vehicle_list')
    permission_required = 'transportation.delete_vehicle'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Vehicle deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== ROUTE ====================

class RouteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Route
    template_name = 'transportation/route_list.html'
    context_object_name = 'routes'
    permission_required = 'transportation.view_route'

class RouteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Route
    fields = ['name', 'code', 'start_point', 'end_point', 'total_distance', 
              'estimated_duration', 'vehicle', 'driver', 'attendant', 'monthly_fee', 'is_active']
    template_name = 'transportation/route_form.html'
    success_url = reverse_lazy('transportation:route_list')
    permission_required = 'transportation.add_route'

    def form_valid(self, form):
        messages.success(self.request, "Route created successfully.")
        return super().form_valid(form)

class RouteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Route
    fields = ['name', 'code', 'start_point', 'end_point', 'total_distance', 
              'estimated_duration', 'vehicle', 'driver', 'attendant', 'monthly_fee', 'is_active']
    template_name = 'transportation/route_form.html'
    success_url = reverse_lazy('transportation:route_list')
    permission_required = 'transportation.change_route'

    def form_valid(self, form):
        messages.success(self.request, "Route updated successfully.")
        return super().form_valid(form)

class RouteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Route
    template_name = 'transportation/confirm_delete.html'
    success_url = reverse_lazy('transportation:route_list')
    permission_required = 'transportation.delete_route'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Route deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== TRANSPORT ALLOCATION ====================

class TransportAllocationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TransportAllocation
    template_name = 'transportation/allocation_list.html'
    context_object_name = 'allocations'
    permission_required = 'transportation.view_transportallocation'

class TransportAllocationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TransportAllocation
    fields = ['student', 'route', 'pickup_stop', 'drop_stop', 'allocation_date', 
              'valid_until', 'monthly_fee', 'is_active']
    template_name = 'transportation/allocation_form.html'
    success_url = reverse_lazy('transportation:allocation_list')
    permission_required = 'transportation.add_transportallocation'

    def form_valid(self, form):
        messages.success(self.request, "Transport allocation created successfully.")
        return super().form_valid(form)

class TransportAllocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TransportAllocation
    fields = ['student', 'route', 'pickup_stop', 'drop_stop', 'allocation_date', 
              'valid_until', 'monthly_fee', 'is_fee_paid', 'is_active']
    template_name = 'transportation/allocation_form.html'
    success_url = reverse_lazy('transportation:allocation_list')
    permission_required = 'transportation.change_transportallocation'

    def form_valid(self, form):
        messages.success(self.request, "Transport allocation updated successfully.")
        return super().form_valid(form)

class TransportAllocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TransportAllocation
    template_name = 'transportation/confirm_delete.html'
    success_url = reverse_lazy('transportation:allocation_list')
    permission_required = 'transportation.delete_transportallocation'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Transport allocation deleted successfully.")
        return super().delete(request, *args, **kwargs)
