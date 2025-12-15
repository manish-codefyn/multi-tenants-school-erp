import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class AcademicYear(BaseModel):
    """
    School Academic Year Management
    """
    name = models.CharField(max_length=100, verbose_name=_("Academic Year"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Year Code"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    is_current = models.BooleanField(default=False, verbose_name=_("Is Current Year"))
    
    # School Terms
    has_terms = models.BooleanField(default=True, verbose_name=_("Has Terms"))
    
    class Meta:
        db_table = "academics_academic_year"
        verbose_name = _("Academic Year")
        verbose_name_plural = _("Academic Years")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('academics:academic_year_detail', args=[str(self.id)])



class Term(BaseModel):
    """
    School Terms (Semesters/Quarters)
    """
    TERM_CHOICES = (
        ("FIRST_TERM", _("First Term")),
        ("SECOND_TERM", _("Second Term")),
        ("THIRD_TERM", _("Third Term")),
        ("FOURTH_TERM", _("Fourth Term")),
        ("ANNUAL", _("Annual")),
    )

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
        verbose_name=_("Academic Year")
    )
    name = models.CharField(max_length=100, verbose_name=_("Term Name"))
    term_type = models.CharField(
        max_length=20,
        choices=TERM_CHOICES,
        verbose_name=_("Term Type")
    )
    order = models.PositiveIntegerField(verbose_name=_("Order"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    is_current = models.BooleanField(default=False, verbose_name=_("Is Current Term"))

    class Meta:
        db_table = "academics_terms"
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")
        unique_together = [['academic_year', 'term_type']]
        ordering = ["academic_year", "order"]

    def __str__(self):
        return f"{self.name} - {self.academic_year}"

    @property
    def is_currently_running(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class SchoolClass(BaseModel):
    """
    School Classes/Grades (Nursery to 12th)
    """
    CLASS_LEVEL_CHOICES = (
        ("PRE_PRIMARY", _("Pre-Primary")),
        ("PRIMARY", _("Primary")),
        ("MIDDLE", _("Middle School")),
        ("HIGH", _("High School")),
        ("SENIOR", _("Senior Secondary")),
    )

    name = models.CharField(max_length=100, verbose_name=_("Class Name"))
    numeric_name = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name=_("Class Number")
    )
    code = models.CharField(max_length=10, unique=True, verbose_name=_("Class Code"))
    level = models.CharField(
        max_length=20,
        choices=CLASS_LEVEL_CHOICES,
        verbose_name=_("Class Level")
    )
    order = models.PositiveIntegerField(verbose_name=_("Display Order"))
    
    # Academic Configuration
    pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=33.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Pass Percentage")
    )
    max_strength = models.PositiveIntegerField(
        default=40,
        verbose_name=_("Maximum Strength")
    )
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tuition Fee")
    )
    
    # Class Teacher
    class_teacher = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_teacher_of",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Class Teacher")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "academics_classes"
        verbose_name = _("Class")
        verbose_name_plural = _("Classes")
        ordering = ["order"]
        indexes = [
            models.Index(fields=['level', 'is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def current_strength(self):
        return self.students.filter(is_active=True).count()

    @property
    def available_seats(self):
        return self.max_strength - self.current_strength

    @property
    def can_admit_more(self):
        return self.available_seats > 0

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('academics:class_detail', args=[str(self.id)])


class Section(BaseModel):
    """
    Class Sections (A, B, C, etc.)
    """
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Class")
    )
    name = models.CharField(max_length=10, verbose_name=_("Section Name"))
    code = models.CharField(max_length=10, verbose_name=_("Section Code"))
    
    # Capacity
    max_strength = models.PositiveIntegerField(
        default=40,
        verbose_name=_("Maximum Strength")
    )
    
    # Section Incharge
    section_incharge = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_incharge_of",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Section Incharge")
    )
    
    # Room
    room_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Room Number")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "academics_sections"
        verbose_name = _("Section")
        verbose_name_plural = _("Sections")
        unique_together = [['class_name', 'name']]
        ordering = ["class_name__order", "name"]
        indexes = [
            models.Index(fields=['class_name', 'is_active']),
        ]

    def __str__(self):
        return f"{self.class_name.name} - {self.name}"

    @property
    def current_strength(self):
        return self.students.filter(is_active=True).count()

    @property
    def available_seats(self):
        return self.max_strength - self.current_strength


