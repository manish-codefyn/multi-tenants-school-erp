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
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel, SoftDeleteModel

# Phone regex for validation
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
)

class Student(BaseModel):
    """
    Enhanced Student model with multi-tenant support and comprehensive features
    """
    STATUS_CHOICES = (
        ("ACTIVE", _("Active")),
        ("INACTIVE", _("Inactive")),
        ("ALUMNI", _("Alumni")),
        ("SUSPENDED", _("Suspended")),
        ("WITHDRAWN", _("Withdrawn")),
        ("GRADUATED", _("Graduated")),
        ("TRANSFERRED", _("Transferred")),
    )
    
    ADMISSION_TYPE_CHOICES = (
        ("REGULAR", _("Regular")),
        ("TRANSFER", _("Transfer")),
        ("LATERAL", _("Lateral Entry")),
        ("DIPLOMA", _("Diploma Holder")),
        ("QUOTA", _("Quota Seat")),
        ("MANAGEMENT", _("Management Quota")),
    )
    
    GENDER_CHOICES = (
        ("M", _("Male")),
        ("F", _("Female")),
        ("O", _("Other")),
        ("U", _("Undisclosed")),
    )
    
    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    )
    
    CATEGORY_CHOICES = (
        ("GENERAL", _("General")),
        ("SC", _("Scheduled Caste")),
        ("ST", _("Scheduled Tribe")),
        ("OBC", _("Other Backward Class")),
        ("EWS", _("Economically Weaker Section")),
        ("OTHER", _("Other")),
    )
    
    RELIGION_CHOICES = (
        ("HINDU", _("Hindu")),
        ("MUSLIM", _("Muslim")),
        ("CHRISTIAN", _("Christian")),
        ("SIKH", _("Sikh")),
        ("BUDDHIST", _("Buddhist")),
        ("JAIN", _("Jain")),
        ("PARSI", _("Parsi")),
        ("JEWISH", _("Jewish")),
        ("OTHER", _("Other")),
        ("NOT_SAY", _("Prefer not to say")),
    )
    
    MARITAL_STATUS_CHOICES = (
        ("SINGLE", _("Single")),
        ("MARRIED", _("Married")),
        ("DIVORCED", _("Divorced")),
        ("WIDOWED", _("Widowed")),
    )

    # ==================== CORE IDENTIFICATION ====================
    user = models.OneToOneField(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="student_profile",
        null=True,
        blank=True,
        verbose_name=_("System User Account")
    )
    
    # Institutional Identification
    admission_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Admission Number")
    )
    roll_number = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        verbose_name=_("Roll Number")
    )
    university_reg_no = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        verbose_name=_("University Registration Number")
    )
    
    # ==================== PERSONAL INFORMATION ====================
    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    middle_name = models.CharField(max_length=50, blank=True, verbose_name=_("Middle Name"))
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    
    # Enhanced personal details
    date_of_birth = models.DateField(verbose_name=_("Date of Birth"))
    place_of_birth = models.CharField(max_length=100, blank=True, verbose_name=_("Place of Birth"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Gender"))
    blood_group = models.CharField(
        max_length=3, 
        choices=BLOOD_GROUP_CHOICES, 
        blank=True,
        verbose_name=_("Blood Group")
    )
    nationality = models.CharField(max_length=50, default="Indian", verbose_name=_("Nationality"))
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        default="SINGLE",
        verbose_name=_("Marital Status")
    )
    
    # ==================== CONTACT INFORMATION ====================
    personal_email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name=_("Personal Email")
    )
    institutional_email = models.EmailField(
        blank=True,
        verbose_name=_("Institutional Email")
    )
    mobile_primary = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        verbose_name=_("Primary Mobile")
    )
    mobile_secondary = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Secondary Mobile")
    )
    
    # ==================== ACADEMIC INFORMATION ====================
    admission_type = models.CharField(
        max_length=20, 
        choices=ADMISSION_TYPE_CHOICES, 
        default="REGULAR",
        verbose_name=_("Admission Type")
    )
    enrollment_date = models.DateField(default=timezone.now, verbose_name=_("Enrollment Date"))
    academic_year = models.ForeignKey(
        "academics.AcademicYear", 
        on_delete=models.CASCADE, 
        related_name="students",
        verbose_name=_("Academic Year")
    )
   # UPDATE THESE FIELDS:
    current_class = models.ForeignKey(
        "academics.SchoolClass",  # Updated reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Current Class")
    )
    stream = models.ForeignKey(
        "academics.Stream",  # This model doesn't exist - you need to create it or remove this field
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Stream")
    )
    section = models.ForeignKey(
        "academics.Section", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="students",
        verbose_name=_("Section")
    )
  
    # ==================== SOCIO-ECONOMIC INFORMATION ====================
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default="GENERAL",
        verbose_name=_("Category")
    )
    religion = models.CharField(
        max_length=20, 
        choices=RELIGION_CHOICES, 
        blank=True,
        verbose_name=_("Religion")
    )
    is_minority = models.BooleanField(default=False, verbose_name=_("Belongs to Minority"))
    is_physically_challenged = models.BooleanField(default=False, verbose_name=_("Physically Challenged"))
    annual_family_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Annual Family Income")
    )
    
    # ==================== STATUS & TRACKING ====================
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="ACTIVE",
        db_index=True,
        verbose_name=_("Status")
    )
    status_changed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Status Changed Date")
    )
    graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Graduation Date")
    )
    
    # ==================== ACADEMIC TRACKING ====================
    current_semester = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name=_("Current Semester")
    )
    total_credits_earned = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Credits Earned")
    )
    cumulative_grade_point = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_("CGPA")
    )
    
    # ==================== FEE & FINANCIAL INFORMATION ====================
    fee_category = models.CharField(
        max_length=20,
        choices=(
            ("REGULAR", _("Regular")),
            ("CONCESSION", _("Concession")),
            ("SCHOLARSHIP", _("Scholarship")),
            ("FREE", _("Free")),
        ),
        default="REGULAR",
        verbose_name=_("Fee Category")
    )
    scholarship_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Scholarship Type")
    )
    
    # ==================== SYSTEM FIELDS ====================
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_students",
        verbose_name=_("Created By")
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_students",
        verbose_name=_("Last Updated By")
    )

    class Meta:
        db_table = "students_student"
        ordering = ["first_name", "last_name"]
        verbose_name = _("Student")
        verbose_name_plural = _("Students")
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['roll_number']),
            models.Index(fields=['personal_email']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant', 'current_class']),
            models.Index(fields=['tenant', 'academic_year']),
            models.Index(fields=['created_at']),
        ]
        permissions = [
            ("view_student_dashboard", "Can view student dashboard"),
            ("export_student_data", "Can export student data"),
            ("bulk_update_students", "Can bulk update students"),
        ]

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"

    def get_absolute_url(self):
        return reverse('students:student_detail', kwargs={'pk': self.pk})

    # ==================== PROPERTIES ====================
    @property
    def full_name(self):
        """Return full name with middle name if available"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        """Calculate current age"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def academic_age(self):
        """Calculate academic age (years since enrollment)"""
        today = timezone.now().date()
        return today.year - self.enrollment_date.year - (
            (today.month, today.day) < (self.enrollment_date.month, self.enrollment_date.day)
        )

    @property
    def is_eligible_for_exams(self):
        """Check if student is eligible to appear for exams"""
        from apps.finance.models import FeePayment
        # Check fee payment status and attendance requirements
        latest_fee = FeePayment.objects.filter(student=self).order_by('-created_at').first()
        attendance_percentage = self.get_attendance_percentage()
        
        return (
            self.status == "ACTIVE" and
            latest_fee and latest_fee.status == "PAID" and
            attendance_percentage >= 75.0
        )

    @property
    def current_address(self):
        """Get current address formatted"""
        address = self.addresses.filter(is_current=True).first()
        if address:
            return address.formatted_address
        return ""

    @property
    def permanent_address(self):
        """Get permanent address formatted"""
        address = self.addresses.filter(address_type="PERMANENT").first()
        if address:
            return address.formatted_address
        return ""

    # ==================== METHODS ====================
    def get_attendance_percentage(self, start_date=None, end_date=None):
        """Calculate attendance percentage for given period"""
        from apps.academics.models import Attendance
        attendances = Attendance.objects.filter(student=self)
        
        if start_date:
            attendances = attendances.filter(date__gte=start_date)
        if end_date:
            attendances = attendances.filter(date__lte=end_date)
            
        total_classes = attendances.count()
        if total_classes == 0:
            return 0.0
            
        present_classes = attendances.filter(status="PRESENT").count()
        return (present_classes / total_classes) * 100

    def get_academic_performance(self):
        """Get academic performance summary"""
        from apps.academics.models import Grade
        grades = Grade.objects.filter(
            enrollment__student=self,
            enrollment__status="COMPLETED"
        )
        
        if not grades.exists():
            return {"gpa": 0.0, "total_subjects": 0, "rank": None}
            
        total_grade_points = sum(grade.grade_point for grade in grades if grade.grade_point)
        total_subjects = grades.count()
        
        return {
            "gpa": total_grade_points / total_subjects if total_subjects > 0 else 0.0,
            "total_subjects": total_subjects,
            "rank": self.get_class_rank()
        }

    def get_class_rank(self):
        """Calculate student's rank in class"""
        # Implementation depends on your ranking logic
        return None

    def generate_institutional_email(self):
        """Generate institutional email if not provided"""
        if not self.institutional_email and self.admission_number:
            domain = self.tenant.domains.filter(is_primary=True).first()
            if domain:
                self.institutional_email = f"{self.admission_number.lower()}@{domain.domain}"
            else:
                self.institutional_email = f"{self.admission_number.lower()}@student.institution.edu"
        return self.institutional_email

    def promote_to_next_semester(self):
        """Promote student to next semester"""
        if self.status == "ACTIVE":
            self.current_semester += 1
            self.save(update_fields=['current_semester'])
            
            # Create academic history record
            StudentAcademicHistory.objects.create(
                student=self,
                academic_year=self.academic_year,
                class_name=self.current_class,
                section=self.section,
                semester=self.current_semester - 1,  # Previous semester
                status="COMPLETED",
                promoted=True
            )

    def create_user_account(self):
        """Create system user account for student"""
        if not self.user:
            from apps.users.models import User
            user = User.objects.create_user(
                email=self.personal_email,
                password=User.objects.make_random_password(),
                first_name=self.first_name,
                last_name=self.last_name,
                tenant=self.tenant,
                role="student"
            )
            self.user = user
            self.save(update_fields=['user'])

    # ==================== DOCUMENT METHODS ====================
    def get_document(self, doc_type):
        """Return the first document of the given type, or None."""
        return self.documents.filter(doc_type=doc_type).first()    

    def get_photo(self):
        return self.get_document("PHOTO")

    def get_birth_certificate(self):
        return self.get_document("BIRTH_CERTIFICATE")

    def get_aadhaar(self):
        return self.get_document("AADHAAR")

    def has_required_documents(self):
        """Check if student has all required documents"""
        required_docs = ["PHOTO", "BIRTH_CERTIFICATE", "AADHAAR"]
        return all(self.get_document(doc) for doc in required_docs)

    # ==================== VALIDATION & CLEANING ====================
    def clean(self):
        """Comprehensive validation"""
        errors = {}
        today = timezone.now().date()

        # Date validations
        if self.date_of_birth >= today:
            errors['date_of_birth'] = _("Date of birth must be in the past")
        
        if self.enrollment_date > today:
            errors['enrollment_date'] = _("Enrollment date cannot be in the future")

        # Age validation
        if self.age < 3:
            errors['date_of_birth'] = _("Student must be at least 3 years old")

        # Academic validation
        if self.section and self.current_class and self.section.class_name != self.current_class:
            errors['section'] = _("Selected section does not belong to the selected class")

        # Email validation
        if Student.objects.filter(
            personal_email=self.personal_email, 
            tenant=self.tenant
        ).exclude(id=self.id).exists():
            errors['personal_email'] = _("A student with this email already exists")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Enhanced save with auto-generation"""
        # Generate admission number if not provided
        if not self.admission_number:
            self.admission_number = self.generate_admission_number()
            
        # Generate institutional email
        if not self.institutional_email:
            self.institutional_email = self.generate_institutional_email()
            
        # Update status changed date if status changed
        if self.pk:
            original = Student.objects.get(pk=self.pk)
            if original.status != self.status:
                self.status_changed_date = timezone.now()
        
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_admission_number(self):
        """Generate unique admission number"""
        prefix = f"ADM-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_student = Student.objects.filter(
            admission_number__startswith=prefix,
            tenant=self.tenant
        ).order_by('admission_number').last()
        
        if last_student:
            last_number = int(last_student.admission_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}{new_number:04d}"

    # ==================== API SERIALIZATION ====================
    def to_api_dict(self, include_sensitive=False):
        """Convert to API-safe dictionary"""
        from apps.core.utils.serializers import model_to_dict
        
        data = model_to_dict(self, exclude=['user', 'tenant'])
        data['id'] = str(self.id)
        data['full_name'] = self.full_name
        data['age'] = self.age
        data['current_address'] = self.current_address
        data['permanent_address'] = self.permanent_address
        
        if include_sensitive:
            data['medical_info'] = self.medical_info.to_dict() if hasattr(self, 'medical_info') else {}
            data['identification'] = self.identification.to_dict() if hasattr(self, 'identification') else {}
            
        return data

class Guardian(BaseModel):
    """
    Enhanced Guardian model with comprehensive relationship tracking
    """
    RELATION_CHOICES = (
        ("FATHER", _("Father")),
        ("MOTHER", _("Mother")),
        ("GUARDIAN", _("Guardian")),
        ("GRANDFATHER", _("Grandfather")),
        ("GRANDMOTHER", _("Grandmother")),
        ("UNCLE", _("Uncle")),
        ("AUNT", _("Aunt")),
        ("BROTHER", _("Brother")),
        ("SISTER", _("Sister")),
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
    
    QUALIFICATION_CHOICES = (
        ("BELOW_10TH", _("Below 10th")),
        ("10TH", _("10th Pass")),
        ("12TH", _("12th Pass")),
        ("DIPLOMA", _("Diploma")),
        ("GRADUATE", _("Graduate")),
        ("POST_GRADUATE", _("Post Graduate")),
        ("PHD", _("PhD")),
        ("OTHER", _("Other")),
    )

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name="guardians",
        verbose_name=_("Student")
    )
    
    # Personal Information
    relation = models.CharField(
        max_length=20, 
        choices=RELATION_CHOICES,
        verbose_name=_("Relation")
    )
    full_name = models.CharField(max_length=100, verbose_name=_("Full Name"))
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth")
    )
    
    # Contact Information
    email = models.EmailField(blank=True, verbose_name=_("Email Address"))
    phone_primary = models.CharField(
        max_length=17, 
        validators=[phone_regex],
        verbose_name=_("Primary Phone")
    )
    phone_secondary = models.CharField(
        max_length=17, 
        validators=[phone_regex], 
        blank=True,
        verbose_name=_("Secondary Phone")
    )
    
    # Professional Information
    occupation = models.CharField(
        max_length=20, 
        choices=OCCUPATION_CHOICES, 
        blank=True,
        verbose_name=_("Occupation")
    )
    qualification = models.CharField(
        max_length=20,
        choices=QUALIFICATION_CHOICES,
        blank=True,
        verbose_name=_("Educational Qualification")
    )
    company_name = models.CharField(max_length=100, blank=True, verbose_name=_("Company Name"))
    designation = models.CharField(max_length=100, blank=True, verbose_name=_("Designation"))
    annual_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Annual Income")
    )
    
    # Guardian Specific
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Is Primary Guardian")
    )
    is_emergency_contact = models.BooleanField(
        default=False,
        verbose_name=_("Is Emergency Contact")
    )
    can_pickup = models.BooleanField(
        default=True,
        verbose_name=_("Can Pickup Student")
    )
    
    # Identification
    aadhaar_number = EncryptedCharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name=_("Aadhaar Number")
    )
    pan_number = EncryptedCharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("PAN Number")
    )

    class Meta:
        db_table = "students_guardian"
        verbose_name = _("Guardian")
        verbose_name_plural = _("Guardians")
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_guardian_per_student'
            ),
            models.UniqueConstraint(
                fields=['student', 'is_emergency_contact'],
                condition=models.Q(is_emergency_contact=True),
                name='unique_emergency_contact_per_student'
            )
        ]
        indexes = [
            models.Index(fields=['student', 'relation']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.relation}) - {self.student}"

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def clean(self):
        """Enhanced validation"""
        errors = {}
        
        # Primary guardian validation
        if self.is_primary:
            existing_primary = Guardian.objects.filter(
                student=self.student, 
                is_primary=True
            ).exclude(id=self.id)
            
            if existing_primary.exists():
                errors['is_primary'] = _("This student already has a primary guardian")

        # Emergency contact validation
        if self.is_emergency_contact:
            existing_emergency = Guardian.objects.filter(
                student=self.student, 
                is_emergency_contact=True
            ).exclude(id=self.id)
            
            if existing_emergency.exists():
                errors['is_emergency_contact'] = _("This student already has an emergency contact")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StudentAddress(BaseModel):
    """
    Enhanced address model with geolocation support
    """
    ADDRESS_TYPE_CHOICES = (
        ("PERMANENT", _("Permanent")),
        ("CORRESPONDENCE", _("Correspondence")),
        ("LOCAL_GUARDIAN", _("Local Guardian")),
        ("HOSTEL", _("Hostel")),
    )

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name="addresses",
        verbose_name=_("Student")
    )
    
    address_type = models.CharField(
        max_length=20, 
        choices=ADDRESS_TYPE_CHOICES,
        default="PERMANENT",
        verbose_name=_("Address Type")
    )
    
    # Address Components
    address_line1 = models.CharField(max_length=255, verbose_name=_("Address Line 1"))
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name=_("Address Line 2"))
    landmark = models.CharField(max_length=100, blank=True, verbose_name=_("Landmark"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    state = models.CharField(max_length=100, verbose_name=_("State"))
    pincode = models.CharField(max_length=10, verbose_name=_("Pincode"))
    country = models.CharField(max_length=100, default="India", verbose_name=_("Country"))
    
    # Geolocation
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Latitude")
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Longitude")
    )
    
    # Status
    is_current = models.BooleanField(default=True, verbose_name=_("Is Current Address"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))

    class Meta:
        db_table = "students_address"
        verbose_name = _("Student Address")
        verbose_name_plural = _("Student Addresses")
        unique_together = [['student', 'address_type']]
        indexes = [
            models.Index(fields=['student', 'is_current']),
            models.Index(fields=['city', 'state']),
        ]

    def __str__(self):
        return f"{self.address_type} Address - {self.student}"

    @property
    def formatted_address(self):
        """Return formatted address string"""
        lines = [self.address_line1]
        if self.address_line2:
            lines.append(self.address_line2)
        if self.landmark:
            lines.append(f"Landmark: {self.landmark}")
        lines.append(f"{self.city}, {self.state} - {self.pincode}")
        lines.append(self.country)
        return ", ".join(lines)

    @property
    def google_maps_url(self):
        """Generate Google Maps URL"""
        if self.latitude and self.longitude:
            return f"https://maps.google.com/?q={self.latitude},{self.longitude}"
        return None

    def clean(self):
        """Address validation"""
        if self.address_type == "PERMANENT" and not self.is_verified:
            # Permanent addresses should be verified
            self.is_verified = True

    def geocode_address(self):
        """Geocode address to get coordinates"""
        # Implementation using Google Maps API or similar
        pass

def student_document_upload_path(instance, filename):
    """Generate upload path for student documents"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.student.admission_number)}_{slugify(instance.doc_type)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "student_documents", 
        str(instance.tenant.id),
        str(instance.student.id), 
        filename
    )


