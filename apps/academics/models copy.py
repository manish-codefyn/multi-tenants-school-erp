from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class Department(BaseModel):
    """
    Academic department model with comprehensive validation and management
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("Department Name"),
        help_text=_("Official name of the academic department")
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Department Code"),
        help_text=_("Unique code identifier for the department (e.g., CS, MATH)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description of the department's focus and offerings")
    )
    head_of_department = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Head of Department"),
        help_text=_("Faculty member leading this department")
    )
    established_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Established Date"),
        help_text=_("Date when the department was established")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Active Status"),
        help_text=_("Whether the department is currently active")
    )

    class Meta:
        db_table = 'academics_departments'
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        indexes = [
            models.Index(fields=['is_active', 'code']),
            models.Index(fields=['name', 'is_active']),
        ]
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate department data"""
        super().clean()
        
        if self.code:
            self.code = self.code.upper().strip()
            
        if self.head_of_department and self.head_of_department.role != 'teacher':
            raise ValidationError({
                'head_of_department': _("Head of department must be a teacher.")
            })

    @property
    def course_count(self):
        """Get number of active courses in this department"""
        return self.courses.filter(is_active=True).count()

    @property
    def active_teacher_count(self):
        """Get number of active teachers in this department"""
        return self.courses.filter(
            is_active=True,
            instructor__is_active=True
        ).values('instructor').distinct().count()

    def can_be_deleted(self):
        """Check if department can be safely deleted"""
        return self.course_count == 0


class CourseManager(models.Manager):
    """Custom manager for Course model with common queries"""
    
    def active_courses(self):
        """Return active courses"""
        return self.filter(is_active=True)
    
    def enrollment_open_courses(self):
        """Return courses that are open for enrollment"""
        return self.filter(
            is_active=True,
            enrollment_open=True,
            start_date__gt=timezone.now().date()
        )
    
    def by_department(self, department_code):
        """Return courses by department code"""
        return self.filter(
            department__code=department_code,
            is_active=True
        )
    
    def with_available_seats(self):
        """Return courses that have available seats"""
        from django.db.models import Count, Q
        return self.annotate(
            current_enrollments=Count(
                'enrollments',
                filter=Q(enrollments__status='active')
            )
        ).filter(
            current_enrollments__lt=models.F('max_students'),
            is_active=True,
            enrollment_open=True
        )