class House(BaseModel):
    """
    School Houses for competitions and activities
    """
    name = models.CharField(max_length=100, verbose_name=_("House Name"))
    code = models.CharField(max_length=10, unique=True, verbose_name=_("House Code"))
    color = models.CharField(max_length=20, verbose_name=_("House Color"))
    motto = models.CharField(max_length=200, blank=True, verbose_name=_("House Motto"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # House Master/Mistress
    house_master = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="house_master_of",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("House Master/Mistress")
    )
    
    # Points
    total_points = models.PositiveIntegerField(default=0, verbose_name=_("Total Points"))
    
    # Logo
    logo = models.ImageField(
        upload_to='houses/logos/',
        null=True,
        blank=True,
        verbose_name=_("House Logo")
    )

    class Meta:
        db_table = "academics_houses"
        verbose_name = _("House")
        verbose_name_plural = _("Houses")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def add_points(self, points, activity):
        """Add points to house"""
        self.total_points += points
        self.save()
        
        # Create points record
        HousePoints.objects.create(
            house=self,
            points=points,
            activity=activity,
            awarded_by=self.house_master
        )


class HousePoints(BaseModel):
    """
    House points tracking
    """
    house = models.ForeignKey(
        House,
        on_delete=models.CASCADE,
        related_name="points_records",
        verbose_name=_("House")
    )
    points = models.IntegerField(verbose_name=_("Points"))
    activity = models.CharField(max_length=200, verbose_name=_("Activity"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    date_awarded = models.DateField(default=timezone.now, verbose_name=_("Date Awarded"))
    awarded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="awarded_points",
        verbose_name=_("Awarded By")
    )

    class Meta:
        db_table = "academics_house_points"
        verbose_name = _("House Points")
        verbose_name_plural = _("House Points")
        ordering = ["-date_awarded"]

    def __str__(self):
        return f"{self.house.name} - {self.points} points"


class Subject(BaseModel):
    """
    School Subjects
    """
    SUBJECT_TYPE_CHOICES = (
        ("CORE", _("Core Subject")),
        ("ELECTIVE", _("Elective Subject")),
        ("LANGUAGE", _("Language")),
        ("CO_CURRICULAR", _("Co-curricular")),
        ("EXTRA_CURRICULAR", _("Extra-curricular")),
    )

    SUBJECT_GROUP_CHOICES = (
        ("SCIENCE", _("Science")),
        ("COMMERCE", _("Commerce")),
        ("ARTS", _("Arts")),
        ("VOCATIONAL", _("Vocational")),
        ("GENERAL", _("General")),
    )

    name = models.CharField(max_length=100, verbose_name=_("Subject Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Subject Code"))
    subject_type = models.CharField(
        max_length=20,
        choices=SUBJECT_TYPE_CHOICES,
        default="CORE",
        verbose_name=_("Subject Type")
    )
    subject_group = models.CharField(
        max_length=20,
        choices=SUBJECT_GROUP_CHOICES,
        blank=True,
        verbose_name=_("Subject Group")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Configuration
    has_practical = models.BooleanField(default=False, verbose_name=_("Has Practical"))
    has_project = models.BooleanField(default=False, verbose_name=_("Has Project Work"))
    is_scoring = models.BooleanField(default=True, verbose_name=_("Is Scoring Subject"))
    
    # Credits/Grading
    credit_hours = models.PositiveIntegerField(default=1, verbose_name=_("Credit Hours"))
    max_marks = models.PositiveIntegerField(default=100, verbose_name=_("Maximum Marks"))
    pass_marks = models.PositiveIntegerField(default=33, verbose_name=_("Pass Marks"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "academics_subjects"
        verbose_name = _("Subject")
        verbose_name_plural = _("Subjects")
        ordering = ["name"]
        indexes = [
            models.Index(fields=['subject_type', 'is_active']),
        ]

    def __str__(self):
        return self.name


class ClassSubject(BaseModel):
    """
    Subjects taught in specific classes
    """
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="class_subjects",
        verbose_name=_("Class")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="class_subjects",
        verbose_name=_("Subject")
    )
    is_compulsory = models.BooleanField(default=True, verbose_name=_("Is Compulsory"))
    periods_per_week = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Periods Per Week")
    )
    
    # Teacher Assignment
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_subjects",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Subject Teacher")
    )
    
    # Academic Year
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="class_subjects",
        verbose_name=_("Academic Year")
    )

    class Meta:
        db_table = "academics_class_subjects"
        verbose_name = _("Class Subject")
        verbose_name_plural = _("Class Subjects")
        unique_together = [['class_name', 'subject', 'academic_year']]
        ordering = ["class_name", "subject"]

    def __str__(self):
        return f"{self.class_name} - {self.subject}"

