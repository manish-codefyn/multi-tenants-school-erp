import uuid
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

# Phone regex for validation
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
)


class Department(BaseModel):
    """
    School Departments for staff organization
    """
    name = models.CharField(max_length=200, verbose_name=_("Department Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Department Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Department Head
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments",
        limit_choices_to={'role__in': ['teacher', 'staff', 'admin']},
        verbose_name=_("Head of Department")
    )
    
    # Contact Information
    email = models.EmailField(blank=True, verbose_name=_("Department Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Department Phone"))
    
    # Location
    location = models.CharField(max_length=200, blank=True, verbose_name=_("Location"))
    
    class Meta:
        db_table = "hr_departments"
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def staff_count(self):
        return self.staff_members.filter(is_active=True).count()

    @property
    def teacher_count(self):
        return self.staff_members.filter(
            is_active=True, 
            user__role='teacher'
        ).count()


class Designation(BaseModel):
    """
    Staff designations and positions
    """
    CATEGORY_CHOICES = (
        ("TEACHING", _("Teaching Staff")),
        ("NON_TEACHING", _("Non-Teaching Staff")),
        ("ADMINISTRATIVE", _("Administrative Staff")),
        ("SUPPORT", _("Support Staff")),
    )

    title = models.CharField(max_length=200, verbose_name=_("Designation Title"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Designation Code"))
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Staff Category")
    )
    description = models.TextField(blank=True, verbose_name=_("Job Description"))
    
    # Salary Information
    grade = models.CharField(max_length=20, blank=True, verbose_name=_("Grade Level"))
    min_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Minimum Salary")
    )
    max_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Maximum Salary")
    )
    
    # Requirements
    qualifications = models.TextField(blank=True, verbose_name=_("Required Qualifications"))
    experience_required = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Experience Required (years)")
    )
    
    # Reporting
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name=_("Reports To")
    )
    
    class Meta:
        db_table = "hr_designations"
        verbose_name = _("Designation")
        verbose_name_plural = _("Designations")
        ordering = ["category", "title"]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    @property
    def current_holders_count(self):
        return self.staff_members.filter(is_active=True).count()