class Course(BaseModel):
    """
    Course model with multi-tenant support and comprehensive business logic
    """
    COURSE_LEVELS = [
        ('introductory', _('Introductory')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('graduate', _('Graduate')),
    ]

    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("Course Name"),
        help_text=_("Official name of the course")
    )
    code = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name=_("Course Code"),
        help_text=_("Unique course code identifier")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Course Description"),
        help_text=_("Detailed description of course content and objectives")
    )
    syllabus = models.TextField(
        blank=True,
        verbose_name=_("Course Syllabus"),
        help_text=_("Detailed course syllabus and schedule")
    )
    credits = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Credit Hours"),
        help_text=_("Number of credit hours for this course")
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_("Department"),
        help_text=_("Academic department offering this course")
    )
    
    instructor = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_courses',
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Instructor"),
        help_text=_("Primary instructor for this course")
    )
    
    start_date = models.DateField(
        verbose_name=_("Start Date"),
        help_text=_("Course start date")
    )
    end_date = models.DateField(
        verbose_name=_("End Date"),
        help_text=_("Course end date")
    )
    
    level = models.CharField(
        max_length=20,
        choices=COURSE_LEVELS,
        default='introductory',
        verbose_name=_("Course Level"),
        help_text=_("Academic level of the course")
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("Active Status"),
        help_text=_("Whether the course is currently active")
    )
    
    # Course settings
    max_students = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        verbose_name=_("Maximum Students"),
        help_text=_("Maximum number of students allowed to enroll")
    )
    
    enrollment_open = models.BooleanField(
        default=True,
        verbose_name=_("Enrollment Open"),
        help_text=_("Whether the course is open for new enrollments")
    )
    
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        verbose_name=_("Prerequisites"),
        help_text=_("Courses that must be completed before taking this course")
    )
    
    # Manager
    objects = CourseManager()

    class Meta:
        db_table = 'academics_courses'
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        unique_together = ['code', 'tenant']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['level', 'is_active']),
        ]
        ordering = ['code', 'start_date']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        """Validate course data"""
        super().clean()
        
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': _("End date must be after start date.")
                })
        
        if self.code:
            self.code = self.code.upper().strip()
            
        if self.instructor and self.instructor.role != 'teacher':
            raise ValidationError({
                'instructor': _("Instructor must be a teacher.")
            })

    def save(self, *args, **kwargs):
        """Custom save method with validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def current_student_count(self):
        """Get current enrolled student count"""
        return self.enrollments.filter(status='active').count()

    @property
    def available_seats(self):
        """Calculate available seats"""
        return max(0, self.max_students - self.current_student_count)

    @property
    def can_enroll(self):
        """Check if course can accept more students"""
        return (
            self.enrollment_open and 
            self.is_active and
            self.start_date > timezone.now().date() and
            self.available_seats > 0
        )

    @property
    def duration_days(self):
        """Calculate course duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    @property
    def is_ongoing(self):
        """Check if course is currently ongoing"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def get_prerequisite_codes(self):
        """Get list of prerequisite course codes"""
        return list(self.prerequisites.values_list('code', flat=True))

    def check_prerequisites(self, student):
        """
        Check if student has completed all prerequisites
        Returns: (bool, list_of_missing_prerequisites)
        """
        if not self.prerequisites.exists():
            return True, []

        completed_courses = Enrollment.objects.filter(
            student=student,
            status='completed',
            grade__in=['A', 'B', 'C', 'D']  # Passing grades
        ).values_list('course_id', flat=True)

        missing_prerequisites = self.prerequisites.exclude(
            id__in=completed_courses
        ).values_list('code', flat=True)

        return len(missing_prerequisites) == 0, list(missing_prerequisites)


class EnrollmentManager(models.Manager):
    """Custom manager for Enrollment model"""
    
    def active_enrollments(self):
        """Return active enrollments"""
        return self.filter(status='active')
    
    def completed_enrollments(self):
        """Return completed enrollments"""
        return self.filter(status='completed')
    
    def by_student(self, student_id):
        """Return enrollments for a specific student"""
        return self.filter(student_id=student_id)
    
    def by_course(self, course_id):
        """Return enrollments for a specific course"""
        return self.filter(course_id=course_id)


class Enrollment(BaseModel):
    """
    Student course enrollment model with comprehensive tracking and grading
    """
    GRADE_CHOICES = [
        ('A', _('A (Excellent)')),
        ('A-', _('A- (Very Good)')),
        ('B+', _('B+ (Good)')),
        ('B', _('B (Satisfactory)')),
        ('B-', _('B- (Above Average)')),
        ('C+', _('C+ (Average)')),
        ('C', _('C (Below Average)')),
        ('C-', _('C- (Marginal)')),
        ('D', _('D (Poor)')),
        ('F', _('F (Fail)')),
        ('I', _('I (Incomplete)')),
        ('W', _('W (Withdrawn)')),
        ('IP', _('IP (In Progress)')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('withdrawn', _('Withdrawn')),
        ('failed', _('Failed')),
        ('transferred', _('Transferred')),
    ]

    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'},
        verbose_name=_("Student"),
        help_text=_("Student enrolled in the course")
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Course"),
        help_text=_("Course being enrolled in")
    )
    
    enrolled_on = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Enrollment Date"),
        help_text=_("Date and time when enrollment was created")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        verbose_name=_("Enrollment Status"),
        help_text=_("Current status of the enrollment")
    )
    
    grade = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        choices=GRADE_CHOICES,
        verbose_name=_("Final Grade"),
        help_text=_("Final grade awarded for the course")
    )
    
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Grade Points"),
        help_text=_("Numerical grade points for GPA calculation")
    )
    
    last_attendance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Last Attendance Date"),
        help_text=_("Date of last recorded attendance")
    )
    
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Completion Date"),
        help_text=_("Date when course was completed")
    )
    
    # Manager
    objects = EnrollmentManager()

    class Meta:
        db_table = 'academics_enrollments'
        verbose_name = _("Enrollment")
        verbose_name_plural = _("Enrollments")
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrolled_on']),
            models.Index(fields=['grade']),
        ]
        ordering = ['-enrolled_on']

    def __str__(self):
        return f"{self.student} - {self.course} ({self.status})"

    def clean(self):
        """Validate enrollment data"""
        super().clean()
        
        # Prevent duplicate active enrollments
        if self.status == 'active' and self.pk is None:
            existing_active = Enrollment.objects.filter(
                student=self.student,
                course=self.course,
                status='active'
            ).exists()
            if existing_active:
                raise ValidationError(
                    _("Student already has an active enrollment for this course.")
                )
        
        # Validate grade assignment
        if self.grade and self.status not in ['completed', 'failed']:
            raise ValidationError({
                'grade': _("Grade can only be assigned to completed or failed enrollments.")
            })

    def save(self, *args, **kwargs):
        """Custom save with automatic grade points calculation"""
        if self.grade:
            self.grade_points = self.calculate_grade_points()
            
        # Set completion date if status changed to completed
        if self.pk:
            old_status = Enrollment.objects.get(pk=self.pk).status
            if old_status != 'completed' and self.status == 'completed':
                self.completion_date = timezone.now().date()
        
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_grade_points(self):
        """Calculate grade points based on grade with precise mapping"""
        grade_points_map = {
            'A': 4.00, 'A-': 3.67,
            'B+': 3.33, 'B': 3.00, 'B-': 2.67,
            'C+': 2.33, 'C': 2.00, 'C-': 1.67,
            'D': 1.00, 'F': 0.00,
            'I': None, 'W': None, 'IP': None
        }
        return grade_points_map.get(self.grade)

    @property
    def is_passing_grade(self):
        """Check if the grade is a passing grade"""
        passing_grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D']
        return self.grade in passing_grades

    @property
    def enrollment_duration(self):
        """Calculate how long the student has been enrolled"""
        return (timezone.now() - self.enrolled_on).days

    def withdraw(self, withdrawal_date=None):
        """Withdraw student from course"""
        self.status = 'withdrawn'
        self.grade = 'W'
        self.grade_points = self.calculate_grade_points()
        if withdrawal_date:
            self.completion_date = withdrawal_date
        self.save()

    def complete_with_grade(self, grade, completion_date=None):
        """Complete enrollment with a grade"""
        if grade not in dict(self.GRADE_CHOICES):
            raise ValidationError(_("Invalid grade provided."))
            
        self.status = 'completed' if self.is_passing_grade else 'failed'
        self.grade = grade
        self.grade_points = self.calculate_grade_points()
        
        if completion_date:
            self.completion_date = completion_date
        else:
            self.completion_date = timezone.now().date()
            
        self.save()

    @classmethod
    def get_student_gpa(cls, student_id):
        """Calculate GPA for a student"""
        from django.db.models import Avg
        result = cls.objects.filter(
            student_id=student_id,
            grade_points__isnull=False,
            status='completed'
        ).aggregate(
            gpa=Avg('grade_points')
        )
        return result['gpa'] or 0.0