class StudentDocument(BaseModel):
    """
    Enhanced document model with versioning and approval workflow
    """
    DOCUMENT_TYPE_CHOICES = (
        ("PHOTO", _("Photograph")),
        ("BIRTH_CERTIFICATE", _("Birth Certificate")),
        ("AADHAAR", _("Aadhaar Card")),
        ("PAN_CARD", _("PAN Card")),
        ("PASSPORT", _("Passport")),
        ("VOTER_ID", _("Voter ID")),
        ("DRIVING_LICENSE", _("Driving License")),
        ("PREVIOUS_MARKSHEET", _("Previous Marksheet")),
        ("TRANSFER_CERTIFICATE", _("Transfer Certificate")),
        ("MEDICAL_CERTIFICATE", _("Medical Certificate")),
        ("CASTE_CERTIFICATE", _("Caste Certificate")),
        ("INCOME_CERTIFICATE", _("Income Certificate")),
        ("DISABILITY_CERTIFICATE", _("Disability Certificate")),
        ("MIGRATION_CERTIFICATE", _("Migration Certificate")),
        ("CHARACTER_CERTIFICATE", _("Character Certificate")),
        ("SCHOLARSHIP_DOCUMENT", _("Scholarship Document")),
        ("OTHER", _("Other")),
    )
    
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("APPROVED", _("Approved")),
        ("REJECTED", _("Rejected")),
        ("EXPIRED", _("Expired")),
    )

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name="documents",
        verbose_name=_("Student")
    )
    
    doc_type = models.CharField(
        max_length=50, 
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name=_("Document Type")
    )
    
    # File Management
    file = models.FileField(
        upload_to=student_document_upload_path, 
        verbose_name=_("Document File")
    )
    file_name = models.CharField(max_length=255, blank=True, verbose_name=_("Original File Name"))
    file_size = models.PositiveIntegerField(default=0, verbose_name=_("File Size (bytes)"))
    file_hash = models.CharField(max_length=64, blank=True, verbose_name=_("File Hash"))
    
    # Metadata
    description = models.TextField(blank=True, verbose_name=_("Description"))
    issue_date = models.DateField(null=True, blank=True, verbose_name=_("Issue Date"))
    expiry_date = models.DateField(null=True, blank=True, verbose_name=_("Expiry Date"))
    issuing_authority = models.CharField(max_length=200, blank=True, verbose_name=_("Issuing Authority"))
    
    # Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
        verbose_name=_("Verified By")
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Verified At"))
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection Reason"))
    
    # Versioning
    version = models.PositiveIntegerField(default=1, verbose_name=_("Version"))
    is_current = models.BooleanField(default=True, verbose_name=_("Is Current Version"))
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_versions",
        verbose_name=_("Previous Version")
    )

    class Meta:
        db_table = "students_documents"
        verbose_name = _("Student Document")
        verbose_name_plural = _("Student Documents")
        indexes = [
            models.Index(fields=['student', 'doc_type', 'is_current']),
            models.Index(fields=['status', 'is_verified']),
            models.Index(fields=['expiry_date']),
        ]
        unique_together = [['student', 'doc_type', 'version']]

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.student} (v{self.version})"

    def clean(self):
        """Document validation"""
        errors = {}
        
        # File size validation (10MB max)
        if self.file and self.file.size > 10 * 1024 * 1024:
            errors['file'] = _('File size must be less than 10MB')
            
        # Expiry date validation
        if self.expiry_date and self.expiry_date < timezone.now().date():
            errors['expiry_date'] = _('Expiry date cannot be in the past')
            
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Enhanced save with file processing"""
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
            # Calculate file hash
            import hashlib
            self.file_hash = hashlib.sha256(self.file.read()).hexdigest()
            
        # Handle versioning
        if self.pk:  # Existing document
            original = StudentDocument.objects.get(pk=self.pk)
            if original.file != self.file:  # File changed
                self.version += 1
                original.is_current = False
                original.save()
                self.previous_version = original
                
        super().save(*args, **kwargs)

    def verify_document(self, user, notes=""):
        """Verify document"""
        self.status = "APPROVED"
        self.is_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.rejection_reason = ""
        self.save()

    def reject_document(self, user, reason):
        """Reject document"""
        self.status = "REJECTED"
        self.is_verified = False
        self.verified_by = user
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    @property
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def get_download_url(self):
        """Get secure download URL"""
        from django.urls import reverse
        return reverse('students:download_document', kwargs={'pk': self.pk})


class StudentMedicalInfo(BaseModel):
    """
    Comprehensive medical information with emergency contacts
    """
    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    )

    student = models.OneToOneField(
        Student, 
        on_delete=models.CASCADE, 
        related_name="medical_info",
        verbose_name=_("Student")
    )
    
    # Basic Medical Information
    blood_group = models.CharField(
        max_length=3, 
        choices=BLOOD_GROUP_CHOICES, 
        blank=True,
        verbose_name=_("Blood Group")
    )
    height_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Height (cm)")
    )
    weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Weight (kg)")
    )
    bmi = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("BMI")
    )
    
    # Medical Conditions
    known_allergies = models.TextField(
        blank=True,
        verbose_name=_("Known Allergies"),
        help_text=_("List any known allergies (food, medication, environmental)")
    )
    chronic_conditions = models.TextField(
        blank=True,
        verbose_name=_("Chronic Medical Conditions"),
        help_text=_("List any chronic medical conditions (asthma, diabetes, etc.)")
    )
    current_medications = models.TextField(
        blank=True,
        verbose_name=_("Current Medications"),
        help_text=_("List any current medications with dosage")
    )
    dietary_restrictions = models.TextField(
        blank=True,
        verbose_name=_("Dietary Restrictions"),
        help_text=_("List any dietary restrictions or preferences")
    )
    
    # Disability Information
    has_disability = models.BooleanField(
        default=False,
        verbose_name=_("Has Disability")
    )
    disability_type = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name=_("Disability Type")
    )
    disability_percentage = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name=_("Disability Percentage")
    )
    disability_certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Disability Certificate Number")
    )
    
    # Vaccination Records
    vaccination_records = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Vaccination Records")
    )
    
    # Emergency Information
    emergency_contact_name = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name=_("Emergency Contact Name")
    )
    emergency_contact_relation = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_("Emergency Contact Relation")
    )
    emergency_contact_phone = models.CharField(
        max_length=17, 
        validators=[phone_regex], 
        blank=True,
        verbose_name=_("Emergency Contact Phone")
    )
    emergency_contact_alt_phone = models.CharField(
        max_length=17, 
        validators=[phone_regex], 
        blank=True,
        verbose_name=_("Alternative Emergency Phone")
    )
    
    # Medical Insurance
    has_medical_insurance = models.BooleanField(
        default=False,
        verbose_name=_("Has Medical Insurance")
    )
    insurance_provider = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Insurance Provider")
    )
    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Insurance Policy Number")
    )
    insurance_valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Insurance Valid Until")
    )
    
    # Additional Information
    special_instructions = models.TextField(
        blank=True,
        verbose_name=_("Special Medical Instructions"),
        help_text=_("Any special instructions for medical emergencies")
    )
    last_medical_checkup = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Last Medical Checkup Date")
    )

    class Meta:
        db_table = "students_medical_info"
        verbose_name = _("Medical Information")
        verbose_name_plural = _("Medical Information")

    def __str__(self):
        return f"Medical Info - {self.student}"

    def save(self, *args, **kwargs):
        """Calculate BMI on save"""
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = self.weight_kg / (height_m * height_m)
        super().save(*args, **kwargs)

    def clean(self):
        """Medical information validation"""
        errors = {}
        
        if self.has_disability and not self.disability_type:
            errors['disability_type'] = _('Disability type is required when disability is marked')
            
        if self.disability_percentage and not self.has_disability:
            errors['has_disability'] = _('Disability must be checked if disability percentage is provided')
            
        if self.has_medical_insurance and not self.insurance_provider:
            errors['insurance_provider'] = _('Insurance provider is required when insurance is marked')

        if errors:
            raise ValidationError(errors)

    @property
    def bmi_category(self):
        """Get BMI category"""
        if not self.bmi:
            return "Unknown"
            
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 25:
            return "Normal"
        elif 25 <= self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def update_vaccination_record(self, vaccine_name, date, dose=None):
        """Update vaccination record"""
        if 'vaccinations' not in self.vaccination_records:
            self.vaccination_records['vaccinations'] = []
            
        self.vaccination_records['vaccinations'].append({
            'name': vaccine_name,
            'date': date.isoformat(),
            'dose': dose
        })
        self.save()

    def get_emergency_info(self):
        """Get formatted emergency information"""
        return {
            'contact_name': self.emergency_contact_name,
            'relation': self.emergency_contact_relation,
            'phone': self.emergency_contact_phone,
            'alt_phone': self.emergency_contact_alt_phone,
            'allergies': self.known_allergies,
            'conditions': self.chronic_conditions,
            'medications': self.current_medications,
            'special_instructions': self.special_instructions
        }

class StudentAcademicHistory(BaseModel):
    """
    Student academic history and progression
    """
    student = models.ForeignKey(
        'Student',
        on_delete=models.CASCADE,
        related_name="academic_history",
        verbose_name=_("Student")
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.CASCADE,
        related_name="student_history",
        verbose_name=_("Academic Year")
    )
    class_name = models.ForeignKey(
        "academics.SchoolClass",  # Updated reference
        on_delete=models.CASCADE,
        related_name="student_history",
        verbose_name=_("Class")
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="student_history",
        verbose_name=_("Section")
    )
    roll_number = models.CharField(
        max_length=20,
        verbose_name=_("Roll Number")
    )
    overall_grade = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Overall Grade")
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Percentage")
    )
    result = models.CharField(
        max_length=20,
        choices=(
            ("PASS", _("Pass")),
            ("FAIL", _("Fail")),
            ("COMPARTMENT", _("Compartment")),
            ("APPEARING", _("Appearing")),
        ),
        default="APPEARING",
        verbose_name=_("Result")
    )
    remarks = models.TextField(
        blank=True,
        verbose_name=_("Remarks")
    )

    class Meta:
        db_table = "students_academic_history"
        verbose_name = _("Academic History")
        verbose_name_plural = _("Academic History")
        unique_together = [['student', 'academic_year']]
        # FIX THE ORDERING - use the actual field name
        ordering = ["class_name__order", "academic_year"]
        # OR if class_name doesn't have order field, use:
        # ordering = ["academic_year", "class_name__name"]

    def __str__(self):
        return f"{self.student} - {self.academic_year} - {self.class_name}"

    def clean(self):
        """Academic history validation"""
        errors = {}
        
        # Percentage validation
        if self.percentage is not None:
            if self.result == "PASS" and self.percentage < self.class_name.pass_percentage:
                errors['percentage'] = _('Percentage should meet passing criteria for PASS result')
            elif self.result == "FAIL" and self.percentage >= self.class_name.pass_percentage:
                errors['result'] = _('Result should be PASS if percentage meets passing criteria')

        # Date validation
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors['end_date'] = _('End date must be after start date')
            
        # Roll number uniqueness within class and academic year
        if StudentAcademicHistory.objects.filter(
            academic_year=self.academic_year,
            class_name=self.class_name,
            section=self.section,
            roll_number=self.roll_number
        ).exclude(id=self.id).exists():
            errors['roll_number'] = _('Roll number must be unique within the same class and academic year')
            
        if errors:
            raise ValidationError(errors)

    @property
    def is_completed(self):
        """Check if academic year is completed"""
        return self.status == "COMPLETED"

    @property
    def pass_fail_status(self):
        """Get pass/fail status"""
        return "PASS" if self.promoted else "FAIL"

    def calculate_percentage(self):
        """Calculate percentage if total and max marks are available"""
        if self.total_marks and self.max_marks and self.max_marks > 0:
            self.percentage = (self.total_marks / self.max_marks) * 100
        return self.percentage

    def save(self, *args, **kwargs):
        """Enhanced save with automatic calculations"""
        # Calculate percentage if not provided
        if not self.percentage and self.total_marks and self.max_marks:
            self.calculate_percentage()
            
        # Set promoted based on result
        if self.result in ["PASS", "APPEARING"]:
            self.promoted = True
        else:
            self.promoted = False
            
        super().save(*args, **kwargs)

class StudentIdentification(BaseModel):
    """
    Comprehensive identification and government ID management
    """
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='identification',
        verbose_name=_("Student")
    )
    
    # Government IDs
    aadhaar_number = EncryptedCharField(
        max_length=12, 
        blank=True, 
        null=True,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{12}$', message=_('Aadhaar number must be 12 digits'))],
        verbose_name=_("Aadhaar Number")
    )
    pan_number = EncryptedCharField(
        max_length=10, 
        blank=True, 
        null=True, 
        unique=True,
        validators=[RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message=_('Invalid PAN format'))],
        verbose_name=_("PAN Number")
    )
    passport_number = EncryptedCharField(
        max_length=20, 
        blank=True, 
        null=True,
        unique=True,
        verbose_name=_("Passport Number")
    )
    driving_license = EncryptedCharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Driving License Number")
    )
    voter_id = EncryptedCharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Voter ID Number")
    )
    
    # Educational IDs
    abc_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name=_("ABC ID")
    )
    shiksha_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name=_("Shiksha ID")
    )
    udise_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("UDISE ID")
    )
    
    # Bank Details
    bank_account_number = EncryptedCharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Bank Account Number")
    )
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Name")
    )
    bank_branch = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Bank Branch")
    )
    ifsc_code = models.CharField(
        max_length=11,
        blank=True,
        validators=[RegexValidator(regex=r'^[A-Z]{4}0[A-Z0-9]{6}$', message=_('Invalid IFSC code'))],
        verbose_name=_("IFSC Code")
    )
    
    # Verification Status
    aadhaar_verified = models.BooleanField(default=False, verbose_name=_("Aadhaar Verified"))
    pan_verified = models.BooleanField(default=False, verbose_name=_("PAN Verified"))
    passport_verified = models.BooleanField(default=False, verbose_name=_("Passport Verified"))
    
    # Social Security
    social_security_number = EncryptedCharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Social Security Number")
    )
    national_insurance_number = EncryptedCharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("National Insurance Number")
    )

    class Meta:
        db_table = 'students_identification'
        verbose_name = _("Student Identification")
        verbose_name_plural = _("Student Identifications")
        indexes = [
            models.Index(fields=['aadhaar_number']),
            models.Index(fields=['pan_number']),
            models.Index(fields=['passport_number']),
        ]

    def __str__(self):
        return f"Identification for {self.student.full_name}"

    def clean(self):
        """Identification validation"""
        # Add any custom validation logic here
        pass

    @property
    def has_complete_identification(self):
        """Check if student has complete identification"""
        return all([
            self.aadhaar_number,
            self.pan_number or self.passport_number
        ])

    def verify_aadhaar(self):
        """Mark Aadhaar as verified"""
        self.aadhaar_verified = True
        self.save(update_fields=['aadhaar_verified'])

    def verify_pan(self):
        """Mark PAN as verified"""
        self.pan_verified = True
        self.save(update_fields=['pan_verified'])

    def get_identification_summary(self):
        """Get identification summary"""
        return {
            'aadhaar': {
                'number': self.aadhaar_number,
                'verified': self.aadhaar_verified
            },
            'pan': {
                'number': self.pan_number,
                'verified': self.pan_verified
            },
            'passport': {
                'number': self.passport_number,
                'verified': self.passport_verified
            },
            'bank_details': {
                'account_number': self.bank_account_number,
                'bank_name': self.bank_name,
                'ifsc_code': self.ifsc_code
            }
        }