class Staff(BaseModel):
    """
    School Staff Management (Teachers and Non-teaching staff)
    """
    EMPLOYMENT_TYPE_CHOICES = (
        ("PERMANENT", _("Permanent")),
        ("PROBATION", _("Probation")),
        ("CONTRACT", _("Contract")),
        ("TEMPORARY", _("Temporary")),
        ("PART_TIME", _("Part-time")),
        ("VISITING", _("Visiting Faculty")),
    )

    EMPLOYMENT_STATUS_CHOICES = (
        ("ACTIVE", _("Active")),
        ("INACTIVE", _("Inactive")),
        ("SUSPENDED", _("Suspended")),
        ("TERMINATED", _("Terminated")),
        ("RETIRED", _("Retired")),
        ("RESIGNED", _("Resigned")),
    )

    GENDER_CHOICES = (
        ("M", _("Male")),
        ("F", _("Female")),
        ("O", _("Other")),
    )

    MARITAL_STATUS_CHOICES = (
        ("SINGLE", _("Single")),
        ("MARRIED", _("Married")),
        ("DIVORCED", _("Divorced")),
        ("WIDOWED", _("Widowed")),
    )

    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    )

    # Core Information
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        verbose_name=_("System User")
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Employee ID")
    )
    
    # Personal Information
    date_of_birth = models.DateField(verbose_name=_("Date of Birth"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Gender"))
    blood_group = models.CharField(
        max_length=3,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        verbose_name=_("Blood Group")
    )
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        verbose_name=_("Marital Status")
    )
    nationality = models.CharField(max_length=50, default="Indian", verbose_name=_("Nationality"))
    
    # Contact Information
    personal_email = models.EmailField(verbose_name=_("Personal Email"))
    personal_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        verbose_name=_("Personal Phone")
    )
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name=_("Emergency Contact Name")
    )
    emergency_contact_relation = models.CharField(
        max_length=50,
        verbose_name=_("Emergency Contact Relation")
    )
    emergency_contact_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        verbose_name=_("Emergency Contact Phone")
    )
    
    # Employment Information
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="staff_members",
        verbose_name=_("Department")
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        related_name="staff_members",
        verbose_name=_("Designation")
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name=_("Employment Type")
    )
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default="ACTIVE",
        verbose_name=_("Employment Status")
    )
    
    # Employment Dates
    joining_date = models.DateField(verbose_name=_("Joining Date"))
    confirmation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Confirmation Date")
    )
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Contract End Date")
    )
    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Retirement Date")
    )
    
    # Academic Information (for teaching staff)
    qualifications = models.JSONField(
        default=list,
        verbose_name=_("Educational Qualifications"),
        help_text=_("List of qualifications with details")
    )
    specialization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Specialization")
    )
    teaching_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Teaching Experience (years)")
    )
    total_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Experience (years)")
    )
    
    # Salary Information
    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Basic Salary")
    )
    bank_account_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Bank Account Number")
    )
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Name")
    )
    ifsc_code = models.CharField(
        max_length=11,
        blank=True,
        verbose_name=_("IFSC Code")
    )
    
    # Additional Information
    pan_number = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("PAN Number")
    )
    aadhaar_number = models.CharField(
        max_length=12,
        blank=True,
        verbose_name=_("Aadhaar Number")
    )
    pf_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("PF Number")
    )
    esi_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("ESI Number")
    )
    
    # Work Information
    work_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Work Location")
    )
    work_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Work Phone")
    )
    work_email = models.EmailField(blank=True, verbose_name=_("Work Email"))


    class Meta:
        db_table = "hr_staff"
        verbose_name = _("Staff")
        verbose_name_plural = _("Staff")
        ordering = ["employee_id"]
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['department', 'designation']),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
        
    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Method 1: Year-based with department
            current_year = timezone.now().strftime('%Y')
            dept_code = self.department.name[:3].upper() if self.department else 'GEN'
            
            pattern = f"EMP{current_year}{dept_code}(\\d{{3}})"
            existing_ids = Staff.objects.filter(
                employee_id__regex=f"^EMP{current_year}{dept_code}\\d{{3}}$"
            ).values_list('employee_id', flat=True)
            
            if existing_ids:
                numbers = []
                for id_str in existing_ids:
                    match = re.match(pattern, id_str)
                    if match:
                        numbers.append(int(match.group(1)))
                next_number = max(numbers) + 1 if numbers else 1
            else:
                next_number = 1
            
            self.employee_id = f"EMP{current_year}{dept_code}{next_number:03d}"
        
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.user.get_full_name()

    def get_full_name(self):
        return self.full_name

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def service_years(self):
        today = timezone.now().date()
        return today.year - self.joining_date.year - (
            (today.month, today.day) < (self.joining_date.month, self.joining_date.day)
        )

    @property
    def is_teaching_staff(self):
        return self.user.role == 'teacher'

    @property
    def is_active_employee(self):
        return self.employment_status == "ACTIVE"

    def promote(self, new_designation, effective_date):
        """Promote staff to new designation"""
        # Create promotion record
        Promotion.objects.create(
            staff=self,
            previous_designation=self.designation,
            new_designation=new_designation,
            effective_date=effective_date,
            reason="Promotion"
        )
        
        # Update current designation
        self.designation = new_designation
        self.save()

    def terminate_employment(self, termination_date, reason):
        """Terminate staff employment"""
        self.employment_status = "TERMINATED"
        self.save()
        
        # Create termination record
        EmploymentHistory.objects.create(
            staff=self,
            action="TERMINATION",
            effective_date=termination_date,
            details={"reason": reason}
        )


