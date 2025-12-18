import uuid
import os
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from encrypted_model_fields.fields import EncryptedCharField

# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel
from apps.academics.models import Subject, SchoolClass, Section, AcademicYear, GradingSystem, Grade
from apps.students.models import Student


def exam_document_upload_path(instance, filename):
    """Generate upload path for exam documents"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.name)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "exam_documents",
        str(instance.tenant.id),
        filename
    )


class ExamType(BaseModel):
    """
    Types of examinations (Unit Test, Mid-Term, Final, etc.)
    """
    name = models.CharField(max_length=100, verbose_name=_("Exam Type Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Exam Type Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    weightage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Weightage (%)"),
        help_text=_("Percentage weight in overall assessment")
    )
    is_final = models.BooleanField(default=False, verbose_name=_("Is Final Exam"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "exams_exam_type"
        ordering = ["order", "name"]
        verbose_name = _("Exam Type")
        verbose_name_plural = _("Exam Types")
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['weightage']),
        ]

    def __str__(self):
        return f"{self.name} ({self.weightage}%)"

    def clean(self):
        """Validate exam type"""
        if self.weightage < 0 or self.weightage > 100:
            raise ValidationError({
                'weightage': _('Weightage must be between 0 and 100 percent')
            })


class Exam(BaseModel):
    """
    Main exam model representing an examination event
    """
    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("SCHEDULED", _("Scheduled")),
        ("ONGOING", _("Ongoing")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
        ("POSTPONED", _("Postponed")),
    )

    EXAM_MODE_CHOICES = (
        ("ONLINE", _("Online")),
        ("OFFLINE", _("Offline")),
        ("HYBRID", _("Hybrid")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Exam Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Exam Code"))
    exam_type = models.ForeignKey(
        ExamType,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Exam Type")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Academic Year")
    )
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="exams",
        verbose_name=_("Class")
    )
    
    # Scheduling
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    exam_mode = models.CharField(
        max_length=10,
        choices=EXAM_MODE_CHOICES,
        default="OFFLINE",
        verbose_name=_("Exam Mode")
    )
    
    # Configuration
    total_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Marks")
    )
    pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=35.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Pass Percentage")
    )
    grace_marks = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Grace Marks")
    )
    
    # Status & Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    instructions = models.TextField(blank=True, verbose_name=_("Exam Instructions"))
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Published At"))

    class Meta:
        db_table = "exams_exam"
        ordering = ["-start_date", "name"]
        verbose_name = _("Exam")
        verbose_name_plural = _("Exams")
        indexes = [
            models.Index(fields=['academic_year', 'class_name']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'is_published']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'class_name', 'exam_type'],
                name='unique_exam_per_class_type_year'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.class_name} ({self.academic_year})"

    @property
    def duration_days(self):
        """Calculate exam duration in days"""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_currently_running(self):
        """Check if exam is currently active"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == "ONGOING"

    def clean(self):
        """Validate exam data"""
        errors = {}
        
        # Date validation
        if self.start_date > self.end_date:
            errors['end_date'] = _('End date must be after start date')
        
        # Academic year validation
        if not (self.start_date >= self.academic_year.start_date and 
                self.end_date <= self.academic_year.end_date):
            errors['start_date'] = _('Exam dates must be within academic year')
            
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Enhanced save with status management"""
        # Load defaults from configuration
        if self.academic_year and not self.pk:  # Only on creation or if explicitly needed
            try:
                from apps.configuration.models import AcademicConfiguration
                config = AcademicConfiguration.get_for_year(self.academic_year)
                
                if self.pass_percentage == 35.00:  # Default value
                    self.pass_percentage = config.pass_percentage
                    
                if self.grace_marks == 0.00:  # Default value
                    self.grace_marks = config.grace_marks
            except Exception:
                pass  # Fallback to model defaults if config fails

        # Auto-update status based on dates
        today = timezone.now().date()
        if self.status != "CANCELLED" and self.status != "POSTPONED":
            if today < self.start_date:
                self.status = "SCHEDULED"
            elif self.start_date <= today <= self.end_date:
                self.status = "ONGOING"
            elif today > self.end_date:
                self.status = "COMPLETED"
        
        # Set published timestamp
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
            
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('exams:exam_detail', kwargs={'pk': self.pk}) 

class ExamSubject(BaseModel):
    """
    Subjects included in an exam with specific configurations
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="exam_subjects",
        verbose_name=_("Exam")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="exam_subjects",
        verbose_name=_("Subject")
    )
    
    # Marks configuration
    max_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Maximum Marks")
    )
    pass_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Passing Marks")
    )
    practical_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Practical Marks")
    )
    theory_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Theory Marks")
    )
    
    # Scheduling
    exam_date = models.DateField(verbose_name=_("Exam Date"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    
    # Additional configuration
    is_compulsory = models.BooleanField(default=True, verbose_name=_("Is Compulsory"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    room_allocations = models.TextField(blank=True, verbose_name=_("Room Allocations"))

    class Meta:
        db_table = "exams_exam_subject"
        ordering = ["exam", "order", "subject"]
        verbose_name = _("Exam Subject")
        verbose_name_plural = _("Exam Subjects")
        unique_together = [['exam', 'subject']]
        indexes = [
            models.Index(fields=['exam', 'exam_date']),
            models.Index(fields=['subject', 'exam_date']),
        ]

    def __str__(self):
        return f"{self.exam.name} - {self.subject.name}"

    @property
    def duration_hours(self):
        """Calculate exam duration in hours"""
        start_dt = timezone.datetime.combine(self.exam_date, self.start_time)
        end_dt = timezone.datetime.combine(self.exam_date, self.end_time)
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600

    def clean(self):
        """Validate exam subject"""
        errors = {}
        
        # Marks validation
        if self.pass_marks > self.max_marks:
            errors['pass_marks'] = _('Pass marks cannot exceed maximum marks')
            
        if (self.theory_marks + self.practical_marks) != self.max_marks:
            errors['max_marks'] = _('Theory + Practical marks must equal maximum marks')
            
        # Date validation
        if self.exam_date < self.exam.start_date or self.exam_date > self.exam.end_date:
            errors['exam_date'] = _('Exam date must be within exam schedule')
            
        if errors:
            raise ValidationError(errors)





class ExamResult(BaseModel):
    """
    Main exam result model for student performance tracking
    """
    STATUS_CHOICES = (
        ("PASS", _("Pass")),
        ("FAIL", _("Fail")),
        ("COMPARTMENT", _("Compartment")),
        ("ABSENT", _("Absent")),
        ("MALPRACTICE", _("Malpractice")),
        ("WITHHELD", _("Withheld")),
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name=_("Exam")
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="exam_results",
        verbose_name=_("Student")
    )
    
    # Overall performance
    total_marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Marks Obtained")
    )
    total_max_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Maximum Marks")
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Percentage")
    )
    overall_grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Overall Grade")
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Grade Point")
    )
    
    # Status and ranking
    result_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PASS",
        verbose_name=_("Result Status")
    )
    rank = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Class Rank"))
    total_students = models.PositiveIntegerField(default=0, verbose_name=_("Total Students"))
    
    # Additional information
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Attendance Percentage")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Published At"))

    class Meta:
        db_table = "exams_exam_result"
        ordering = ["exam", "rank", "student"]
        verbose_name = _("Exam Result")
        verbose_name_plural = _("Exam Results")
        unique_together = [['exam', 'student']]
        indexes = [
            models.Index(fields=['exam', 'student']),
            models.Index(fields=['student', 'exam']),
            models.Index(fields=['result_status', 'is_published']),
            models.Index(fields=['rank']),
        ]

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.percentage}%"

    @property
    def is_pass(self):
        """Check if result is passing"""
        return self.result_status == "PASS"

    @property
    def percentage_display(self):
        """Formatted percentage for display"""
        return f"{self.percentage}%" if self.percentage else "N/A"

    def calculate_percentage(self):
        """Calculate percentage if marks are available"""
        if self.total_marks_obtained and self.total_max_marks and self.total_max_marks > 0:
            return (self.total_marks_obtained / self.total_max_marks) * 100
        return None

    def determine_grade(self):
        """Determine grade based on percentage"""
        if not self.percentage:
            return None
            
        grading_system = GradingSystem.objects.filter(is_default=True).first()
        if not grading_system:
            return None
            
        grade = Grade.objects.filter(
            grading_system=grading_system,
            min_percentage__lte=self.percentage,
            max_percentage__gte=self.percentage
        ).first()
        
        return grade

    def update_rank(self):
        """Update rank based on percentage"""
        if not self.percentage:
            return
            
        # Get all results for this exam ordered by percentage descending
        results = ExamResult.objects.filter(
            exam=self.exam,
            percentage__isnull=False
        ).order_by('-percentage', 'student__roll_number')
        
        current_rank = 0
        last_percentage = None
        rank_increment = 0
        
        for result in results:
            rank_increment += 1
            if result.percentage != last_percentage:
                current_rank = rank_increment
                last_percentage = result.percentage
                
            result.rank = current_rank
            result.total_students = results.count()
            result.save(update_fields=['rank', 'total_students'])

    def clean(self):
        """Validate result data"""
        if self.total_marks_obtained and self.total_max_marks:
            if self.total_marks_obtained > self.total_max_marks:
                raise ValidationError({
                    'total_marks_obtained': _('Obtained marks cannot exceed maximum marks')
                })

    def save(self, *args, **kwargs):
        """Enhanced save with automatic calculations"""
        # Calculate percentage
        if self.total_marks_obtained and self.total_max_marks:
            self.percentage = self.calculate_percentage()
        
        # Determine grade
        if self.percentage is not None:
            grade = self.determine_grade()
            if grade:
                self.overall_grade = grade
                self.grade_point = grade.grade_point
        
        # Set result status
        if self.percentage is not None:
            if self.percentage >= self.exam.pass_percentage:
                self.result_status = "PASS"
            else:
                self.result_status = "FAIL"
        
        # Set published timestamp
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Update rank after save
        if self.percentage is not None:
            self.update_rank()


