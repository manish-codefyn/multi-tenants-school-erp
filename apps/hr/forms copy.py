# forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Department, Designation, Staff, StaffAddress, StaffDocument,
    StaffAttendance, LeaveType, LeaveApplication, LeaveBalance,
    SalaryStructure, Payroll, Promotion, EmploymentHistory,
    TrainingProgram, TrainingParticipation, PerformanceReview,
    Recruitment, JobApplication
)
from apps.core.forms import BaseForm

class DepartmentForm(BaseForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_of_department', 'email', 'phone', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class DesignationForm(BaseForm):
    class Meta:
        model = Designation
        fields = [
             'title', 'code', 'category', 'description', 'grade',
            'min_salary', 'max_salary', 'qualifications',
            'experience_required', 'reports_to'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
        }

class StaffForm(BaseForm):
    class Meta:
        model = Staff
        fields = [
             'user', 'date_of_birth', 'gender', 'blood_group',
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
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'confirmation_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
            'retirement_date': forms.DateInput(attrs={'type': 'date'}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
        }

class StaffAddressForm(BaseForm):
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

class StaffDocumentForm(BaseForm):
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

class AttendanceForm(BaseForm):
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

class LeaveTypeForm(BaseForm):
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

class LeaveApplicationForm(BaseForm):
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

class LeaveBalanceForm(BaseForm):
    class Meta:
        model = LeaveBalance
        fields = [
             'staff', 'leave_type', 'year', 'total_entitled',
            'used_days', 'carried_forward', 'adjusted_days'
        ]

class SalaryStructureForm(BaseForm):
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

class PayrollForm(BaseForm):
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

class PromotionForm(BaseForm):
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

class EmploymentHistoryForm(BaseForm):
    class Meta:
        model = EmploymentHistory
        fields = [
             'staff', 'action', 'effective_date', 'details', 'description'
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class TrainingProgramForm(BaseForm):
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

class TrainingParticipationForm(BaseForm):
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

class PerformanceReviewForm(BaseForm):
    class Meta:
        model = PerformanceReview
        fields = [
             'staff', 'review_type', 'review_period_start', 'review_period_end',
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

class RecruitmentForm(BaseForm):
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

class JobApplicationForm(BaseForm):
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