class StaffAddress(BaseModel):
    """
    Staff address information
    """
    ADDRESS_TYPE_CHOICES = (
        ("PERMANENT", _("Permanent Address")),
        ("CORRESPONDENCE", _("Correspondence Address")),
        ("LOCAL", _("Local Address")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Staff")
    )
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        verbose_name=_("Address Type")
    )
    address_line1 = models.CharField(max_length=255, verbose_name=_("Address Line 1"))
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_("Address Line 2"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state = models.CharField(max_length=100, verbose_name=_("State"))
    pincode = models.CharField(max_length=10, verbose_name=_("Pincode"))
    country = models.CharField(max_length=100, default="India", verbose_name=_("Country"))
    is_current = models.BooleanField(default=True, verbose_name=_("Is Current Address"))

    class Meta:
        db_table = "hr_staff_addresses"
        verbose_name = _("Staff Address")
        verbose_name_plural = _("Staff Addresses")
        unique_together = [['staff', 'address_type']]

    def __str__(self):
        return f"{self.address_type} - {self.staff}"


class StaffDocument(BaseModel):
    """
    Staff documents and certificates
    """
    DOCUMENT_TYPE_CHOICES = (
        ("PHOTOGRAPH", _("Photograph")),
        ("RESUME", _("Resume")),
        ("EDUCATIONAL_CERTIFICATE", _("Educational Certificate")),
        ("EXPERIENCE_CERTIFICATE", _("Experience Certificate")),
        ("AADHAAR", _("Aadhaar Card")),
        ("PAN_CARD", _("PAN Card")),
        ("BANK_PASSBOOK", _("Bank Passbook")),
        ("APPOINTMENT_LETTER", _("Appointment Letter")),
        ("CONTRACT", _("Employment Contract")),
        ("SALARY_SLIP", _("Salary Slip")),
        ("OTHER", _("Other")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Staff")
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name=_("Document Type")
    )
    file = models.FileField(
        upload_to='staff_documents/',
        verbose_name=_("Document File")
    )
    file_name = models.CharField(max_length=255, blank=True, verbose_name=_("File Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    issue_date = models.DateField(null=True, blank=True, verbose_name=_("Issue Date"))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Expiry Date"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_staff_documents",
        verbose_name=_("Verified By")
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Verified At"))

    class Meta:
        db_table = "hr_staff_documents"
        verbose_name = _("Staff Document")
        verbose_name_plural = _("Staff Documents")

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.staff}"


class StaffAttendance(BaseModel):
    """
    Staff attendance tracking
    """
    ATTENDANCE_STATUS_CHOICES = (
        ("PRESENT", _("Present")),
        ("ABSENT", _("Absent")),
        ("LATE", _("Late")),
        ("HALF_DAY", _("Half Day")),
        ("HOLIDAY", _("Holiday")),
        ("LEAVE", _("On Leave")),
        ("WEEKLY_OFF", _("Weekly Off")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Staff")
    )
    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default="PRESENT",
        verbose_name=_("Status")
    )
    
    # Time Tracking
    check_in = models.TimeField(null=True, blank=True, verbose_name=_("Check In Time"))
    check_out = models.TimeField(null=True, blank=True, verbose_name=_("Check Out Time"))
    total_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Hours")
    )
    
    # Late Information
    late_minutes = models.PositiveIntegerField(default=0, verbose_name=_("Late Minutes"))
    overtime_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Overtime Hours")
    )
    
    # Remarks
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="marked_attendances",
        verbose_name=_("Marked By")
    )

    class Meta:
        db_table = "hr_attendance"
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        unique_together = [['staff', 'date']]
        ordering = ["-date", "staff"]
        indexes = [
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.staff} - {self.date} - {self.status}"

    def save(self, *args, **kwargs):
        # Calculate total hours if check_in and check_out are provided
        if self.check_in and self.check_out:
            from datetime import datetime, time
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            if check_out_dt < check_in_dt:
                # Handle overnight shifts
                check_out_dt = datetime.combine(self.date + timezone.timedelta(days=1), self.check_out)
            
            duration = check_out_dt - check_in_dt
            self.total_hours = duration.total_seconds() / 3600
            
        super().save(*args, **kwargs)

    @property
    def is_present(self):
        return self.status in ["PRESENT", "LATE", "HALF_DAY"]