class SubjectResult(BaseModel):
    """
    Detailed subject-wise results
    """
    exam_result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name="subject_results",
        verbose_name=_("Exam Result")
    )
    exam_subject = models.ForeignKey(
        ExamSubject,
        on_delete=models.CASCADE,
        related_name="subject_results",
        verbose_name=_("Exam Subject")
    )
    
    # Marks obtained
    theory_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Theory Marks")
    )
    practical_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Practical Marks")
    )
    total_marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total Marks Obtained")
    )
    
    # Grading
    grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Grade")
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Grade Point")
    )
    
    # Status
    is_pass = models.BooleanField(default=True, verbose_name=_("Is Pass"))
    attendance = models.CharField(
        max_length=10,
        choices=(
            ("PRESENT", _("Present")),
            ("ABSENT", _("Absent")),
            ("LEAVE", _("On Leave")),
        ),
        default="PRESENT",
        verbose_name=_("Attendance Status")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))

    class Meta:
        db_table = "exams_subject_result"
        ordering = ["exam_subject__subject__name"]
        verbose_name = _("Subject Result")
        verbose_name_plural = _("Subject Results")
        unique_together = [['exam_result', 'exam_subject']]
        indexes = [
            models.Index(fields=['exam_result', 'exam_subject']),
            models.Index(fields=['is_pass', 'attendance']),
        ]

    def __str__(self):
        return f"{self.exam_result.student} - {self.exam_subject.subject}"

    @property
    def percentage(self):
        """Calculate subject percentage"""
        if self.total_marks_obtained and self.exam_subject.max_marks:
            return (self.total_marks_obtained / self.exam_subject.max_marks) * 100
        return None

    def clean(self):
        """Validate subject result"""
        if self.theory_marks and self.practical_marks:
            if (self.theory_marks + self.practical_marks) != self.total_marks_obtained:
                raise ValidationError({
                    'total_marks_obtained': _('Theory + Practical marks must equal total marks')
                })
            
            if self.total_marks_obtained > self.exam_subject.max_marks:
                raise ValidationError({
                    'total_marks_obtained': _('Obtained marks cannot exceed maximum marks for subject')
                })

    def save(self, *args, **kwargs):
        """Enhanced save with automatic calculations"""
        # Calculate total marks
        if self.theory_marks is not None and self.practical_marks is not None:
            self.total_marks_obtained = self.theory_marks + self.practical_marks
        
        # Determine pass/fail
        if self.total_marks_obtained is not None:
            self.is_pass = self.total_marks_obtained >= self.exam_subject.pass_marks
        
        # Determine grade
        if self.percentage is not None:
            grade = self.determine_grade()
            if grade:
                self.grade = grade
                self.grade_point = grade.grade_point
        
        super().save(*args, **kwargs)

    def determine_grade(self):
        """Determine grade based on subject percentage"""
        grading_system = GradingSystem.objects.filter(is_default=True).first()
        if not grading_system:
            return None
            
        return Grade.objects.filter(
            grading_system=grading_system,
            min_percentage__lte=self.percentage,
            max_percentage__gte=self.percentage
        ).first()


