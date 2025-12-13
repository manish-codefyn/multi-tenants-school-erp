from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Hostel, Room, HostelAllocation, LeaveApplication

class HostelDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'hostel/dashboard.html'
    permission_required = 'hostel.view_hostel'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_hostels'] = Hostel.objects.filter(tenant=tenant, is_active=True).count()
        context['total_rooms'] = Room.objects.filter(tenant=tenant).count()
        context['total_allocations'] = HostelAllocation.objects.filter(tenant=tenant, is_active=True).count()
        context['pending_leaves'] = LeaveApplication.objects.filter(tenant=tenant, status='PENDING').count()
        
        return context

# ==================== HOSTEL ====================

class HostelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Hostel
    template_name = 'hostel/hostel_list.html'
    context_object_name = 'hostels'
    permission_required = 'hostel.view_hostel'

class HostelDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Hostel
    template_name = 'hostel/hostel_detail.html'
    context_object_name = 'hostel'
    permission_required = 'hostel.view_hostel'

class HostelCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Hostel
    fields = ['name', 'code', 'hostel_type', 'address', 'contact_number', 'email', 
              'total_rooms', 'total_capacity', 'warden', 'hostel_fee', 'security_deposit', 
              'rules_regulations', 'is_active']
    template_name = 'hostel/hostel_form.html'
    success_url = reverse_lazy('hostel:hostel_list')
    permission_required = 'hostel.add_hostel'

    def form_valid(self, form):
        messages.success(self.request, "Hostel created successfully.")
        return super().form_valid(form)

class HostelUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Hostel
    fields = ['name', 'code', 'hostel_type', 'address', 'contact_number', 'email', 
              'total_rooms', 'total_capacity', 'warden', 'hostel_fee', 'security_deposit', 
              'rules_regulations', 'is_active']
    template_name = 'hostel/hostel_form.html'
    success_url = reverse_lazy('hostel:hostel_list')
    permission_required = 'hostel.change_hostel'

    def form_valid(self, form):
        messages.success(self.request, "Hostel updated successfully.")
        return super().form_valid(form)

class HostelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Hostel
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel:hostel_list')
    permission_required = 'hostel.delete_hostel'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Hostel deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== ROOM ====================

class RoomListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Room
    template_name = 'hostel/room_list.html'
    context_object_name = 'rooms'
    permission_required = 'hostel.view_room'

class RoomCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Room
    fields = ['hostel', 'room_number', 'room_type', 'floor', 'total_beds', 'is_available', 'under_maintenance']
    template_name = 'hostel/room_form.html'
    success_url = reverse_lazy('hostel:room_list')
    permission_required = 'hostel.add_room'

    def form_valid(self, form):
        messages.success(self.request, "Room created successfully.")
        return super().form_valid(form)

class RoomUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Room
    fields = ['hostel', 'room_number', 'room_type', 'floor', 'total_beds', 'is_available', 'under_maintenance']
    template_name = 'hostel/room_form.html'
    success_url = reverse_lazy('hostel:room_list')
    permission_required = 'hostel.change_room'

    def form_valid(self, form):
        messages.success(self.request, "Room updated successfully.")
        return super().form_valid(form)

class RoomDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Room
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel:room_list')
    permission_required = 'hostel.delete_room'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Room deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== HOSTEL ALLOCATION ====================

class HostelAllocationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = HostelAllocation
    template_name = 'hostel/allocation_list.html'
    context_object_name = 'allocations'
    permission_required = 'hostel.view_hostelallocation'

class HostelAllocationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = HostelAllocation
    fields = ['student', 'hostel', 'room', 'bed_number', 'allocation_date', 
              'expected_vacate_date', 'monthly_fee', 'security_deposit_paid']
    template_name = 'hostel/allocation_form.html'
    success_url = reverse_lazy('hostel:allocation_list')
    permission_required = 'hostel.add_hostelallocation'

    def form_valid(self, form):
        messages.success(self.request, "Hostel allocation created successfully.")
        return super().form_valid(form)

class HostelAllocationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = HostelAllocation
    fields = ['student', 'hostel', 'room', 'bed_number', 'allocation_date', 
              'expected_vacate_date', 'monthly_fee', 'security_deposit_paid', 'is_active']
    template_name = 'hostel/allocation_form.html'
    success_url = reverse_lazy('hostel:allocation_list')
    permission_required = 'hostel.change_hostelallocation'

    def form_valid(self, form):
        messages.success(self.request, "Hostel allocation updated successfully.")
        return super().form_valid(form)

class HostelAllocationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = HostelAllocation
    template_name = 'hostel/confirm_delete.html'
    success_url = reverse_lazy('hostel:allocation_list')
    permission_required = 'hostel.delete_hostelallocation'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Hostel allocation deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== LEAVE APPLICATION ====================

class LeaveApplicationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LeaveApplication
    template_name = 'hostel/leave_list.html'
    context_object_name = 'leaves'
    permission_required = 'hostel.view_leaveapplication'

class LeaveApplicationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LeaveApplication
    fields = ['student', 'leave_type', 'purpose', 'from_date', 'to_date', 
              'destination', 'contact_number', 'guardian_name', 'guardian_contact']
    template_name = 'hostel/leave_form.html'
    success_url = reverse_lazy('hostel:leave_list')
    permission_required = 'hostel.add_leaveapplication'

    def form_valid(self, form):
        messages.success(self.request, "Leave application submitted successfully.")
        return super().form_valid(form)

class LeaveApplicationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LeaveApplication
    fields = ['student', 'leave_type', 'purpose', 'from_date', 'to_date', 
              'destination', 'contact_number', 'guardian_name', 'guardian_contact', 'status']
    template_name = 'hostel/leave_form.html'
    success_url = reverse_lazy('hostel:leave_list')
    permission_required = 'hostel.change_leaveapplication'

    def form_valid(self, form):
        messages.success(self.request, "Leave application updated successfully.")
        return super().form_valid(form)