class LeaveType(BaseModel):
    """
    Types of leaves available for staff
    """
    name = models.CharField(max_length=100, verbose_name=_("Leave Type Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Leave Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Leave Configuration
    max_days_per_year = models.PositiveIntegerField(verbose_name=_("Maximum Days Per Year"))
    can_carry_forward = models.BooleanField(default=False, verbose_name=_("Can Carry Forward"))
    max_carry_forward_days = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Maximum Carry Forward Days")
    )
    requires_approval = models.BooleanField(default=True, verbose_name=_("Requires Approval"))
    approval_authority = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approvable_leaves",
        verbose_name=_("Approval Authority")
    )
    
    # Eligibility
    eligibility_after_months = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Eligible After (months)")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "hr_leave_types"
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveApplication(BaseModel):
    """
    Staff leave applications
    """
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("APPROVED", _("Approved")),
        ("REJECTED", _("Rejected")),
        ("CANCELLED", _("Cancelled")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="leave_applications",
        verbose_name=_("Staff")
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Leave Type")
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    total_days = models.PositiveIntegerField(verbose_name=_("Total Days"))
    
    # Application Details
    reason = models.TextField(verbose_name=_("Reason for Leave"))
    contact_address = models.TextField(verbose_name=_("Contact Address During Leave"))
    contact_number = models.CharField(
        max_length=17,
        validators=[phone_regex],
        verbose_name=_("Contact Number During Leave")
    )
    
    # Handover
    work_handover_to = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handover_received",
        verbose_name=_("Work Handover To")
    )
    handover_notes = models.TextField(blank=True, verbose_name=_("Handover Notes"))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    applied_date = models.DateTimeField(default=timezone.now, verbose_name=_("Applied Date"))
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
        verbose_name=_("Approved By")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    approval_remarks = models.TextField(blank=True, verbose_name=_("Approval Remarks"))
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection Reason"))

    class Meta:
        db_table = "hr_leave_applications"
        verbose_name = _("Leave Application")
        verbose_name_plural = _("Leave Applications")
        ordering = ["-applied_date"]
        indexes = [
            models.Index(fields=['staff', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.staff} - {self.leave_type} - {self.start_date} to {self.end_date}"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError(_("End date must be after start date"))
        
        # Calculate total days
        self.total_days = (self.end_date - self.start_date).days + 1

    def approve(self, user, remarks=""):
        """Approve leave application"""
        self.status = "APPROVED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.approval_remarks = remarks
        self.save()

    def reject(self, user, reason):
        """Reject leave application"""
        self.status = "REJECTED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save()


class LeaveBalance(BaseModel):
    """
    Staff leave balances
    """
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="leave_balances",
        verbose_name=_("Staff")
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances",
        verbose_name=_("Leave Type")
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        verbose_name=_("Year")
    )
    total_entitled = models.PositiveIntegerField(verbose_name=_("Total Entitled Days"))
    used_days = models.PositiveIntegerField(default=0, verbose_name=_("Used Days"))
    carried_forward = models.PositiveIntegerField(default=0, verbose_name=_("Carried Forward Days"))
    adjusted_days = models.IntegerField(default=0, verbose_name=_("Adjusted Days"))

    class Meta:
        db_table = "hr_leave_balances"
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = [['staff', 'leave_type', 'year']]
        ordering = ["staff", "leave_type", "year"]

    def __str__(self):
        return f"{self.staff} - {self.leave_type} - {self.year}"

    @property
    def available_days(self):
        return self.total_entitled + self.carried_forward + self.adjusted_days - self.used_days

    @property
    def remaining_days(self):
        return max(0, self.available_days)


class SalaryStructure(BaseModel):
    """
    Staff salary structure and components
    """
    COMPONENT_TYPE_CHOICES = (
        ("EARNING", _("Earning")),
        ("DEDUCTION", _("Deduction")),
    )

    staff = models.OneToOneField(
        Staff,
        on_delete=models.CASCADE,
        related_name="salary_structure",
        verbose_name=_("Staff")
    )
    effective_from = models.DateField(verbose_name=_("Effective From"))
    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Effective To")
    )
    components = models.JSONField(
        default=dict,
        verbose_name=_("Salary Components"),
        help_text=_("JSON structure of salary components and amounts")
    )
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Earnings")
    )
    total_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Deductions")
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Net Salary")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "hr_salary_structures"
        verbose_name = _("Salary Structure")
        verbose_name_plural = _("Salary Structures")
        ordering = ["-effective_from"]

    def __str__(self):
        return f"{self.staff} - Salary Structure ({self.effective_from})"

    def save(self, *args, **kwargs):
        # Calculate totals from components
        earnings = 0
        deductions = 0
        
        for component, amount in self.components.items():
            # This is a simplified calculation - you might want more complex logic
            if amount > 0:
                earnings += amount
            else:
                deductions += abs(amount)
                
        self.total_earnings = earnings
        self.total_deductions = deductions
        self.net_salary = earnings - deductions
        
        super().save(*args, **kwargs)