class MarkSheet(BaseModel):
    """
    Digital mark sheet generation and management
    """
    exam_result = models.OneToOneField(
        ExamResult,
        on_delete=models.CASCADE,
        related_name="mark_sheet",
        verbose_name=_("Exam Result")
    )
    
    # Mark sheet details
    mark_sheet_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Mark Sheet Number")
    )
    issue_date = models.DateField(default=timezone.now, verbose_name=_("Issue Date"))
    is_issued = models.BooleanField(default=False, verbose_name=_("Is Issued"))
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Issued By")
    )
    
    # Digital document
    digital_copy = models.FileField(
        upload_to=exam_document_upload_path,
        null=True,
        blank=True,
        verbose_name=_("Digital Copy")
    )
    
    # Verification
    verification_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name=_("Verification Code")
    )
    qr_code = models.ImageField(
        upload_to=exam_document_upload_path,
        null=True,
        blank=True,
        verbose_name=_("QR Code")
    )
    
    # Status
    is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Verified At"))
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_mark_sheets",
        verbose_name=_("Verified By")
    )

    class Meta:
        db_table = "exams_mark_sheet"
        ordering = ["-issue_date", "mark_sheet_number"]
        verbose_name = _("Mark Sheet")
        verbose_name_plural = _("Mark Sheets")
        indexes = [
            models.Index(fields=['mark_sheet_number']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['is_issued', 'is_verified']),
        ]

    def __str__(self):
        return f"Mark Sheet - {self.mark_sheet_number}"

    def generate_verification_code(self):
        """Generate unique verification code"""
        if not self.verification_code:
            self.verification_code = f"MS{uuid.uuid4().hex[:8].upper()}"
        return self.verification_code

    def save(self, *args, **kwargs):
        """Enhanced save with code generation"""
        if not self.mark_sheet_number:
            self.mark_sheet_number = self.generate_mark_sheet_number()
            
        if not self.verification_code:
            self.generate_verification_code()
            
        super().save(*args, **kwargs)

    def generate_mark_sheet_number(self):
        """Generate unique mark sheet number"""
        prefix = f"MS-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_sheet = MarkSheet.objects.filter(
            mark_sheet_number__startswith=prefix,
            tenant=self.tenant
        ).order_by('mark_sheet_number').last()
        
        if last_sheet:
            last_number = int(last_sheet.mark_sheet_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}{new_number:06d}"

    def verify_mark_sheet(self, user):
        """Verify mark sheet"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verified_by = user
        self.save()


class CompartmentExam(BaseModel):
    """
    Management of compartment/improvement exams
    """
    original_result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name="compartment_exams",
        verbose_name=_("Original Result")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name=_("Subject")
    )
    
    # Exam details
    exam_date = models.DateField(verbose_name=_("Exam Date"))
    max_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Maximum Marks")
    )
    pass_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Passing Marks")
    )
    
    # Result
    marks_obtained = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Marks Obtained")
    )
    is_pass = models.BooleanField(default=False, verbose_name=_("Is Pass"))
    improved_grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Improved Grade")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=(
            ("SCHEDULED", _("Scheduled")),
            ("APPEARED", _("Appeared")),
            ("PASS", _("Pass")),
            ("FAIL", _("Fail")),
            ("ABSENT", _("Absent")),
        ),
        default="SCHEDULED",
        verbose_name=_("Status")
    )
    fee_paid = models.BooleanField(default=False, verbose_name=_("Fee Paid"))
    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fee Amount")
    )

    class Meta:
        db_table = "exams_compartment_exam"
        ordering = ["exam_date", "original_result__student"]
        verbose_name = _("Compartment Exam")
        verbose_name_plural = _("Compartment Exams")
        unique_together = [['original_result', 'subject']]
        indexes = [
            models.Index(fields=['original_result', 'status']),
            models.Index(fields=['exam_date', 'is_pass']),
        ]

    def __str__(self):
        return f"Compartment - {self.original_result.student} - {self.subject}"

    def update_original_result(self):
        """Update original result if compartment exam is passed"""
        if self.is_pass and self.marks_obtained:
            # Update the subject result in original exam
            subject_result = SubjectResult.objects.filter(
                exam_result=self.original_result,
                exam_subject__subject=self.subject
            ).first()
            
            if subject_result:
                subject_result.total_marks_obtained = self.marks_obtained
                subject_result.is_pass = True
                subject_result.save()
                
                # Recalculate overall result
                self.original_result.save()


class ResultStatistics(BaseModel):
    """
    Comprehensive result statistics and analytics
    """
    exam = models.OneToOneField(
        Exam,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name=_("Exam")
    )
    
    # Basic statistics
    total_students = models.PositiveIntegerField(default=0, verbose_name=_("Total Students"))
    appeared_students = models.PositiveIntegerField(default=0, verbose_name=_("Appeared Students"))
    passed_students = models.PositiveIntegerField(default=0, verbose_name=_("Passed Students"))
    failed_students = models.PositiveIntegerField(default=0, verbose_name=_("Failed Students"))
    
    # Percentage calculations
    pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Pass Percentage")
    )
    distinction_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Distinction Percentage")
    )
    first_class_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("First Class Percentage")
    )
    
    # Grade distribution
    grade_distribution = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("Grade Distribution")
    )
    
    # Subject-wise performance
    subject_performance = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("Subject Performance")
    )
    
    # Additional metrics
    average_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Average Percentage")
    )
    highest_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Highest Percentage")
    )
    lowest_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Lowest Percentage")
    )
    
    # Calculation timestamp
    calculated_at = models.DateTimeField(auto_now=True, verbose_name=_("Calculated At"))

    class Meta:
        db_table = "exams_result_statistics"
        verbose_name = _("Result Statistics")
        verbose_name_plural = _("Result Statistics")

    def __str__(self):
        return f"Statistics - {self.exam.name}"

    def calculate_statistics(self):
        """Calculate comprehensive result statistics"""
        results = ExamResult.objects.filter(exam=self.exam)
        
        self.total_students = results.count()
        self.appeared_students = results.exclude(result_status="ABSENT").count()
        self.passed_students = results.filter(result_status="PASS").count()
        self.failed_students = results.filter(result_status="FAIL").count()
        
        # Calculate percentages
        if self.appeared_students > 0:
            self.pass_percentage = (self.passed_students / self.appeared_students) * 100
        
        # Calculate average, highest, lowest percentages
        valid_results = results.filter(percentage__isnull=False)
        if valid_results.exists():
            self.average_percentage = valid_results.aggregate(
                avg=models.Avg('percentage')
            )['avg'] or 0
            
            self.highest_percentage = valid_results.aggregate(
                max=models.Max('percentage')
            )['max'] or 0
            
            self.lowest_percentage = valid_results.aggregate(
                min=models.Min('percentage')
            )['min'] or 0
        
        self.save()

    def get_performance_summary(self):
        """Get performance summary for reporting"""
        return {
            'total_students': self.total_students,
            'appeared_students': self.appeared_students,
            'passed_students': self.passed_students,
            'pass_percentage': float(self.pass_percentage),
            'average_percentage': float(self.average_percentage),
            'highest_percentage': float(self.highest_percentage),
            'lowest_percentage': float(self.lowest_percentage)
        }