class TimeTable(BaseModel):
    """
    School Time Table
    """
    DAY_CHOICES = (
        ("MONDAY", _("Monday")),
        ("TUESDAY", _("Tuesday")),
        ("WEDNESDAY", _("Wednesday")),
        ("THURSDAY", _("Thursday")),
        ("FRIDAY", _("Friday")),
        ("SATURDAY", _("Saturday")),
    )

    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("Class")
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("Section")
    )
    # ADD THIS FIELD
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("Academic Year")
    )

    day = models.CharField(max_length=10, choices=DAY_CHOICES, verbose_name=_("Day"))
    period_number = models.PositiveIntegerField(verbose_name=_("Period Number"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    
    # Subject and Teacher
    subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
        verbose_name=_("Subject")
    )
    teacher = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timetable_periods",
        verbose_name=_("Teacher")
    )
    
    # Room
    room = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Room/Lab")
    )
    
    # Period Type
    period_type = models.CharField(
        max_length=20,
        choices=(
            ("LECTURE", _("Lecture")),
            ("PRACTICAL", _("Practical")),
            ("TUTORIAL", _("Tutorial")),
            ("BREAK", _("Break")),
            ("ASSEMBLY", _("Assembly")),
            ("GAMES", _("Games")),
        ),
        default="LECTURE",
        verbose_name=_("Period Type")
    )

    class Meta:
        db_table = "academics_timetable"
        verbose_name = _("Time Table")
        verbose_name_plural = _("Time Tables")
        unique_together = [['class_name', 'section', 'day', 'period_number', 'academic_year']]
        ordering = ["day", "period_number"]

    def __str__(self):
        return f"{self.class_name} {self.section} - {self.day} Period {self.period_number}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(_("End time must be after start time"))


class StudentAttendance(BaseModel):
    """
    Student Attendance Management
    """
    ATTENDANCE_STATUS = (
        ("PRESENT", _("Present")),
        ("ABSENT", _("Absent")),
        ("LATE", _("Late")),
        ("HALF_DAY", _("Half Day")),
        ("HOLIDAY", _("Holiday")),
        ("LEAVE", _("On Leave")),
    )
    SESSION_CHOICES = (
        ("MORNING", _("Morning")),
        ("AFTERNOON", _("Afternoon")),
        ("FULL_DAY", _("Full Day")),
    )
    session = models.CharField(
    max_length=10,
    choices=SESSION_CHOICES,
    default="FULL_DAY",
    verbose_name=_("Session")
)
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Student")
    )
    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS,
        default="PRESENT",
        verbose_name=_("Status")
    )
    
    # Class Information
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Class")
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Section")
    )
    
    # Session (Morning/Afternoon)
    session = models.CharField(
        max_length=10,
        choices=(
            ("MORNING", _("Morning")),
            ("AFTERNOON", _("Afternoon")),
            ("FULL_DAY", _("Full Day")),
        ),
        default="FULL_DAY",
        verbose_name=_("Session")
    )
    
    # Remarks
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="academics_attendance_marked",
        verbose_name=_("Marked By")
    )

    class Meta:
        db_table = "academics_attendance"
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        unique_together = [['student', 'date', 'session']]
        ordering = ["-date", "student"]
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['class_name', 'date']),
            models.Index(fields=['status', 'date']),
        ]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"

    @property
    def is_present(self):
        return self.status in ["PRESENT", "LATE", "HALF_DAY"]