class Payroll(BaseModel):
    """
    Monthly payroll processing
    """
    PAYROLL_STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("PROCESSED", _("Processed")),
        ("APPROVED", _("Approved")),
        ("PAID", _("Paid")),
        ("CANCELLED", _("Cancelled")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="payrolls",
        verbose_name=_("Staff")
    )
    salary_month = models.DateField(verbose_name=_("Salary Month"))
    pay_date = models.DateField(verbose_name=_("Pay Date"))
    
    # Salary Details
    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Basic Salary")
    )
    allowances = models.JSONField(
        default=dict,
        verbose_name=_("Allowances")
    )
    deductions = models.JSONField(
        default=dict,
        verbose_name=_("Deductions")
    )
    
    # Calculations
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Earnings")
    )
    total_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Deductions")
    )
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Net Salary")
    )
    
    # Attendance Adjustments
    working_days = models.PositiveIntegerField(verbose_name=_("Working Days"))
    present_days = models.PositiveIntegerField(verbose_name=_("Present Days"))
    leave_days = models.PositiveIntegerField(default=0, verbose_name=_("Leave Days"))
    absent_days = models.PositiveIntegerField(default=0, verbose_name=_("Absent Days"))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PAYROLL_STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    
    # Payment Information
    payment_method = models.CharField(
        max_length=50,
        choices=(
            ("BANK_TRANSFER", _("Bank Transfer")),
            ("CHEQUE", _("Cheque")),
            ("CASH", _("Cash")),
        ),
        default="BANK_TRANSFER",
        verbose_name=_("Payment Method")
    )
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Transaction Reference")
    )
    
    # Approval
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_payrolls",
        verbose_name=_("Processed By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payrolls",
        verbose_name=_("Approved By")
    )

    class Meta:
        db_table = "hr_payroll"
        verbose_name = _("Payroll")
        verbose_name_plural = _("Payroll")
        unique_together = [['staff', 'salary_month']]
        ordering = ["-salary_month"]
        indexes = [
            models.Index(fields=['staff', 'salary_month']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.staff} - {self.salary_month.strftime('%B %Y')}"

    def calculate_salary(self):
        """Calculate salary based on attendance and structure"""
        # This is a simplified calculation
        # You would implement complex salary calculation logic here
        daily_rate = self.basic_salary / self.working_days
        payable_days = self.present_days + self.leave_days  # Assuming paid leaves
        
        self.total_earnings = daily_rate * payable_days
        self.net_salary = self.total_earnings - self.total_deductions
        
        self.save()


class Promotion(BaseModel):
    """
    Staff promotion history
    """
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="promotions",
        verbose_name=_("Staff")
    )
    previous_designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        related_name="previous_promotions",
        verbose_name=_("Previous Designation")
    )
    new_designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        related_name="new_promotions",
        verbose_name=_("New Designation")
    )
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    reason = models.TextField(verbose_name=_("Promotion Reason"))
    salary_before = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Salary Before Promotion")
    )
    salary_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Salary After Promotion")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="approved_promotions",
        verbose_name=_("Approved By")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))

    class Meta:
        db_table = "hr_promotions"
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.staff} - Promotion to {self.new_designation}"


