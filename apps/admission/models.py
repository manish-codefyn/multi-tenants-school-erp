import uuid
import os
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model

# Import core models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

# Phone regex for validation
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
)

# ==================== ADMISSION CYCLE & PROGRAMS ====================

class AdmissionCycle(BaseModel):
    """
    Admission cycle management for different academic years - SCHOOL VERSION
    """
    CYCLE_STATUS = (
        ("DRAFT", _("Draft")),
        ("ACTIVE", _("Active")),
        ("CLOSED", _("Closed")),
        ("ARCHIVED", _("Archived")),
    )

    SCHOOL_LEVELS = (
        ("PRIMARY", _("Primary School")),
        ("MIDDLE", _("Middle School")),
        ("HIGH", _("High School")),
        ("SENIOR_SECONDARY", _("Senior Secondary")),
        ("ALL", _("All Levels")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Admission Cycle Name"))
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.CASCADE,
        related_name="admission_cycles",
        verbose_name=_("Academic Year")
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Cycle Code")
    )
    school_level = models.CharField(
        max_length=20,
        choices=SCHOOL_LEVELS,
        default="ALL",
        verbose_name=_("School Level")
    )
    
    # Dates
    start_date = models.DateTimeField(verbose_name=_("Application Start Date"))
    end_date = models.DateTimeField(verbose_name=_("Application End Date"))
    merit_list_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Merit List Declaration Date")
    )
    admission_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Admission Completion Date")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=CYCLE_STATUS,
        default="DRAFT",
        db_index=True,
        verbose_name=_("Status")
    )
    
    # Configuration
    max_applications = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Maximum Applications")
    )
    application_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Application Fee")
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Is Active"))
    
    # Instructions
    instructions = models.TextField(blank=True, verbose_name=_("Application Instructions"))
    terms_conditions = models.TextField(blank=True, verbose_name=_("Terms & Conditions"))
    
    class Meta:
        db_table = "admission_cycles"
        verbose_name = _("Admission Cycle")
        verbose_name_plural = _("Admission Cycles")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['academic_year', 'status']),
            models.Index(fields=['school_level']),
        ]

    def __str__(self):
        return f"{self.name} - {self.academic_year}"

    def clean(self):
        """Validate admission cycle dates"""
        errors = {}
        if self.end_date <= self.start_date:
            errors['end_date'] = _("End date must be after start date")
            
        if self.merit_list_date and self.merit_list_date < self.end_date:
            errors['merit_list_date'] = _("Merit list date must be after application end date")
            
        if self.admission_end_date and self.admission_end_date < self.merit_list_date:
            errors['admission_end_date'] = _("Admission end date must be after merit list date")
            
        if errors:
            raise ValidationError(errors)

    @property
    def is_open(self):
        """Check if admission cycle is currently open"""
        now = timezone.now()
        return (self.status == "ACTIVE" and 
                self.start_date <= now <= self.end_date and 
                self.is_active)

    @property
    def application_count(self):
        """Get total applications in this cycle"""
        return self.applications.count()

    @property
    def can_accept_applications(self):
        """Check if cycle can accept more applications"""
        if self.max_applications:
            return self.application_count < self.max_applications
        return True

    def get_remaining_days(self):
        """Get remaining days for application"""
        if self.is_open:
            remaining = self.end_date - timezone.now()
            return max(0, remaining.days)
        return 0