class Holiday(BaseModel):
    """
    School Holidays and Events
    """
    HOLIDAY_TYPE_CHOICES = (
        ("NATIONAL", _("National Holiday")),
        ("RELIGIOUS", _("Religious Holiday")),
        ("SCHOOL", _("School Holiday")),
        ("EXAM", _("Examination Holiday")),
        ("EVENT", _("School Event")),
        ("OTHER", _("Other")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Holiday Name"))
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPE_CHOICES,
        verbose_name=_("Holiday Type")
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Academic Year
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="holidays",
        verbose_name=_("Academic Year")
    )
    
    # Affected Classes (empty means all classes)
    affected_classes = models.ManyToManyField(
        SchoolClass,
        blank=True,
        related_name="holidays",
        verbose_name=_("Affected Classes")
    )

    class Meta:
        db_table = "academics_holidays"
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def is_date_in_holiday(self, date):
        return self.start_date <= date <= self.end_date


class StudyMaterial(BaseModel):
    """
    Study materials, notes, and resources
    """
    MATERIAL_TYPE_CHOICES = (
        ("NOTE", _("Notes")),
        ("PRESENTATION", _("Presentation")),
        ("WORKSHEET", _("Worksheet")),
        ("ASSIGNMENT", _("Assignment")),
        ("REFERENCE", _("Reference Material")),
        ("VIDEO", _("Video")),
        ("AUDIO", _("Audio")),
        ("OTHER", _("Other")),
    )

    title = models.CharField(max_length=200, verbose_name=_("Title"))
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPE_CHOICES,
        verbose_name=_("Material Type")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Class and Subject
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="study_materials",
        verbose_name=_("Class")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="study_materials",
        verbose_name=_("Subject")
    )
    
    # File
    file = models.FileField(
        upload_to='study_materials/',
        verbose_name=_("File")
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name=_("File Size"))
    
    # Teacher
    uploaded_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="uploaded_materials",
        verbose_name=_("Uploaded By")
    )
    
    # Visibility
    is_published = models.BooleanField(default=True, verbose_name=_("Is Published"))
    publish_date = models.DateTimeField(default=timezone.now, verbose_name=_("Publish Date"))

    class Meta:
        db_table = "academics_study_materials"
        verbose_name = _("Study Material")
        verbose_name_plural = _("Study Materials")
        ordering = ["-publish_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class Syllabus(BaseModel):
    """
    Class-wise syllabus and curriculum
    """
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="syllabus",
        verbose_name=_("Class")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="syllabus",
        verbose_name=_("Subject")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="syllabus",
        verbose_name=_("Academic Year")
    )
    
    # Syllabus Content
    topics = models.JSONField(
        default=list,
        verbose_name=_("Topics"),
        help_text=_("List of topics and subtopics in JSON format")
    )
    
    # Books and References
    recommended_books = models.TextField(blank=True, verbose_name=_("Recommended Books"))
    reference_materials = models.TextField(blank=True, verbose_name=_("Reference Materials"))
    
    # Assessment Pattern
    assessment_pattern = models.JSONField(
        default=dict,
        verbose_name=_("Assessment Pattern"),
        help_text=_("Marks distribution and exam pattern")
    )

    class Meta:
        db_table = "academics_syllabus"
        verbose_name = _("Syllabus")
        verbose_name_plural = _("Syllabus")
        unique_together = [['class_name', 'subject', 'academic_year']]
        ordering = ["class_name", "subject"]

    def __str__(self):
        return f"{self.class_name} - {self.subject} - {self.academic_year}"