class EmploymentHistory(BaseModel):
    """
    Staff employment history and changes
    """
    ACTION_CHOICES = (
        ("JOINING", _("Joining")),
        ("TRANSFER", _("Transfer")),
        ("PROMOTION", _("Promotion")),
        ("DEMOTION", _("Demotion")),
        ("SALARY_REVISION", _("Salary Revision")),
        ("DEPARTMENT_CHANGE", _("Department Change")),
        ("TERMINATION", _("Termination")),
        ("RESIGNATION", _("Resignation")),
        ("RETIREMENT", _("Retirement")),
        ("EXTENSION", _("Contract Extension")),
        ("OTHER", _("Other")),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="employment_history",
        verbose_name=_("Staff")
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name=_("Action")
    )
    effective_date = models.DateField(verbose_name=_("Effective Date"))
    details = models.JSONField(
        default=dict,
        verbose_name=_("Action Details")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="initiated_employment_actions",
        verbose_name=_("Initiated By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_employment_actions",
        verbose_name=_("Approved By")
    )

    class Meta:
        db_table = "hr_employment_history"
        verbose_name = _("Employment History")
        verbose_name_plural = _("Employment History")
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.staff} - {self.action} - {self.effective_date}"


class TrainingProgram(BaseModel):
    """
    Staff training and development programs
    """
    TRAINING_TYPE_CHOICES = (
        ("WORKSHOP", _("Workshop")),
        ("SEMINAR", _("Seminar")),
        ("CONFERENCE", _("Conference")),
        ("ONLINE_COURSE", _("Online Course")),
        ("CERTIFICATION", _("Certification")),
        ("SKILL_DEVELOPMENT", _("Skill Development")),
        ("ORIENTATION", _("Orientation")),
        ("OTHER", _("Other")),
    )

    title = models.CharField(max_length=200, verbose_name=_("Training Title"))
    training_type = models.CharField(
        max_length=50,
        choices=TRAINING_TYPE_CHOICES,
        verbose_name=_("Training Type")
    )
    description = models.TextField(verbose_name=_("Description"))
    organizer = models.CharField(max_length=200, verbose_name=_("Organizer"))
    venue = models.CharField(max_length=200, verbose_name=_("Venue"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    duration_hours = models.PositiveIntegerField(verbose_name=_("Duration (Hours)"))
    cost_per_participant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Cost per Participant")
    )
    max_participants = models.PositiveIntegerField(verbose_name=_("Maximum Participants"))
    is_mandatory = models.BooleanField(default=False, verbose_name=_("Is Mandatory"))
    status = models.CharField(
        max_length=20,
        choices=(
            ("UPCOMING", _("Upcoming")),
            ("ONGOING", _("Ongoing")),
            ("COMPLETED", _("Completed")),
            ("CANCELLED", _("Cancelled")),
        ),
        default="UPCOMING",
        verbose_name=_("Status")
    )

    class Meta:
        db_table = "hr_training_programs"
        verbose_name = _("Training Program")
        verbose_name_plural = _("Training Programs")
        ordering = ["-start_date"]

    def __str__(self):
        return self.title

    @property
    def participant_count(self):
        return self.participants.count()

    @property
    def available_slots(self):
        return self.max_participants - self.participant_count


class TrainingParticipation(BaseModel):
    """
    Staff participation in training programs
    """
    training = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name=_("Training Program")
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="training_participations",
        verbose_name=_("Staff")
    )
    status = models.CharField(
        max_length=20,
        choices=(
            ("REGISTERED", _("Registered")),
            ("ATTENDED", _("Attended")),
            ("COMPLETED", _("Completed")),
            ("CANCELLED", _("Cancelled")),
            ("ABSENT", _("Absent")),
        ),
        default="REGISTERED",
        verbose_name=_("Status")
    )
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Attendance Percentage")
    )
    grade = models.CharField(max_length=10, blank=True, verbose_name=_("Grade"))
    certificate_issued = models.BooleanField(default=False, verbose_name=_("Certificate Issued"))
    certificate_issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Certificate Issue Date")
    )
    feedback = models.TextField(blank=True, verbose_name=_("Feedback"))
    skills_acquired = models.JSONField(
        default=list,
        verbose_name=_("Skills Acquired")
    )

    class Meta:
        db_table = "hr_training_participations"
        verbose_name = _("Training Participation")
        verbose_name_plural = _("Training Participations")
        unique_together = [['training', 'staff']]

    def __str__(self):
        return f"{self.staff} - {self.training}"