class AdmissionProgram(BaseModel):
    """
    Admission programs/classes offered for school
    """
    PROGRAM_TYPES = (
        ("NURSERY", _("Nursery")),
        ("KG", _("Kindergarten")),
        ("PRIMARY", _("Primary")),
        ("MIDDLE", _("Middle School")),
        ("HIGH", _("High School")),
        ("SENIOR_SECONDARY", _("Senior Secondary")),
        ("OTHER", _("Other")),
    )

    STREAMS = (
        ("SCIENCE", _("Science")),
        ("COMMERCE", _("Commerce")),
        ("ARTS", _("Arts")),
        ("VOCATIONAL", _("Vocational")),
        ("GENERAL", _("General")),
    )

    admission_cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name="programs",
        verbose_name=_("Admission Cycle")
    )
    program_name = models.CharField(
        max_length=200,
        verbose_name=_("Program Name")
    )
    program_type = models.CharField(
        max_length=20,
        choices=PROGRAM_TYPES,
        verbose_name=_("Program Type")
    )
    class_grade = models.CharField(
        max_length=50,
        verbose_name=_("Class/Grade"),
        help_text=_("e.g., Class 1, Grade 5, Nursery A")
    )
    stream = models.CharField(
        max_length=20,
        choices=STREAMS,
        blank=True,
        verbose_name=_("Stream"),
        help_text=_("Applicable for senior secondary classes")
    )
    
    # Seats Information
    total_seats = models.PositiveIntegerField(verbose_name=_("Total Seats"))
    general_seats = models.PositiveIntegerField(verbose_name=_("General Seats"))
    reserved_seats = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Reserved Seats"),
        help_text=_("JSON format: {'SC': 10, 'ST': 5, 'OBC': 15, 'EWS': 8}")
    )
    
    # Age Criteria
    min_age_years = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Minimum Age (Years)")
    )
    min_age_months = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Minimum Age (Months)")
    )
    max_age_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Maximum Age (Years)")
    )
    max_age_months = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Maximum Age (Months)")
    )
    
    # Eligibility Criteria
    min_qualification = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Minimum Qualification"),
        help_text=_("e.g., Previous class passed")
    )
    min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name=_("Minimum Percentage Required")
    )
    entrance_exam_required = models.BooleanField(
        default=False,
        verbose_name=_("Entrance Exam Required")
    )
    interview_required = models.BooleanField(
        default=False,
        verbose_name=_("Interview Required")
    )
    eligibility_criteria = models.TextField(blank=True, verbose_name=_("Eligibility Criteria"))
    
    # Fees
    application_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Program Application Fee")
    )
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Annual Tuition Fee")
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "admission_programs"
        verbose_name = _("Admission Program")
        verbose_name_plural = _("Admission Programs")
        unique_together = [['admission_cycle', 'class_grade', 'stream']]
        indexes = [
            models.Index(fields=['admission_cycle', 'is_active']),
            models.Index(fields=['program_type']),
            models.Index(fields=['class_grade']),
        ]

    def __str__(self):
        stream_display = f" - {self.get_stream_display()}" if self.stream else ""
        return f"{self.class_grade}{stream_display} - {self.admission_cycle}"

    @property
    def filled_seats(self):
        """Get number of filled seats"""
        return self.applications.filter(status="ADMITTED").count()

    @property
    def available_seats(self):
        """Get available seats"""
        return self.total_seats - self.filled_seats

    @property
    def application_count(self):
        """Get total applications for this program"""
        return self.applications.count()

    def check_age_eligibility(self, date_of_birth):
        """Check if candidate meets age criteria"""
        today = timezone.now().date()
        age_delta = today - date_of_birth
        age_years = age_delta.days // 365
        age_months = (age_delta.days % 365) // 30
        
        min_age_ok = (age_years > self.min_age_years or 
                     (age_years == self.min_age_years and age_months >= self.min_age_months))
        
        if self.max_age_years:
            max_age_ok = (age_years < self.max_age_years or 
                         (age_years == self.max_age_years and age_months <= self.max_age_months))
            return min_age_ok and max_age_ok
        
        return min_age_ok

    def check_eligibility(self, percentage, qualification, date_of_birth):
        """Check if candidate meets all eligibility criteria"""
        age_eligible = self.check_age_eligibility(date_of_birth)
        academic_eligible = True
        
        if self.min_percentage:
            academic_eligible = percentage >= self.min_percentage
            
        return age_eligible and academic_eligible


# ==================== ONLINE APPLICATION MODELS ====================