class Stream(BaseModel):
    """
    Academic Streams (Science, Commerce, Arts, etc.)
    """
    name = models.CharField(max_length=100, verbose_name=_("Stream Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Stream Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Stream Configuration
    # Stream Configuration
    available_from_class = models.ForeignKey(
        'SchoolClass',
        on_delete=models.CASCADE,
        related_name="available_streams",
        verbose_name=_("Available From Class"),
        help_text=_("Class from which this stream becomes available")
    )

    subjects = models.ManyToManyField(
        'Subject',
        related_name="streams",
        verbose_name=_("Core Subjects"),
        blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "academics_streams"
        verbose_name = _("Stream")
        verbose_name_plural = _("Streams")
        ordering = ["name"]

    def __str__(self):
        return self.name

        
class ClassTeacher(BaseModel):
    """
    Class Teacher assignments
    """
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="class_teachers",
        verbose_name=_("Class")
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="class_teachers",
        verbose_name=_("Section")
    )
    teacher = models.ForeignKey(
       settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="class_teacher_assignments",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Class Teacher")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="class_teachers",
        verbose_name=_("Academic Year")
    )
    start_date = models.DateField(default=timezone.now, verbose_name=_("Start Date"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("End Date"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "academics_class_teachers"
        verbose_name = _("Class Teacher")
        verbose_name_plural = _("Class Teachers")
        unique_together = [['class_name', 'section', 'academic_year']]
        ordering = ["class_name", "section"]

    def __str__(self):
        return f"{self.class_name} {self.section} - {self.teacher}"

    @property
    def student_count(self):
        return self.section.students.filter(is_active=True).count()


class GradingSystem(BaseModel):
    """
    Configurable grading system for the institution
    """
    name = models.CharField(max_length=100, verbose_name=_("Grading System Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("System Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_default = models.BooleanField(default=False, verbose_name=_("Is Default System"))

    class Meta:
        db_table = "academics_grading_system"
        ordering = ["name"]
        verbose_name = _("Grading System")
        verbose_name_plural = _("Grading Systems")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Ensure only one default grading system"""
        if self.is_default:
            GradingSystem.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Grade(BaseModel):
    """
    Individual grades within a grading system
    """
    grading_system = models.ForeignKey(
        GradingSystem,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Grading System")
    )
    grade = models.CharField(max_length=5, verbose_name=_("Grade"))
    description = models.CharField(max_length=100, verbose_name=_("Description"))
    min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Minimum Percentage")
    )
    max_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Maximum Percentage")
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Grade Point")
    )
    remarks = models.CharField(max_length=200, blank=True, verbose_name=_("Remarks"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        db_table = "academics_grade"
        ordering = ["grading_system", "order", "min_percentage"]
        verbose_name = _("Grade")
        verbose_name_plural = _("Grades")
        unique_together = [['grading_system', 'grade']]
        indexes = [
            models.Index(fields=['grading_system', 'min_percentage', 'max_percentage']),
        ]

    def __str__(self):
        return f"{self.grade} ({self.min_percentage}-{self.max_percentage}%) - {self.grade_point}"

    def clean(self):
        """Validate grade ranges"""
        if self.min_percentage >= self.max_percentage:
            raise ValidationError({
                'min_percentage': _('Minimum percentage must be less than maximum percentage')
            })
        
        # Check for overlapping grades
        # Note: We filter by grading_system but exclude self if it exists
        overlapping_grades = Grade.objects.filter(
            grading_system=self.grading_system,
            min_percentage__lt=self.max_percentage,
            max_percentage__gt=self.min_percentage
        )
        
        if self.pk:
            overlapping_grades = overlapping_grades.exclude(id=self.pk)
        
        if overlapping_grades.exists():
            raise ValidationError(_('Grade percentage ranges cannot overlap'))




