# forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Department, Designation, Staff, StaffAddress, StaffDocument,
    StaffAttendance, LeaveType, LeaveApplication, LeaveBalance,
    SalaryStructure, Payroll, Promotion, EmploymentHistory,
    TrainingProgram, TrainingParticipation, PerformanceReview,
    Recruitment, JobApplication, Qualification, Holiday, WorkSchedule
)
from apps.core.forms import BaseForm, TenantAwareModelForm
from apps.core.utils.form_helpers import DateInput, PhoneInput, SelectWithSearch, SelectMultipleWithSearch


class QualificationForm(TenantAwareModelForm):
    class Meta:
        model = Qualification
        fields = ['degree', 'specialization', 'institution', 'year']
        widgets = {
            'year': DateInput(),
        }

class HolidayForm(TenantAwareModelForm):
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'is_recurring', 'description']
        widgets = {
            'date': DateInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class WorkScheduleForm(TenantAwareModelForm):
    working_days = forms.MultipleChoiceField(
        choices=[
            (0, _("Monday")),
            (1, _("Tuesday")),
            (2, _("Wednesday")),
            (3, _("Thursday")),
            (4, _("Friday")),
            (5, _("Saturday")),
            (6, _("Sunday")),
        ],
        widget=forms.CheckboxSelectMultiple,
        label=_("Working Days")
    )

    class Meta:
        model = WorkSchedule
        fields = ['name', 'start_time', 'end_time', 'working_days', 'is_default']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_working_days(self):
        data = self.cleaned_data['working_days']
        return [int(day) for day in data]


class DepartmentForm(TenantAwareModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_of_department', 'email', 'phone', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class DesignationForm(TenantAwareModelForm):
    class Meta:
        model = Designation
        exclude = [
           'code'
        ]
        fields = [
            'title','category', 'description', 'grade',
            'min_salary', 'max_salary', 'qualifications',
            'experience_required', 'reports_to' ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
         
        }

class StaffForm(TenantAwareModelForm):
    first_name = forms.CharField(max_length=150, required=True, label=_("First Name"))
    last_name = forms.CharField(max_length=150, required=True, label=_("Last Name"))

    class Meta:
        model = Staff
        fields = [
            'first_name', 'last_name',
            'date_of_birth', 'gender', 'blood_group',
            'marital_status', 'nationality', 'personal_email', 'personal_phone',
            'emergency_contact_name', 'emergency_contact_relation', 'emergency_contact_phone',
            'department', 'designation', 'employment_type', 'employment_status',
            'joining_date', 'confirmation_date', 'contract_end_date', 'retirement_date',
            'qualifications', 'specialization', 'teaching_experience', 'total_experience',
            'basic_salary', 'bank_account_number', 'bank_name', 'ifsc_code',
            'pan_number', 'aadhaar_number', 'pf_number', 'esi_number',
            'work_location', 'work_phone', 'work_email'
        ]
        widgets = {
            'date_of_birth': DateInput(),
            'joining_date': DateInput(),
            'confirmation_date': DateInput(),
            'contract_end_date': DateInput(),
            'retirement_date': DateInput(),
            'qualifications': SelectMultipleWithSearch(),
            'department': SelectWithSearch(),
            'designation': SelectWithSearch(),
            'personal_phone': PhoneInput(),
            'emergency_contact_phone': PhoneInput(),
            'work_phone': PhoneInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teaching_experience'].required = False
        self.fields['total_experience'].required = False
        self.fields['basic_salary'].required = False

    def clean_teaching_experience(self):
        data = self.cleaned_data.get('teaching_experience')
        return data if data is not None else 0

    def clean_total_experience(self):
        data = self.cleaned_data.get('total_experience')
        return data if data is not None else 0

    def clean_basic_salary(self):
        data = self.cleaned_data.get('basic_salary')
        return data if data is not None else 0.00

    def save(self, commit=True):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # If instance doesn't have a user yet, create one
        if not self.instance.user_id:
            email = self.cleaned_data['personal_email']
            first_name = self.cleaned_data['first_name']
            last_name = self.cleaned_data['last_name']
            
            # Check if user exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'staff', # Default role
                    'is_active': True,
                    'tenant': self.tenant # TenantAwareModelForm sets this
                }
            )
            if created:
                user.set_password('Staff@123') # Initial password
                user.save()
            
            self.instance.user = user
        
        return super().save(commit=commit)

class StaffAddressForm(TenantAwareModelForm):
    class Meta:
        model = StaffAddress
        fields = [
           'staff', 'address_type', 'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'country', 'is_current'
        ]
        widgets = {
            'address_line1': forms.Textarea(attrs={'rows': 2}),
            'address_line2': forms.Textarea(attrs={'rows': 2}),
        }

class StaffDocumentForm(TenantAwareModelForm):
    class Meta:
        model = StaffDocument
        fields = [
           'staff', 'document_type', 'file', 'file_name',
            'description', 'issue_date', 'expiry_date', 'is_verified'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class AttendanceForm(TenantAwareModelForm):
    class Meta:
        model = StaffAttendance
        fields = [
            'staff', 'date', 'status', 'check_in', 'check_out',
            'late_minutes', 'overtime_hours', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

class LeaveTypeForm(TenantAwareModelForm):
    class Meta:
        model = LeaveType
        fields = [
            'name', 'code', 'description', 'max_days_per_year',
            'can_carry_forward', 'max_carry_forward_days',
            'requires_approval', 'approval_authority',
            'eligibility_after_months', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class LeaveApplicationForm(TenantAwareModelForm):
    class Meta:
        model = LeaveApplication
        fields = [
           'staff', 'leave_type', 'start_date', 'end_date',
            'reason', 'contact_address', 'contact_number',
            'work_handover_to', 'handover_notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'contact_address': forms.Textarea(attrs={'rows': 2}),
            'handover_notes': forms.Textarea(attrs={'rows': 2}),
        }

class LeaveBalanceForm(TenantAwareModelForm):
    class Meta:
        model = LeaveBalance
        fields = [
             'staff', 'leave_type', 'year', 'total_entitled',
            'used_days', 'carried_forward', 'adjusted_days'
        ]

class SalaryStructureForm(TenantAwareModelForm):
    class Meta:
        model = SalaryStructure
        fields = [
             'staff', 'effective_from', 'effective_to',
            'components', 'is_active'
        ]
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
            'components': forms.Textarea(attrs={'rows': 5}),
        }

class PayrollForm(TenantAwareModelForm):
    class Meta:
        model = Payroll
        fields = [
             'staff', 'salary_month', 'pay_date', 'basic_salary',
            'allowances', 'deductions', 'working_days',
            'present_days', 'leave_days', 'absent_days',
            'status', 'payment_method', 'transaction_reference'
        ]
        widgets = {
            'salary_month': forms.DateInput(attrs={'type': 'date'}),
            'pay_date': forms.DateInput(attrs={'type': 'date'}),
            'allowances': forms.Textarea(attrs={'rows': 3}),
            'deductions': forms.Textarea(attrs={'rows': 3}),
        }

class PromotionForm(TenantAwareModelForm):
    class Meta:
        model = Promotion
        fields = [
             'staff', 'previous_designation', 'new_designation',
            'effective_date', 'reason', 'salary_before',
            'salary_after', 'remarks'
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

class EmploymentHistoryForm(TenantAwareModelForm):
    class Meta:
        model = EmploymentHistory
        fields = [
             'staff', 'action', 'effective_date', 'description'
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class TrainingProgramForm(TenantAwareModelForm):
    class Meta:
        model = TrainingProgram
        fields = [
             'title', 'training_type', 'description', 'organizer',
            'venue', 'start_date', 'end_date', 'duration_hours',
            'cost_per_participant', 'max_participants',
            'is_mandatory', 'status'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TrainingParticipationForm(TenantAwareModelForm):
    class Meta:
        model = TrainingParticipation
        fields = [
             'training', 'staff', 'status', 'attendance_percentage',
            'grade', 'certificate_issued', 'certificate_issue_date',
            'feedback', 'skills_acquired'
        ]
        widgets = {
            'certificate_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'feedback': forms.Textarea(attrs={'rows': 2}),
            'skills_acquired': forms.Textarea(attrs={'rows': 2}),
        }

class PerformanceReviewForm(TenantAwareModelForm):
    class Meta:
        model = PerformanceReview
        fields = [
             'staff', 'review_type', 'status', 'review_period_start', 'review_period_end',
            'review_date', 'job_knowledge_rating', 'work_quality_rating',
            'productivity_rating', 'teamwork_rating', 'communication_rating',
            'attendance_rating', 'strengths', 'areas_for_improvement',
            'goals_next_period', 'reviewed_by'
        ]
        widgets = {
            'review_period_start': forms.DateInput(attrs={'type': 'date'}),
            'review_period_end': forms.DateInput(attrs={'type': 'date'}),
            'review_date': forms.DateInput(attrs={'type': 'date'}),
            'strengths': forms.Textarea(attrs={'rows': 3}),
            'areas_for_improvement': forms.Textarea(attrs={'rows': 3}),
            'goals_next_period': forms.Textarea(attrs={'rows': 3}),
        }

class RecruitmentForm(TenantAwareModelForm):
    class Meta:
        model = Recruitment
        fields = [
             'position_title', 'department', 'designation', 'employment_type',
            'no_of_openings', 'job_description', 'requirements',
            'required_qualifications', 'required_experience',
            'salary_range_min', 'salary_range_max',
            'posting_date', 'closing_date', 'expected_joining_date',
            'status', 'hiring_manager'
        ]
        widgets = {
            'posting_date': forms.DateInput(attrs={'type': 'date'}),
            'closing_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_joining_date': forms.DateInput(attrs={'type': 'date'}),
            'job_description': forms.Textarea(attrs={'rows': 3}),
            'requirements': forms.Textarea(attrs={'rows': 3}),
            'required_qualifications': forms.Textarea(attrs={'rows': 3}),
        }

class JobApplicationForm(TenantAwareModelForm):
    class Meta:
        model = JobApplication
        fields = [
             'recruitment', 'applicant_name', 'email', 'phone',
            'cover_letter', 'resume', 'expected_salary',
            'notice_period', 'status', 'rating', 'notes'
        ]
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),

        }

class PublicJobApplicationForm(TenantAwareModelForm):
    class Meta:
        model = JobApplication
        fields = [
             'recruitment', 'applicant_name', 'email', 'phone',
            'cover_letter', 'resume', 'expected_salary',
            'notice_period'
        ]
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
        }

class StaffImportForm(forms.Form):
    file = forms.FileField(
        label=_("Import File"),
        help_text=_("Upload CSV or Excel file containing staff records.")
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        ext = file.name.split('.')[-1].lower()
        if ext not in ['csv', 'xls', 'xlsx']:
            raise forms.ValidationError(_("Unsupported file format. Please upload CSV or Excel."))
        return file