class OnlineApplication(BaseModel):
    """
    Main online application model for school admissions
    """
    APPLICATION_STATUS = (
        ("DRAFT", _("Draft")),
        ("SUBMITTED", _("Submitted")),
        ("UNDER_REVIEW", _("Under Review")),
        ("SHORTLISTED", _("Shortlisted")),
        ("REJECTED", _("Rejected")),
        ("WAITLISTED", _("Waitlisted")),
        ("ADMITTED", _("Admitted")),
        ("ADMISSION_CANCELLED", _("Admission Cancelled")),
    )

    GENDER_CHOICES = (
        ("M", _("Male")),
        ("F", _("Female")),
        ("O", _("Other")),
        ("U", _("Undisclosed")),
    )

    CATEGORY_CHOICES = (
        ("GENERAL", _("General")),
        ("SC", _("Scheduled Caste")),
        ("ST", _("Scheduled Tribe")),
        ("OBC", _("Other Backward Class")),
        ("EWS", _("Economically Weaker Section")),
        ("OTHER", _("Other")),
    )

    BLOOD_GROUPS = (
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
    )
    RELIGION_CHOICES = [
        ('hindu', _('Hindu')),
        ('muslim', _('Muslim')),
        ('christian', _('Christian')),
        ('sikh', _('Sikh')),
        ('buddhist', _('Buddhist')),
        ('jain', _('Jain')),
        ('other', _('Other')),
    ]


    # Application Identification
    application_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Application Number")
    )
    admission_cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Admission Cycle")
    )
    program = models.ForeignKey(
        AdmissionProgram,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Program"),
        null=True,
        blank=True
    )
    
    # Applicant Personal Information (Student)
    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    middle_name = models.CharField(max_length=50, blank=True, verbose_name=_("Middle Name"))
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    date_of_birth = models.DateField(verbose_name=_("Date of Birth"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Gender"))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True, verbose_name=_("Blood Group"))
    nationality = models.CharField(max_length=50, default="Indian", verbose_name=_("Nationality"))
    religion = models.CharField(
        max_length=20,
        choices=RELIGION_CHOICES,
        blank=True,
        verbose_name=_("Religion")
    )
    # Student Medical Information
    has_medical_conditions = models.BooleanField(default=False, verbose_name=_("Has Medical Conditions"))
    medical_conditions = models.TextField(blank=True, verbose_name=_("Medical Conditions"))
    allergies = models.TextField(blank=True, verbose_name=_("Allergies"))
    emergency_contact_name = models.CharField(max_length=100, blank=True, verbose_name=_("Emergency Contact Name"))
    emergency_contact_relation = models.CharField(max_length=50, blank=True, verbose_name=_("Emergency Contact Relation"))
    emergency_contact_phone = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Emergency Contact Phone")
    )
    
    # Contact Information
    email = models.EmailField(verbose_name=_("Email Address"), blank=True, null=True)
    phone = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        verbose_name=_("Phone Number"),
        blank=True,
        null=True
    )
    alternate_phone = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Alternate Phone")
    )
    
    # Address Information
    address_line1 = models.CharField(max_length=255, verbose_name=_("Address Line 1"), blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_("Address Line 2"))
    city = models.CharField(max_length=100, verbose_name=_("City"), blank=True, null=True)
    state = models.CharField(max_length=100, verbose_name=_("State"), blank=True, null=True)
    pincode = models.CharField(max_length=10, verbose_name=_("Pincode"), blank=True, null=True)
    country = models.CharField(max_length=100, default="India", verbose_name=_("Country"), blank=True, null=True)
    
    # Academic Information (Previous School)
    previous_school = models.CharField(max_length=200, verbose_name=_("Previous School/College"), blank=True, null=True)
    previous_qualification = models.CharField(max_length=100, verbose_name=_("Previous Class/Grade"), blank=True, null=True)
    previous_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name=_("Previous Percentage/CGPA")
    )
    previous_board = models.CharField(max_length=100, blank=True, verbose_name=_("Board/University"))
    passing_year = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Year of Passing")
    )
    # School Specific Information
    house_choice = models.CharField(max_length=50, blank=True, verbose_name=_("House Preference"))
    transport_required = models.BooleanField(default=False, verbose_name=_("School Transport Required"))
    hostel_required = models.BooleanField(default=False, verbose_name=_("Hostel Facility Required"))
    
    # Entrance Exam Information
    entrance_exam_name = models.CharField(max_length=100, blank=True, verbose_name=_("Entrance Exam"))
    entrance_exam_rank = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Entrance Rank"))
    entrance_exam_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Entrance Score")
    )
    interview_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Interview Score")
    )
    
    # Application Status & Tracking
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default="DRAFT",
        db_index=True,
        verbose_name=_("Application Status")
    )
    submission_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Submission Date"))
    review_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Review Date"))
    decision_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Decision Date"))
    
    # Payment Information
    application_fee_paid = models.BooleanField(default=False, verbose_name=_("Application Fee Paid"))
    payment_reference = models.CharField(max_length=100, blank=True, verbose_name=_("Payment Reference"))
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Payment Date"))
    
    # Additional Information
    special_requirements = models.TextField(blank=True, verbose_name=_("Special Requirements"))
    how_heard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("How did you hear about us?")
    )
    comments = models.TextField(blank=True, verbose_name=_("Additional Comments"))
    
    # System Fields
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))

    class Meta:
        db_table = "admission_online_applications"
        verbose_name = _("Online Application")
        verbose_name_plural = _("Online Applications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['application_number']),
            models.Index(fields=['email', 'admission_cycle']),
            models.Index(fields=['status', 'admission_cycle']),
            models.Index(fields=['program', 'status']),
            models.Index(fields=['date_of_birth']),
        ]

    def __str__(self):
        return f"{self.application_number or 'DRAFT'} - {self.full_name}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure tenant is set early
        if not self.tenant_id and hasattr(self, '_try_set_tenant'):
            self._try_set_tenant()
    
    def save(self, *args, **kwargs):
        """Ensure tenant is set before generating application number"""
        # Set tenant early if not set
        from apps.core.utils.tenant import get_current_tenant
        
        if not self.tenant_id:
            current_tenant = get_current_tenant()
            if current_tenant:
                self.tenant = current_tenant
            else:
                # Try to get tenant from admission cycle or program
                if hasattr(self, 'admission_cycle_id') and self.admission_cycle_id:
                    try:
                        cycle_tenant = self.admission_cycle.tenant
                        self.tenant = cycle_tenant
                    except (AdmissionCycle.DoesNotExist, AttributeError):
                        pass
                elif hasattr(self, 'program_id') and self.program_id:
                    try:
                        program_tenant = self.program.tenant
                        self.tenant = program_tenant
                    except (AdmissionProgram.DoesNotExist, AttributeError):
                        pass
        
        # Only generate application number if status is SUBMITTED and it doesn't exist
        if self.status == 'SUBMITTED' and not self.application_number:
            self.application_number = self.generate_application_number()
        
        # Call parent save
        super().save(*args, **kwargs)

    def generate_application_number(self):
        """Generate unique application number"""
        if not self.tenant:
            # Try to get tenant one more time
            from apps.core.utils.tenant import get_current_tenant
            current_tenant = get_current_tenant()
            if current_tenant:
                self.tenant = current_tenant
        
        if not self.tenant:
            # Fallback: create without tenant prefix
            prefix = f"APP-{self.admission_cycle.code}-"
        else:
            prefix = f"APP-{self.admission_cycle.code}-"
        
        # Get last application (filter by tenant if exists)
        if self.tenant:
            last_app = OnlineApplication.objects.filter(
                application_number__startswith=prefix,
                tenant=self.tenant
            ).order_by('application_number').last()
        else:
            last_app = OnlineApplication.objects.filter(
                application_number__startswith=prefix
            ).order_by('application_number').last()
        
        if last_app:
            try:
                last_num = int(last_app.application_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError, AttributeError):
                new_num = 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:05d}"

    @property
    def full_name(self):
        """Get full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    # In your OnlineApplication model class in models.py
    @property
    def age(self):
        """Calculate age - safely handle None date_of_birth"""
        if not self.date_of_birth:
            return None
        
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


    @property
    def is_eligible(self):
        """Check if application meets eligibility criteria"""
        return self.program.check_eligibility(
            self.previous_percentage or 0, 
            self.previous_qualification,
            self.date_of_birth
        )

    @property
    def formatted_address(self):
        """Get formatted address"""
        lines = [self.address_line1]
        if self.address_line2:
            lines.append(self.address_line2)
        lines.append(f"{self.city}, {self.state} - {self.pincode}")
        lines.append(self.country)
        return ", ".join(lines)

    def submit_application(self):
        """Submit the application"""
        if self.status == "DRAFT":
            self.status = "SUBMITTED"
            self.submission_date = timezone.now()
            self.save()
            
            # Create application log
            ApplicationLog.objects.create(
                application=self,
                action="SUBMITTED",
                description="Application submitted successfully",
                created_by=None  # System action
            )

    def update_status(self, new_status, user=None, notes=""):
        """Update application status with logging"""
        old_status = self.status
        self.status = new_status
        
        if new_status == "UNDER_REVIEW":
            self.review_date = timezone.now()
        elif new_status in ["ADMITTED", "REJECTED", "WAITLISTED"]:
            self.decision_date = timezone.now()
            
        self.save()
        
        # Log status change
        ApplicationLog.objects.create(
            application=self,
            action=f"STATUS_CHANGE_{new_status}",
            description=f"Status changed from {old_status} to {new_status}. {notes}",
            created_by=user
        )

    def make_payment(self, reference_id):
        """Mark application fee as paid"""
        self.application_fee_paid = True
        self.payment_reference = reference_id
        self.payment_date = timezone.now()
        self.save()
        
        ApplicationLog.objects.create(
            application=self,
            action="PAYMENT_RECEIVED",
            description=f"Application fee paid. Reference: {reference_id}",
            created_by=None
        )


# ==================== APPLICATION DOCUMENTS ====================

def application_document_upload_path(instance, filename):
    """Generate upload path for application documents"""
    ext = filename.split('.')[-1]
    # Handle case where application_number might be None/Draft
    app_num = instance.application.application_number or f"DRAFT_{instance.application.id}"
    filename = f"{slugify(app_num)}_{slugify(instance.document_type)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "admission_documents",
        str(instance.tenant.id),
        str(instance.application.id),
        filename
    )
class ApplicationDocument(BaseModel):
    """
    Documents submitted with school application
    """
    DOCUMENT_TYPES = (
        ("PHOTOGRAPH", _("Passport Size Photograph")),
        ("SIGNATURE", _("Signature")),
        ("BIRTH_CERTIFICATE", _("Birth Certificate")),
        ("AADHAAR_CARD", _("Aadhaar Card")),
        ("TENTH_MARKSHEET", _("10th Marksheet")),
        ("TWELFTH_MARKSHEET", _("12th Marksheet")),
        ("LAST_CLASS_MARKSHEET", _("Last Class Marksheet")),
        ("TRANSFER_CERTIFICATE", _("Transfer Certificate")),
        ("CASTE_CERTIFICATE", _("Caste Certificate")),
        ("INCOME_CERTIFICATE", _("Income Certificate")),
        ("DISABILITY_CERTIFICATE", _("Disability Certificate")),
        ("ENTRANCE_SCORE_CARD", _("Entrance Score Card")),
        ("PASSPORT", _("Passport")),
        ("MEDICAL_CERTIFICATE", _("Medical Certificate")),
        ("RESIDENTIAL_PROOF", _("Residential Proof")),
        ("OTHER", _("Other")),
    )

    application = models.ForeignKey(
        OnlineApplication,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Application")
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        verbose_name=_("Document Type")
    )
    file = models.FileField(
        upload_to='documents/',       
        verbose_name=_("Document File")
    )
    file_name = models.CharField(max_length=255, blank=True, verbose_name=_("Original File Name"))
    file_size = models.PositiveIntegerField(default=0, verbose_name=_("File Size"))
    
    # Verification
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_application_docs",
        verbose_name=_("Verified By")
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Verified At"))
    verification_notes = models.TextField(blank=True, verbose_name=_("Verification Notes"))
    
    # Metadata
    description = models.TextField(blank=True, verbose_name=_("Description"))

    class Meta:
        db_table = "admission_application_documents"
        verbose_name = _("Application Document")
        verbose_name_plural = _("Application Documents")
        unique_together = [['application', 'document_type']]
        indexes = [
            models.Index(fields=['application', 'document_type']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.application}"

    def clean(self):
        """Document validation"""
        # File size limit: 5MB
        if self.file and self.file.size > 5 * 1024 * 1024:
            raise ValidationError({'file': _('File size must be less than 5MB')})
        
        # Check filename length (Windows has ~260 char limit for paths)
        if self.file and len(self.file.name) > 200:
            raise ValidationError({
                'file': _('Filename is too long. Please use a shorter filename.')
            })

    def save(self, *args, **kwargs):
        """Save file metadata"""
        # Generate a clean filename if file is being uploaded
        if self.file and not self.pk:
            # Get original name and extension
            original_name = os.path.basename(self.file.name)
            name, ext = os.path.splitext(original_name)
            
            # Clean the name
            from django.utils.text import slugify
            cleaned_name = slugify(name)[:100]  # Limit to 100 chars
            
            # Generate new filename with short UUID
            short_uuid = str(uuid.uuid4()).split('-')[0]
            new_filename = f"{cleaned_name}_{short_uuid}{ext}"
            
            # Rename the file
            self.file.name = new_filename
        
        if self.file:
            self.file_name = os.path.basename(self.file.name)
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)

    def verify_document(self, user, notes=""):
        """Verify document"""
        self.is_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.verification_notes = notes
        self.save()

# ==================== APPLICATION GUARDIAN INFORMATION ====================

class ApplicationGuardian(BaseModel):
    """
    Guardian information for school application
    """
    RELATION_CHOICES = (
        ("FATHER", _("Father")),
        ("MOTHER", _("Mother")),
        ("GUARDIAN", _("Guardian")),
        ("GRANDFATHER", _("Grandfather")),
        ("GRANDMOTHER", _("Grandmother")),
        ("UNCLE", _("Uncle")),
        ("AUNT", _("Aunt")),
        ("OTHER", _("Other")),
    )

    OCCUPATION_CHOICES = (
        ("SERVICE", _("Service")),
        ("BUSINESS", _("Business")),
        ("GOVT", _("Government Job")),
        ("PRIVATE", _("Private Job")),
        ("RETIRED", _("Retired")),
        ("HOUSEWIFE", _("Housewife")),
        ("FARMER", _("Farmer")),
        ("TEACHER", _("Teacher")),
        ("DOCTOR", _("Doctor")),
        ("ENGINEER", _("Engineer")),
        ("STUDENT", _("Student")),
        ("UNEMPLOYED", _("Unemployed")),
        ("OTHER", _("Other")),
    )

    application = models.ForeignKey(
        OnlineApplication,
        on_delete=models.CASCADE,
        related_name="guardians",
        verbose_name=_("Application")
    )
    relation = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        verbose_name=_("Relation")
    )
    full_name = models.CharField(max_length=100, verbose_name=_("Full Name"))
    occupation = models.CharField(
        max_length=20,
        choices=OCCUPATION_CHOICES,
        blank=True,
        verbose_name=_("Occupation")
    )
    email = models.EmailField(blank=True, verbose_name=_("Email Address"))
    phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        verbose_name=_("Phone Number")
    )
    alternate_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Alternate Phone")
    )
    
    # Address
    address_line1 = models.CharField(max_length=255, verbose_name=_("Address Line 1"))
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_("Address Line 2"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state = models.CharField(max_length=100, verbose_name=_("State"))
    pincode = models.CharField(max_length=10, verbose_name=_("Pincode"))
    
    # Additional Information
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Annual Income")
    )
    qualification = models.CharField(max_length=100, blank=True, verbose_name=_("Qualification"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Is Primary Guardian"))
    is_emergency_contact = models.BooleanField(default=False, verbose_name=_("Is Emergency Contact"))

    class Meta:
        db_table = "admission_application_guardians"
        verbose_name = _("Application Guardian")
        verbose_name_plural = _("Application Guardians")
        constraints = [
            models.UniqueConstraint(
                fields=['application', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_guardian_per_application'
            )
        ]

    def __str__(self):
        return f"{self.full_name} ({self.relation}) - {self.application}"

    def clean(self):
        """Guardian validation"""
        if self.is_primary:
            existing_primary = ApplicationGuardian.objects.filter(
                application=self.application,
                is_primary=True
            ).exclude(id=self.id)
            
            if existing_primary.exists():
                raise ValidationError({
                    'is_primary': _("This application already has a primary guardian")
                })


# ==================== APPLICATION LOG & TRACKING ====================

class ApplicationLog(BaseModel):
    """
    Audit log for application status changes and activities
    """
    application = models.ForeignKey(
        OnlineApplication,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name=_("Application")
    )
    action = models.CharField(max_length=100, verbose_name=_("Action"))
    description = models.TextField(verbose_name=_("Description"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("IP Address"))
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))
    
    # User who performed the action (null for system actions)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_logs",
        verbose_name=_("Performed By")
    )

    class Meta:
        db_table = "admission_application_logs"
        verbose_name = _("Application Log")
        verbose_name_plural = _("Application Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['application', 'created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.application} - {self.action} - {self.created_at}"


# ==================== MERIT LIST & SELECTION ====================

class MeritList(BaseModel):
    """
    Merit list for school admission selection
    """
    admission_cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name="merit_lists",
        verbose_name=_("Admission Cycle")
    )
    program = models.ForeignKey(
        AdmissionProgram,
        on_delete=models.CASCADE,
        related_name="merit_lists",
        verbose_name=_("Program")
    )
    name = models.CharField(max_length=200, verbose_name=_("Merit List Name"))
    category = models.CharField(
        max_length=20,
        choices=OnlineApplication.CATEGORY_CHOICES,
        default="GENERAL",
        verbose_name=_("Category")
    )
    
    # Selection Criteria
    cutoff_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        verbose_name=_("Cutoff Percentage")
    )
    cutoff_entrance_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Cutoff Entrance Score")
    )
    cutoff_interview_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Cutoff Interview Score")
    )
    
    # Status
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    published_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Published Date"))

    class Meta:
        db_table = "admission_merit_lists"
        verbose_name = _("Merit List")
        verbose_name_plural = _("Merit Lists")
        unique_together = [['admission_cycle', 'program', 'category']]
        indexes = [
            models.Index(fields=['admission_cycle', 'program']),
            models.Index(fields=['is_published']),
        ]

    def __str__(self):
        return f"{self.name} - {self.program} - {self.category}"

    def publish(self):
        """Publish the merit list"""
        self.is_published = True
        self.published_date = timezone.now()
        self.save()

    def get_selected_applications(self):
        """Get applications selected in this merit list"""
        return self.entries.filter(is_selected=True).order_by('rank')


class MeritListEntry(BaseModel):
    """
    Individual entries in merit list
    """
    merit_list = models.ForeignKey(
        MeritList,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name=_("Merit List")
    )
    application = models.ForeignKey(
        OnlineApplication,
        on_delete=models.CASCADE,
        related_name="merit_list_entries",
        verbose_name=_("Application")
    )
    rank = models.PositiveIntegerField(verbose_name=_("Rank"))
    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Total Score")
    )
    is_selected = models.BooleanField(default=False, verbose_name=_("Is Selected"))
    selection_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Selection Date"))

    class Meta:
        db_table = "admission_merit_list_entries"
        verbose_name = _("Merit List Entry")
        verbose_name_plural = _("Merit List Entries")
        unique_together = [['merit_list', 'application']]
        ordering = ['rank']
        indexes = [
            models.Index(fields=['merit_list', 'rank']),
            models.Index(fields=['is_selected']),
        ]

    def __str__(self):
        return f"{self.merit_list} - Rank {self.rank} - {self.application}"

    def select(self):
        """Select this application"""
        self.is_selected = True
        self.selection_date = timezone.now()
        self.save()
        
        # Update application status
        self.application.update_status("ADMITTED")


# ==================== ADMISSION FORM CONFIGURATION ====================

class AdmissionFormConfig(BaseModel):
    """
    Dynamic form configuration for school admission applications
    """
    admission_cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name="form_configs",
        verbose_name=_("Admission Cycle")
    )
    program = models.ForeignKey(
        AdmissionProgram,
        on_delete=models.CASCADE,
        related_name="form_configs",
        verbose_name=_("Program")
    )
    
    # Form Configuration
    form_fields = models.JSONField(
        default=dict,
        verbose_name=_("Form Fields Configuration"),
        help_text=_("JSON configuration for form fields, validations, and visibility")
    )
    required_documents = models.JSONField(
        default=list,
        verbose_name=_("Required Documents"),
        help_text=_("List of required document types")
    )
    
    # Customization
    custom_css = models.TextField(blank=True, verbose_name=_("Custom CSS"))
    custom_js = models.TextField(blank=True, verbose_name=_("Custom JavaScript"))
    thank_you_message = models.TextField(blank=True, verbose_name=_("Thank You Message"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "admission_form_configs"
        verbose_name = _("Admission Form Configuration")
        verbose_name_plural = _("Admission Form Configurations")
        unique_together = [['admission_cycle', 'program']]

    def __str__(self):
        return f"Form Config - {self.program} - {self.admission_cycle}"


# ==================== ADMISSION STATISTICS ====================

class AdmissionStatistics(BaseModel):
    """
    Real-time admission statistics and analytics for school
    """
    admission_cycle = models.ForeignKey(
        AdmissionCycle,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name=_("Admission Cycle")
    )
    program = models.ForeignKey(
        AdmissionProgram,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name=_("Program")
    )
    
    # Application Counts
    total_applications = models.PositiveIntegerField(default=0, verbose_name=_("Total Applications"))
    draft_applications = models.PositiveIntegerField(default=0, verbose_name=_("Draft Applications"))
    submitted_applications = models.PositiveIntegerField(default=0, verbose_name=_("Submitted Applications"))
    under_review_applications = models.PositiveIntegerField(default=0, verbose_name=_("Under Review"))
    admitted_applications = models.PositiveIntegerField(default=0, verbose_name=_("Admitted Applications"))
    rejected_applications = models.PositiveIntegerField(default=0, verbose_name=_("Rejected Applications"))
    
    # Category-wise Statistics
    category_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Category Breakdown")
    )
    
    # Gender Statistics
    gender_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Gender Breakdown")
    )
    
    # Age Group Statistics
    age_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Age Group Breakdown")
    )
    
    # Date of last update
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))

    class Meta:
        db_table = "admission_statistics"
        verbose_name = _("Admission Statistics")
        verbose_name_plural = _("Admission Statistics")
        unique_together = [['admission_cycle', 'program']]
        indexes = [
            models.Index(fields=['admission_cycle', 'program']),
        ]

    def __str__(self):
        return f"Statistics - {self.program} - {self.admission_cycle}"

    def update_statistics(self):
        """Update statistics from current data"""
        applications = self.program.applications.all()
        
        self.total_applications = applications.count()
        self.draft_applications = applications.filter(status="DRAFT").count()
        self.submitted_applications = applications.filter(status="SUBMITTED").count()
        self.under_review_applications = applications.filter(status="UNDER_REVIEW").count()
        self.admitted_applications = applications.filter(status="ADMITTED").count()
        self.rejected_applications = applications.filter(status="REJECTED").count()
        
        # Update category breakdown
        self.category_breakdown = {}
        for category, _ in OnlineApplication.CATEGORY_CHOICES:
            count = applications.filter(category=category).count()
            self.category_breakdown[category] = count
            
        # Update gender breakdown
        self.gender_breakdown = {}
        for gender, _ in OnlineApplication.GENDER_CHOICES:
            count = applications.filter(gender=gender).count()
            self.gender_breakdown[gender] = count
            
        # Update age breakdown
        self.age_breakdown = {}
        age_groups = ["3-5", "6-8", "9-11", "12-14", "15-18"]
        for age_group in age_groups:
            # Implementation for age group counting would go here
            self.age_breakdown[age_group] = 0  # Placeholder

        self.save()