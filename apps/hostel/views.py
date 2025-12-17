import csv
import openpyxl
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib import messages
from django.views.generic import FormView
from .models import (
    Hostel, Room, HostelAllocation, LeaveApplication, HostelAttendance,
    Amenity, Facility, MessMenuCategory, MessMenuItem, DailyMessMenu,
    HostelMessSubscription
)
from .forms import (
    HostelForm, RoomForm, HostelAllocationForm, 
    LeaveApplicationForm, HostelAttendanceForm, ImportFileForm,
    AmenityForm, FacilityForm, MessMenuCategoryForm, MessMenuItemForm,
    DailyMessMenuForm, HostelMessSubscriptionForm
)
from apps.core.views import (
    BaseTemplateView, BaseListView, BaseDetailView, 
    BaseCreateView, BaseUpdateView, BaseDeleteView
)
from apps.core.utils.tenant import get_current_tenant
from apps.students.models import Student

# ==================== DASHBOARD ====================

class HostelDashboardView(BaseTemplateView):
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

# ==================== IMPORT BASE VIEW ====================

class BaseImportView(FormView):
    form_class = ImportFileForm
    template_name = 'hostel/import_form.html'
    permission_required = None 
    success_url = None
    model = None
    import_fields = [] 

    def form_valid(self, form):
        file = form.cleaned_data['file']
        tenant = get_current_tenant()
        
        try:
            if file.name.endswith('.csv'):
                data = self.read_csv(file)
            else:
                data = self.read_excel(file)
            
            success_count, error_count, errors = self.process_data(data, tenant)
            
            if success_count > 0:
                messages.success(self.request, f"Successfully imported {success_count} records.")
            if error_count > 0:
                messages.warning(self.request, f"Failed to import {error_count} records. Check errors below.")
                for err in errors[:10]:
                    messages.error(self.request, err)
            
        except Exception as e:
            messages.error(self.request, f"Error processing file: {str(e)}")
            
        return redirect(self.success_url)

    def read_csv(self, file):
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        return list(reader)

    def read_excel(self, file):
        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_dict = dict(zip(headers, row))
            data.append(row_dict)
        return data

    def process_data(self, data, tenant):
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in enumerate(data):
            try:
                self.process_row(row, tenant)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return success_count, error_count, errors

    def process_row(self, row, tenant):
        raise NotImplementedError("Subclasses must implement process_row")

# ==================== HOSTEL ====================

class HostelListView(BaseListView):
    model = Hostel
    template_name = 'hostel/hostel_list.html'
    context_object_name = 'hostels'
    permission_required = 'hostel.view_hostel'
    search_fields = ['name', 'code', 'warden__username']
    filterset_fields = ['hostel_type', 'is_active']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_url'] = reverse_lazy('hostel:hostel_import')
        return context

class HostelDetailView(BaseDetailView):
    model = Hostel
    template_name = 'hostel/hostel_detail.html'
    context_object_name = 'hostel'
    permission_required = 'hostel.view_hostel'