class PerformanceReview(BaseModel):
    """
    Staff performance reviews and appraisals
    """
    REVIEW_TYPE_CHOICES = (
        ("PROBATION", _("Probation Review")),
        ("ANNUAL", _("Annual Appraisal")),
        ("QUARTERLY", _("Quarterly Review")),
        ("PROMOTION", _("Promotion Review")),
        ("SPECIAL", _("Special Review")),
    )

    RATING_CHOICES = (
        (1, "1 - Unsatisfactory"),
        (2, "2 - Needs Improvement"),
        (3, "3 - Meets Expectations"),
        (4, "4 - Exceeds Expectations"),
        (5, "5 - Outstanding"),
    )

    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
        verbose_name=_("Staff")
    )
    review_type = models.CharField(
        max_length=20,
        choices=REVIEW_TYPE_CHOICES,
        verbose_name=_("Review Type")
    )
    review_period_start = models.DateField(verbose_name=_("Review Period Start"))
    review_period_end = models.DateField(verbose_name=_("Review Period End"))
    review_date = models.DateField(default=timezone.now, verbose_name=_("Review Date"))
    
    # Ratings
    job_knowledge_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Job Knowledge Rating")
    )
    work_quality_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Work Quality Rating")
    )
    productivity_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Productivity Rating")
    )
    teamwork_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Teamwork Rating")
    )
    communication_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Communication Rating")
    )
    attendance_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Attendance Rating")
    )
    
    # Overall
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name=_("Overall Rating")
    )
    strengths = models.TextField(verbose_name=_("Strengths"))
    areas_for_improvement = models.TextField(verbose_name=_("Areas for Improvement"))
    goals_next_period = models.TextField(verbose_name=_("Goals for Next Period"))
    
    # Reviewers
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conducted_reviews",
        verbose_name=_("Reviewed By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_reviews",
        verbose_name=_("Approved By")
    )
    
    # Employee Acknowledgement
    employee_comments = models.TextField(blank=True, verbose_name=_("Employee Comments"))
    employee_acknowledged = models.BooleanField(default=False, verbose_name=_("Employee Acknowledged"))
    acknowledgement_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Acknowledgement Date")
    )

    class Meta:
        db_table = "hr_performance_reviews"
        verbose_name = _("Performance Review")
        verbose_name_plural = _("Performance Reviews")
        ordering = ["-review_date"]

    def __str__(self):
        return f"{self.staff} - {self.review_type} - {self.review_period_end}"

    def save(self, *args, **kwargs):
        # Calculate overall rating
        ratings = [
            self.job_knowledge_rating,
            self.work_quality_rating,
            self.productivity_rating,
            self.teamwork_rating,
            self.communication_rating,
            self.attendance_rating
        ]
        self.overall_rating = sum(ratings) / len(ratings)
        super().save(*args, **kwargs)


class Recruitment(BaseModel):
    """
    Staff recruitment and hiring process
    """
    POSITION_STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("OPEN", _("Open")),
        ("INTERVIEWING", _("Interviewing")),
        ("OFFERED", _("Offer Made")),
        ("FILLED", _("Filled")),
        ("CANCELLED", _("Cancelled")),
        ("ON_HOLD", _("On Hold")),
    )

    position_title = models.CharField(max_length=200, verbose_name=_("Position Title"))
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="recruitments",
        verbose_name=_("Department")
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        related_name="recruitments",
        verbose_name=_("Designation")
    )
    employment_type = models.CharField(
        max_length=20,
        choices=Staff.EMPLOYMENT_TYPE_CHOICES,
        verbose_name=_("Employment Type")
    )
    
    # Position Details
    no_of_openings = models.PositiveIntegerField(verbose_name=_("Number of Openings"))
    job_description = models.TextField(verbose_name=_("Job Description"))
    requirements = models.TextField(verbose_name=_("Requirements"))
    required_qualifications = models.TextField(verbose_name=_("Required Qualifications"))
    required_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Required Experience (years)")
    )
    
    # Salary Information
    salary_range_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Minimum Salary")
    )
    salary_range_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Maximum Salary")
    )
    
    # Timeline
    posting_date = models.DateField(default=timezone.now, verbose_name=_("Posting Date"))
    closing_date = models.DateField(verbose_name=_("Closing Date"))
    expected_joining_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expected Joining Date")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=POSITION_STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    
    # Hiring Manager
    hiring_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="managed_recruitments",
        verbose_name=_("Hiring Manager")
    )

    class Meta:
        db_table = "hr_recruitments"
        verbose_name = _("Recruitment")
        verbose_name_plural = _("Recruitments")
        ordering = ["-posting_date"]

    def __str__(self):
        return f"{self.position_title} - {self.department}"

    @property
    def applications_count(self):
        return self.applications.count()

    @property
    def is_open(self):
        return (self.status == "OPEN" and 
                self.closing_date >= timezone.now().date())


