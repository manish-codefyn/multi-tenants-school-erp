from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.forms import TenantAwareModelForm
from apps.core.utils.form_helpers import DateInput, SelectWithSearch, TimeInput, SelectMultipleWithSearch
from .models import (
    Hostel, Room, HostelAllocation, LeaveApplication, HostelAttendance,
    Amenity, Facility, MessMenuCategory, MessMenuItem, DailyMessMenu,
    DailyMenuItem, HostelMessSubscription
)

class AmenityForm(TenantAwareModelForm):
    class Meta:
        model = Amenity
        fields = ['name', 'icon']

class FacilityForm(TenantAwareModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'icon', 'category', 'description']
        widgets = {
             'description': forms.Textarea(attrs={'rows': 2}),
        }

class HostelForm(TenantAwareModelForm):
    class Meta:
        model = Hostel
        fields = ['name', 'code', 'hostel_type', 'address', 'contact_number', 'email', 
                  'total_rooms', 'total_capacity', 'warden', 'hostel_fee', 'security_deposit', 
                  'amenities', 'rules_regulations', 'is_active']
        widgets = {
            'warden': SelectWithSearch(),
            'amenities': SelectMultipleWithSearch(), 
            'rules_regulations': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class RoomForm(TenantAwareModelForm):
    class Meta:
        model = Room
        fields = ['hostel', 'room_number', 'room_type', 'floor', 'total_beds', 
                  'facilities', 'is_available', 'under_maintenance']
        widgets = {
            'hostel': SelectWithSearch(),
            'facilities': SelectMultipleWithSearch(),
        }

class HostelAllocationForm(TenantAwareModelForm):
    class Meta:
        model = HostelAllocation
        fields = ['student', 'hostel', 'room', 'bed_number', 'allocation_date', 
                  'expected_vacate_date', 'monthly_fee', 'security_deposit_paid', 'is_active']
        widgets = {
            'student': SelectWithSearch(),
            'hostel': SelectWithSearch(),
            'room': SelectWithSearch(),
            'allocation_date': DateInput(),
            'expected_vacate_date': DateInput(),
            'actual_vacate_date': DateInput(),
        }

class LeaveApplicationForm(TenantAwareModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['student', 'leave_type', 'purpose', 'from_date', 'to_date', 
                  'destination', 'contact_number', 'guardian_name', 'guardian_contact', 'status']
        widgets = {
            'student': SelectWithSearch(),
            'from_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'to_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 3}),
        }

class HostelAttendanceForm(TenantAwareModelForm):
    class Meta:
        model = HostelAttendance
        fields = ['student', 'date', 'status', 'check_in_time', 'check_out_time', 'remarks']
        widgets = {
            'student': SelectWithSearch(),
            'date': DateInput(),
            'check_in_time': TimeInput(),
            'check_out_time': TimeInput(),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

# --- Mess Forms ---

class MessMenuCategoryForm(TenantAwareModelForm):
    class Meta:
        model = MessMenuCategory
        fields = ['name', 'description', 'display_order']
        widgets = {
             'description': forms.Textarea(attrs={'rows': 2}),
        }

class MessMenuItemForm(TenantAwareModelForm):
    class Meta:
        model = MessMenuItem
        fields = ['name', 'description', 'category', 'food_type', 'standard_price', 
                  'is_available', 'preparation_time', 'display_order']
        widgets = {
            'category': SelectWithSearch(),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class DailyMessMenuForm(TenantAwareModelForm):
    class Meta:
        model = DailyMessMenu
        fields = ['day', 'meal', 'date', 'items', 'special_note', 'is_active']
        widgets = {
            'date': DateInput(),
            'items': SelectMultipleWithSearch(),
            'special_note': forms.TextInput(attrs={'placeholder': 'E.g. Festival Special'}),
        }

class HostelMessSubscriptionForm(TenantAwareModelForm):
    class Meta:
        model = HostelMessSubscription
        fields = ['student', 'plan_type', 'start_date', 'end_date', 'monthly_rate', 
                  'includes_breakfast', 'includes_lunch', 'includes_snacks', 'includes_dinner', 'is_active']
        widgets = {
            'student': SelectWithSearch(),
            'start_date': DateInput(),
            'end_date': DateInput(),
        }

class ImportFileForm(forms.Form):
    file = forms.FileField(
        label=_("Import File"),
        help_text=_("Upload CSV or Excel file. (Max size: 5MB)")
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        ext = file.name.split('.')[-1].lower()
        if ext not in ['csv', 'xls', 'xlsx']:
            raise forms.ValidationError(_("Unsupported file format. Please upload CSV or Excel."))
        return file