class HostelCreateView(BaseCreateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/hostel_form.html'
    permission_required = 'hostel.add_hostel'
    success_url_name = 'hostel:hostel_list'

class HostelUpdateView(BaseUpdateView):
    model = Hostel
    form_class = HostelForm
    template_name = 'hostel/hostel_form.html'
    permission_required = 'hostel.change_hostel'
    success_url_name = 'hostel:hostel_list'

class HostelDeleteView(BaseDeleteView):
    model = Hostel
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_hostel'
    success_url_name = 'hostel:hostel_list'

class HostelImportView(BaseImportView):
    permission_required = 'hostel.add_hostel'
    success_url = reverse_lazy('hostel:hostel_list')
    
    def process_row(self, row, tenant):
        code = row.get('code')
        if not code:
            raise Exception("Code is required")
            
        Hostel.objects.update_or_create(
            tenant=tenant,
            code=code,
            defaults={
                'name': row.get('name', 'Unknown'),
                'hostel_type': row.get('type', 'COED').upper(), 
                'total_rooms': int(row.get('total_rooms', 0)),
                'total_capacity': int(row.get('total_capacity', 0)),
                'hostel_fee': float(row.get('fee', 0.0)),
                'address': row.get('address', ''),
                'contact_number': row.get('contact', ''),
                'email': row.get('email', '')
            }
        )

# ==================== ROOM ====================

class RoomListView(BaseListView):
    model = Room
    template_name = 'hostel/room_list.html'
    context_object_name = 'rooms'
    permission_required = 'hostel.view_room'
    search_fields = ['room_number', 'hostel__name']
    filterset_fields = ['room_type', 'is_available', 'under_maintenance', 'hostel']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_url'] = reverse_lazy('hostel:room_import')
        return context

class RoomCreateView(BaseCreateView):
    model = Room
    form_class = RoomForm
    template_name = 'hostel/room_form.html'
    permission_required = 'hostel.add_room'
    success_url = reverse_lazy('hostel:room_list')

class RoomUpdateView(BaseUpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'hostel/room_form.html'
    permission_required = 'hostel.change_room'
    success_url = reverse_lazy('hostel:room_list')

class RoomDeleteView(BaseDeleteView):
    model = Room
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_room'
    success_url = reverse_lazy('hostel:room_list')

class RoomImportView(BaseImportView):
    permission_required = 'hostel.add_room'
    success_url = reverse_lazy('hostel:room_list')
    
    def process_row(self, row, tenant):
        hostel_code = row.get('hostel_code')
        room_number = row.get('room_number')
        
        if not hostel_code or not room_number:
            raise Exception("Hostel code and Room number are required")
            
        try:
            hostel = Hostel.objects.get(tenant=tenant, code=hostel_code)
        except Hostel.DoesNotExist:
            raise Exception(f"Hostel with code {hostel_code} not found")
            
        Room.objects.update_or_create(
            tenant=tenant,
            hostel=hostel,
            room_number=room_number,
            defaults={
                'room_type': row.get('type', 'DORMITORY').upper(),
                'floor': int(row.get('floor', 0)),
                'total_beds': int(row.get('beds', 1))
            }
        )

# ==================== HOSTEL ALLOCATION ====================

class HostelAllocationListView(BaseListView):
    model = HostelAllocation
    template_name = 'hostel/allocation_list.html'
    context_object_name = 'allocations'
    permission_required = 'hostel.view_hostelallocation'
    search_fields = ['student__first_name', 'student__last_name', 'hostel__name', 'room__room_number']
    filterset_fields = ['is_active', 'hostel']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_url'] = reverse_lazy('hostel:allocation_import')
        return context

class HostelAllocationCreateView(BaseCreateView):
    model = HostelAllocation
    form_class = HostelAllocationForm
    template_name = 'hostel/allocation_form.html'
    permission_required = 'hostel.add_hostelallocation'
    success_url = reverse_lazy('hostel:allocation_list')

class HostelAllocationUpdateView(BaseUpdateView):
    model = HostelAllocation
    form_class = HostelAllocationForm
    template_name = 'hostel/allocation_form.html'
    permission_required = 'hostel.change_hostelallocation'
    success_url = reverse_lazy('hostel:allocation_list')

class HostelAllocationDeleteView(BaseDeleteView):
    model = HostelAllocation
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_hostelallocation'
    success_url = reverse_lazy('hostel:allocation_list')

class HostelAllocationImportView(BaseImportView):
    permission_required = 'hostel.add_hostelallocation'
    success_url = reverse_lazy('hostel:allocation_list')
    
    def process_row(self, row, tenant):
        student_id = row.get('admission_number')
        hostel_code = row.get('hostel_code')
        room_number = row.get('room_number')
        bed = row.get('bed')
        
        if not all([student_id, hostel_code, room_number, bed]):
            raise Exception("Admission No, Hostel Code, Room No, and Bed are required")

        try:
            student = Student.objects.get(tenant=tenant, admission_number=student_id)
        except Student.DoesNotExist:
             raise Exception(f"Student with ID {student_id} not found")
        
        try:
            hostel = Hostel.objects.get(tenant=tenant, code=hostel_code)
            room = Room.objects.get(tenant=tenant, hostel=hostel, room_number=room_number)
        except (Hostel.DoesNotExist, Room.DoesNotExist):
            raise Exception("Hostel or Room not found")

        HostelAllocation.objects.update_or_create(
             tenant=tenant,
             student=student,
             defaults={
                 'hostel': hostel,
                 'room': room,
                 'bed_number': bed,
                 'monthly_fee': float(row.get('fee', hostel.hostel_fee)),
                 'is_active': True
             }
         )

# ==================== LEAVE APPLICATION ====================

class LeaveApplicationListView(BaseListView):
    model = LeaveApplication
    template_name = 'hostel/leave_list.html'
    context_object_name = 'leaves'
    permission_required = 'hostel.view_leaveapplication'
    search_fields = ['student__first_name', 'student__last_name', 'purpose']
    filterset_fields = ['status', 'leave_type']

class LeaveApplicationCreateView(BaseCreateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = 'hostel/leave_form.html'
    permission_required = 'hostel.add_leaveapplication'
    success_url = reverse_lazy('hostel:leave_list')

class LeaveApplicationUpdateView(BaseUpdateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = 'hostel/leave_form.html'
    permission_required = 'hostel.change_leaveapplication'
    success_url = reverse_lazy('hostel:leave_list')

class LeaveApplicationDeleteView(BaseDeleteView):
    model = LeaveApplication
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_leaveapplication'
    success_url = reverse_lazy('hostel:leave_list')

# ==================== AMENITIES & FACILITIES ====================

class AmenityListView(BaseListView):
    model = Amenity
    template_name = 'hostel/amenity_list.html'
    context_object_name = 'amenities'
    permission_required = 'hostel.view_amenity'
    search_fields = ['name']

class AmenityCreateView(BaseCreateView):
    model = Amenity
    form_class = AmenityForm
    template_name = 'hostel/amenity_form.html'
    permission_required = 'hostel.add_amenity'
    success_url = reverse_lazy('hostel:amenity_list')

class AmenityUpdateView(BaseUpdateView):
    model = Amenity
    form_class = AmenityForm
    template_name = 'hostel/amenity_form.html'
    permission_required = 'hostel.change_amenity'
    success_url = reverse_lazy('hostel:amenity_list')

class AmenityDeleteView(BaseDeleteView):
    model = Amenity
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_amenity'
    success_url = reverse_lazy('hostel:amenity_list')

class FacilityListView(BaseListView):
    model = Facility
    template_name = 'hostel/facility_list.html'
    context_object_name = 'facilities'
    permission_required = 'hostel.view_facility'
    search_fields = ['name']
    filterset_fields = ['category']

class FacilityCreateView(BaseCreateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'hostel/facility_form.html'
    permission_required = 'hostel.add_facility'
    success_url = reverse_lazy('hostel:facility_list')

class FacilityUpdateView(BaseUpdateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'hostel/facility_form.html'
    permission_required = 'hostel.change_facility'
    success_url = reverse_lazy('hostel:facility_list')

class FacilityDeleteView(BaseDeleteView):
    model = Facility
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_facility'
    success_url = reverse_lazy('hostel:facility_list')


# ==================== MESS MANAGEMENT (NEW) ====================

class MessDashboardView(BaseTemplateView):
    template_name = 'hostel/mess/dashboard.html'
    permission_required = 'hostel.view_messmenu'

class MessMenuCategoryListView(BaseListView):
    model = MessMenuCategory
    template_name = 'hostel/mess/category_list.html'
    context_object_name = 'categories'
    permission_required = 'hostel.view_messmenucategory'

class MessMenuCategoryCreateView(BaseCreateView):
    model = MessMenuCategory
    form_class = MessMenuCategoryForm
    template_name = 'hostel/mess/category_form.html'
    permission_required = 'hostel.add_messmenucategory'
    success_url = reverse_lazy('hostel:mess_category_list')

class MessMenuCategoryUpdateView(BaseUpdateView):
    model = MessMenuCategory
    form_class = MessMenuCategoryForm
    template_name = 'hostel/mess/category_form.html'
    permission_required = 'hostel.change_messmenucategory'
    success_url = reverse_lazy('hostel:mess_category_list')

class MessMenuCategoryDeleteView(BaseDeleteView):
    model = MessMenuCategory
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_messmenucategory'
    success_url = reverse_lazy('hostel:mess_category_list')

class MessMenuItemListView(BaseListView):
    model = MessMenuItem
    template_name = 'hostel/mess/item_list.html'
    context_object_name = 'items'
    permission_required = 'hostel.view_messmenuitem'
    search_fields = ['name', 'food_type']
    filterset_fields = ['category', 'food_type', 'is_available']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_url'] = reverse_lazy('hostel:mess_item_import')
        return context

class MessMenuItemCreateView(BaseCreateView):
    model = MessMenuItem
    form_class = MessMenuItemForm
    template_name = 'hostel/mess/item_form.html'
    permission_required = 'hostel.add_messmenuitem'
    success_url = reverse_lazy('hostel:mess_item_list')

class MessMenuItemUpdateView(BaseUpdateView):
    model = MessMenuItem
    form_class = MessMenuItemForm
    template_name = 'hostel/mess/item_form.html'
    permission_required = 'hostel.change_messmenuitem'
    success_url = reverse_lazy('hostel:mess_item_list')

class MessMenuItemDeleteView(BaseDeleteView):
    model = MessMenuItem
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_messmenuitem'
    success_url = reverse_lazy('hostel:mess_item_list')

class MessMenuItemImportView(BaseImportView):
    permission_required = 'hostel.add_messmenuitem'
    success_url = reverse_lazy('hostel:mess_item_list')
    
    def process_row(self, row, tenant):
        # name, category_name, food_type, price
        name = row.get('name')
        if not name:
             raise Exception("Name required")
        
        category_name = row.get('category')
        category = None
        if category_name:
            category, _ = MessMenuCategory.objects.get_or_create(tenant=tenant, name=category_name)
            
        MessMenuItem.objects.update_or_create(
             tenant=tenant,
             name=name,
             defaults={
                 'category': category,
                 'food_type': row.get('food_type', 'veg'),
                 'standard_price': float(row.get('price', 0))
             }
        )

class DailyMessMenuListView(BaseListView):
    model = DailyMessMenu
    template_name = 'hostel/mess/daily_list.html'
    context_object_name = 'menus'
    permission_required = 'hostel.view_dailymessmenu'
    search_fields = ['special_note']
    filterset_fields = ['date', 'day', 'meal']

class DailyMessMenuCreateView(BaseCreateView):
    model = DailyMessMenu
    form_class = DailyMessMenuForm
    template_name = 'hostel/mess/daily_form.html'
    permission_required = 'hostel.add_dailymessmenu'
    success_url = reverse_lazy('hostel:mess_daily_list')

class DailyMessMenuUpdateView(BaseUpdateView):
    model = DailyMessMenu
    form_class = DailyMessMenuForm
    template_name = 'hostel/mess/daily_form.html'
    permission_required = 'hostel.change_dailymessmenu'
    success_url = reverse_lazy('hostel:mess_daily_list')

class DailyMessMenuDeleteView(BaseDeleteView):
    model = DailyMessMenu
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_dailymessmenu'
    success_url = reverse_lazy('hostel:mess_daily_list')

class HostelMessSubscriptionListView(BaseListView):
    model = HostelMessSubscription
    template_name = 'hostel/mess/subscription_list.html'
    context_object_name = 'subscriptions'
    permission_required = 'hostel.view_hostelmesssubscription'
    search_fields = ['student__first_name', 'student__last_name']
    filterset_fields = ['plan_type', 'is_active']

class HostelMessSubscriptionCreateView(BaseCreateView):
    model = HostelMessSubscription
    form_class = HostelMessSubscriptionForm
    template_name = 'hostel/mess/subscription_form.html'
    permission_required = 'hostel.add_hostelmesssubscription'
    success_url = reverse_lazy('hostel:mess_subscription_list')

class HostelMessSubscriptionUpdateView(BaseUpdateView):
    model = HostelMessSubscription
    form_class = HostelMessSubscriptionForm
    template_name = 'hostel/mess/subscription_form.html'
    permission_required = 'hostel.change_hostelmesssubscription'
    success_url = reverse_lazy('hostel:mess_subscription_list')

class HostelMessSubscriptionDeleteView(BaseDeleteView):
    model = HostelMessSubscription
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_hostelmesssubscription'
    success_url = reverse_lazy('hostel:mess_subscription_list')

# ==================== HOSTEL ATTENDANCE ====================

class HostelAttendanceListView(BaseListView):
    model = HostelAttendance
    template_name = 'hostel/attendance_list.html'
    context_object_name = 'attendances'
    permission_required = 'hostel.view_hostelattendance'
    search_fields = ['student__first_name', 'student__last_name', 'remarks']
    filterset_fields = ['date', 'status']

class HostelAttendanceCreateView(BaseCreateView):
    model = HostelAttendance
    form_class = HostelAttendanceForm
    template_name = 'hostel/attendance_form.html'
    permission_required = 'hostel.add_hostelattendance'
    success_url = reverse_lazy('hostel:attendance_list')
    
    def form_valid(self, form):
        form.instance.marked_by = self.request.user
        return super().form_valid(form)

class HostelAttendanceUpdateView(BaseUpdateView):
    model = HostelAttendance
    form_class = HostelAttendanceForm
    template_name = 'hostel/attendance_form.html'
    permission_required = 'hostel.change_hostelattendance'
    success_url = reverse_lazy('hostel:attendance_list')

class HostelAttendanceDeleteView(BaseDeleteView):
    model = HostelAttendance
    template_name = 'hostel/confirm_delete.html'
    permission_required = 'hostel.delete_hostelattendance'
    success_url = reverse_lazy('hostel:attendance_list')