class JobApplication(BaseModel):
    """
    Job applications for open positions
    """
    APPLICATION_STATUS_CHOICES = (
        ("APPLIED", _("Applied")),
        ("SCREENING", _("Screening")),
        ("INTERVIEW", _("Interview")),
        ("SHORTLISTED", _("Shortlisted")),
        ("REJECTED", _("Rejected")),
        ("OFFERED", _("Offered")),
        ("ACCEPTED", _("Accepted")),
        ("DECLINED", _("Declined")),
    )

    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Recruitment")
    )
    applicant_name = models.CharField(max_length=100, verbose_name=_("Applicant Name"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        verbose_name=_("Phone")
    )
    
    # Application Details
    cover_letter = models.TextField(blank=True, verbose_name=_("Cover Letter"))
    resume = models.FileField(
        upload_to='job_applications/resumes/',
        verbose_name=_("Resume")
    )
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Expected Salary")
    )
    notice_period = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Notice Period (days)")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default="APPLIED",
        verbose_name=_("Status")
    )
    applied_date = models.DateTimeField(default=timezone.now, verbose_name=_("Applied Date"))
    
    # Evaluation
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating")
    )
    notes = models.TextField(blank=True, verbose_name=_("Evaluation Notes"))

    class Meta:
        db_table = "hr_job_applications"
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        ordering = ["-applied_date"]

    def __str__(self):
        return f"{self.applicant_name} - {self.recruitment.position_title}"

class Holiday(BaseModel):
    """
    Public holidays and non-working days
    """
    name = models.CharField(max_length=100, verbose_name=_("Holiday Name"))
    date = models.DateField(verbose_name=_("Date"))
    is_recurring = models.BooleanField(default=True, verbose_name=_("Is Recurring"))
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        db_table = "hr_holidays"
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"


class WorkSchedule(BaseModel):
    """
    Work shifts and schedules
    """
    name = models.CharField(max_length=100, verbose_name=_("Schedule Name"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    working_days = models.JSONField(
        default=list,
        verbose_name=_("Working Days"),
        help_text=_("List of working days (0=Monday, 6=Sunday)")
    )
    is_default = models.BooleanField(default=False, verbose_name=_("Is Default"))

    class Meta:
        db_table = "hr_work_schedules"
        verbose_name = _("Work Schedule")
        verbose_name_plural = _("Work Schedules")

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class TaxConfig(BaseModel):
    """
    Tax rules and configurations
    """
    name = models.CharField(max_length=100, verbose_name=_("Tax Name"))
    tax_type = models.CharField(
        max_length=50,
        choices=(("INCOME_TAX", "Income Tax"), ("PROFESSIONAL_TAX", "Professional Tax")),
        verbose_name=_("Tax Type")
    )
    slabs = models.JSONField(
        default=list,
        verbose_name=_("Tax Slabs"),
        help_text=_("List of tax slabs and rates")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "hr_tax_configs"
        verbose_name = _("Tax Configuration")
        verbose_name_plural = _("Tax Configurations")

    def __str__(self):
        return self.name


class PFESIConfig(BaseModel):
    """
    PF and ESI configurations
    """
    pf_employee_contribution = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("PF Employee Contribution (%)")
    )
    pf_employer_contribution = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("PF Employer Contribution (%)")
    )
    esi_employee_contribution = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("ESI Employee Contribution (%)")
    )
    esi_employer_contribution = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("ESI Employer Contribution (%)")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "hr_pf_esi_configs"
        verbose_name = _("PF & ESI Configuration")
        verbose_name_plural = _("PF & ESI Configurations")

    def __str__(self):
        return "PF & ESI Configuration"
