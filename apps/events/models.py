import uuid
import os
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from encrypted_model_fields.fields import EncryptedCharField

# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel
from apps.academics.models import SchoolClass, Section, AcademicYear
from apps.students.models import Student

# Phone regex for validation
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
)

def event_image_upload_path(instance, filename):
    """Generate upload path for event images"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.title)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "event_images",
        str(instance.tenant.id),
        filename
    )

def event_document_upload_path(instance, filename):
    """Generate upload path for event documents"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.event.title)}_{slugify(instance.name)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "event_documents",
        str(instance.tenant.id),
        str(instance.event.id),
        filename
    )

class EventCategory(BaseModel):
    """
    Event categories for better organization and filtering
    """
    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Category Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name=_("Color Code"),
        help_text=_("Hex color code for calendar display")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icon"),
        help_text=_("Font awesome or material icon name")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))

    class Meta:
        db_table = "events_category"
        ordering = ["order", "name"]
        verbose_name = _("Event Category")
        verbose_name_plural = _("Event Categories")
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:category_events', kwargs={'pk': self.pk})


class Event(BaseModel):
    """
    Main event model for managing all types of institutional events
    """
    EVENT_TYPE_CHOICES = (
        ("ACADEMIC", _("Academic")),
        ("CULTURAL", _("Cultural")),
        ("SPORTS", _("Sports")),
        ("WORKSHOP", _("Workshop")),
        ("SEMINAR", _("Seminar")),
        ("CONFERENCE", _("Conference")),
        ("CELEBRATION", _("Celebration")),
        ("COMPETITION", _("Competition")),
        ("CAMPUS", _("Campus Event")),
        ("COMMUNITY", _("Community Service")),
        ("OTHER", _("Other")),
    )

    EVENT_SCOPE_CHOICES = (
        ("WHOLE_SCHOOL", _("Whole School")),
        ("JUNIOR_SCHOOL", _("Junior School")),
        ("SENIOR_SCHOOL", _("Senior School")),
        ("CLASS_SPECIFIC", _("Class Specific")),
        ("SECTION_SPECIFIC", _("Section Specific")),
        ("HOUSE_SPECIFIC", _("House Specific")),
        ("CLUB_SPECIFIC", _("Club Specific")),
        ("STAFF_ONLY", _("Staff Only")),
        ("PARENTS_ONLY", _("Parents Only")),
        ("INVITEES_ONLY", _("Invitees Only")),
    )

    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("SCHEDULED", _("Scheduled")),
        ("ONGOING", _("Ongoing")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
        ("POSTPONED", _("Postponed")),
    )

    PRIORITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("URGENT", _("Urgent")),
    )

    # Basic Information
    title = models.CharField(max_length=200, verbose_name=_("Event Title"))
    slug = models.SlugField(max_length=250, unique=True, verbose_name=_("URL Slug"))
    description = models.TextField(verbose_name=_("Event Description"))
    short_description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_("Short Description")
    )
    
    # Categorization
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name=_("Event Type")
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("Event Category")
    )
    
    # Scheduling
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    is_all_day = models.BooleanField(default=False, verbose_name=_("All Day Event"))
    
    # Location
    venue = models.CharField(max_length=200, verbose_name=_("Venue"))
    address = models.TextField(blank=True, verbose_name=_("Full Address"))
    google_maps_link = models.URLField(blank=True, verbose_name=_("Google Maps Link"))
    is_online = models.BooleanField(default=False, verbose_name=_("Is Online Event"))
    online_link = models.URLField(blank=True, verbose_name=_("Online Event Link"))
    
    # Scope and Audience
    event_scope = models.CharField(
        max_length=20,
        choices=EVENT_SCOPE_CHOICES,
        default="WHOLE_SCHOOL",
        verbose_name=_("Event Scope")
    )
    target_classes = models.ManyToManyField(
        SchoolClass,
        blank=True,
        related_name="events",
        verbose_name=_("Target Classes")
    )
    target_sections = models.ManyToManyField(
        Section,
        blank=True,
        related_name="events",
        verbose_name=_("Target Sections")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Academic Year")
    )
    
    # Status and Visibility
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Priority")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Published At"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Is Featured"))
    
    # Media
    featured_image = models.ImageField(
        upload_to=event_image_upload_path,
        null=True,
        blank=True,
        verbose_name=_("Featured Image")
    )
    
    # Capacity and Registration
    max_attendees = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Maximum Attendees")
    )
    requires_registration = models.BooleanField(
        default=False,
        verbose_name=_("Requires Registration")
    )
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Registration Deadline")
    )
    
    # Financial
    is_free = models.BooleanField(default=True, verbose_name=_("Is Free"))
    fee_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fee Amount")
    )
    fee_currency = models.CharField(
        max_length=3,
        default="INR",
        verbose_name=_("Fee Currency")
    )
    
    # Contact Information
    organizer_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Organizer Name")
    )
    organizer_email = models.EmailField(blank=True, verbose_name=_("Organizer Email"))
    organizer_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Organizer Phone")
    )
    
    # Additional Metadata
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for better searchability")
    )
    external_link = models.URLField(blank=True, verbose_name=_("External Link"))
    estimated_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Estimated Budget")
    )

    class Meta:
        db_table = "events_event"
        ordering = ["-start_date", "-created_at"]
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['is_published', 'is_featured']),
            models.Index(fields=['slug']),
            models.Index(fields=['academic_year', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_date})"

    def save(self, *args, **kwargs):
        """Enhanced save with slug generation and status management"""
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Event.objects.filter(slug=self.slug).exclude(id=self.id).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-update status based on dates
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        if self.status not in ["CANCELLED", "POSTPONED"]:
            if today < self.start_date:
                self.status = "SCHEDULED"
            elif today == self.start_date and current_time < self.start_time:
                self.status = "SCHEDULED"
            elif (self.start_date <= today <= self.end_date) and \
                 (today > self.start_date or current_time >= self.start_time) and \
                 (today < self.end_date or current_time <= self.end_time):
                self.status = "ONGOING"
            elif today > self.end_date or (today == self.end_date and current_time > self.end_time):
                self.status = "COMPLETED"
        
        # Set published timestamp
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
            
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'slug': self.slug})

    # ==================== PROPERTIES ====================
    @property
    def duration_days(self):
        """Calculate event duration in days"""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_current(self):
        """Check if event is currently occurring based on dates and time"""
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        return (self.start_date <= today <= self.end_date and
                (self.is_all_day or 
                 (today > self.start_date or current_time >= self.start_time) and
                 (today < self.end_date or current_time <= self.end_time)))

    @property
    def days_until_event(self):
        """Calculate days until event starts"""
        today = timezone.now().date()
        if today < self.start_date:
            return (self.start_date - today).days
        return 0

    @property
    def registration_count(self):
        """Get total registration count"""
        return self.registrations.filter(status="REGISTERED").count()

    @property
    def is_registration_open(self):
        """Check if registration is still open"""
        if not self.requires_registration:
            return False
            
        if self.registration_deadline:
            return timezone.now() <= self.registration_deadline
            
        return self.start_date >= timezone.now().date()

    @property
    def is_full(self):
        """Check if event is at full capacity"""
        if self.max_attendees:
            return self.registration_count >= self.max_attendees
        return False

    @property
    def available_slots(self):
        """Calculate available slots"""
        if self.max_attendees:
            return max(0, self.max_attendees - self.registration_count)
        return None

    @property
    def tag_list(self):
        """Get tags as list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    # ==================== METHODS ====================
    def clean(self):
        """Comprehensive event validation"""
        errors = {}
        
        # Date validation
        if self.start_date > self.end_date:
            errors['end_date'] = _('End date must be after start date')
        
        if self.start_date == self.end_date and self.start_time >= self.end_time:
            errors['end_time'] = _('End time must be after start time for single-day events')
        
        # Registration deadline validation
        if self.requires_registration and self.registration_deadline:
            event_start = timezone.datetime.combine(self.start_date, self.start_time)
            if self.registration_deadline > event_start:
                errors['registration_deadline'] = _('Registration deadline must be before event start time')
        
        # Online event validation
        if self.is_online and not self.online_link:
            errors['online_link'] = _('Online link is required for online events')
        
        # Capacity validation
        if self.max_attendees and self.max_attendees < 1:
            errors['max_attendees'] = _('Maximum attendees must be at least 1')
            
        if errors:
            raise ValidationError(errors)

    def update_status(self, new_status):
        """Update event status with validation"""
        valid_transitions = {
            "DRAFT": ["SCHEDULED", "CANCELLED"],
            "SCHEDULED": ["ONGOING", "CANCELLED", "POSTPONED"],
            "ONGOING": ["COMPLETED", "CANCELLED"],
            "COMPLETED": [],
            "CANCELLED": [],
            "POSTPONED": ["SCHEDULED", "CANCELLED"]
        }
        
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            self.save()
            return True
        return False

    def get_calendar_events(self):
        """Get events in calendar-friendly format"""
        events = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            events.append({
                'title': self.title,
                'start': current_date.isoformat(),
                'end': current_date.isoformat(),
                'allDay': self.is_all_day,
                'color': self.category.color if self.category else '#3B82F6',
                'url': self.get_absolute_url()
            })
            current_date += timezone.timedelta(days=1)
            
        return events

    def send_notifications(self, notification_type):
        """Send event notifications to relevant audience"""
        # Implementation depends on your notification system
        pass


class EventRegistration(BaseModel):
    """
    Event registration management with attendance tracking
    """
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("REGISTERED", _("Registered")),
        ("CANCELLED", _("Cancelled")),
        ("WAITLISTED", _("Waitlisted")),
        ("ATTENDED", _("Attended")),
        ("NO_SHOW", _("No Show")),
    )

    REGISTRATION_TYPE_CHOICES = (
        ("STUDENT", _("Student")),
        ("STAFF", _("Staff")),
        ("PARENT", _("Parent")),
        ("GUEST", _("Guest")),
        ("VOLUNTEER", _("Volunteer")),
        ("SPEAKER", _("Speaker")),
        ("ORGANIZER", _("Organizer")),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("Event")
    )
    
    # Registrant Information
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_registrations",
        verbose_name=_("Student")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_registrations",
        verbose_name=_("User")
    )
    
    # External Registrant (for guests)
    external_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("External Registrant Name")
    )
    external_email = models.EmailField(blank=True, verbose_name=_("External Email"))
    external_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("External Phone")
    )
    external_organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Organization")
    )
    
    # Registration Details
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        verbose_name=_("Registration Type")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Date")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    # Attendance Tracking
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Check-in Time")
    )
    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Check-out Time")
    )
    attendance_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Attendance Duration")
    )
    
    # Payment Information
    fee_paid = models.BooleanField(default=False, verbose_name=_("Fee Paid"))
    payment_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Payment Amount")
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Reference")
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Payment Date")
    )
    
    # Additional Information
    special_requirements = models.TextField(
        blank=True,
        verbose_name=_("Special Requirements")
    )
    dietary_restrictions = models.TextField(
        blank=True,
        verbose_name=_("Dietary Restrictions")
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Emergency Contact")
    )
    emergency_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("Emergency Phone")
    )
    
    # Internal Notes
    internal_notes = models.TextField(
        blank=True,
        verbose_name=_("Internal Notes")
    )
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name=_("Cancellation Reason")
    )

    class Meta:
        db_table = "events_registration"
        ordering = ["-registration_date", "event"]
        verbose_name = _("Event Registration")
        verbose_name_plural = _("Event Registrations")
        unique_together = [
            ['event', 'student'],
            ['event', 'user'],
            ['event', 'external_email']
        ]
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['student', 'registration_date']),
            models.Index(fields=['user', 'registration_date']),
            models.Index(fields=['registration_type', 'status']),
        ]

    def __str__(self):
        registrant_name = self.get_registrant_name()
        return f"{registrant_name} - {self.event.title}"

    def get_registrant_name(self):
        """Get registrant name based on registration type"""
        if self.student:
            return self.student.full_name
        elif self.user:
            return self.user.get_full_name()
        else:
            return self.external_name

    def get_registrant_email(self):
        """Get registrant email"""
        if self.student:
            return self.student.personal_email
        elif self.user:
            return self.user.email
        else:
            return self.external_email

    def clean(self):
        """Registration validation"""
        errors = {}
        
        # Ensure at least one registrant type is specified
        if not any([self.student, self.user, self.external_name]):
            errors['student'] = _('Either student, user, or external name must be provided')
        
        # External registration requires email
        if not self.student and not self.user and not self.external_email:
            errors['external_email'] = _('Email is required for external registrations')
        
        # Check event capacity
        if self.event.max_attendees and self.status == "REGISTERED":
            current_registrations = EventRegistration.objects.filter(
                event=self.event,
                status="REGISTERED"
            ).exclude(id=self.id).count()
            
            if current_registrations >= self.event.max_attendees:
                errors['status'] = _('Event has reached maximum capacity')
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Enhanced save with automatic calculations"""
        # Set waitlist status if event is full
        if (self.event.max_attendees and 
            self.status == "PENDING" and 
            self.event.registration_count >= self.event.max_attendees):
            self.status = "WAITLISTED"
        
        # Calculate attendance duration
        if self.check_in_time and self.check_out_time:
            self.attendance_duration = self.check_out_time - self.check_in_time
            
        self.full_clean()
        super().save(*args, **kwargs)

    def check_in(self):
        """Check in registrant"""
        if not self.check_in_time:
            self.check_in_time = timezone.now()
            self.save()

    def check_out(self):
        """Check out registrant"""
        if self.check_in_time and not self.check_out_time:
            self.check_out_time = timezone.now()
            self.attendance_duration = self.check_out_time - self.check_in_time
            self.status = "ATTENDED"
            self.save()

    def cancel_registration(self, reason=""):
        """Cancel registration"""
        self.status = "CANCELLED"
        self.cancellation_reason = reason
        self.save()
        
        # Move first waitlisted registration to registered
        if self.event.max_attendees:
            waitlisted = EventRegistration.objects.filter(
                event=self.event,
                status="WAITLISTED"
            ).order_by('registration_date').first()
            
            if waitlisted:
                waitlisted.status = "REGISTERED"
                waitlisted.save()


class EventDocument(BaseModel):
    """
    Event-related documents and resources
    """
    DOCUMENT_TYPE_CHOICES = (
        ("BROCHURE", _("Brochure")),
        ("AGENDA", _("Agenda")),
        ("SCHEDULE", _("Schedule")),
        ("PRESENTATION", _("Presentation")),
        ("HANDOUT", _("Handout")),
        ("CERTIFICATE", _("Certificate")),
        ("PHOTO", _("Photo")),
        ("VIDEO", _("Video")),
        ("AUDIO", _("Audio")),
        ("OTHER", _("Other")),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Event")
    )
    name = models.CharField(max_length=200, verbose_name=_("Document Name"))
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name=_("Document Type")
    )
    file = models.FileField(
        upload_to=event_document_upload_path,
        verbose_name=_("File")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_public = models.BooleanField(
        default=True,
        verbose_name=_("Is Public"),
        help_text=_("Whether this document is accessible to all event attendees")
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Download Count")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Uploaded By")
    )

    class Meta:
        db_table = "events_document"
        ordering = ["event", "document_type", "name"]
        verbose_name = _("Event Document")
        verbose_name_plural = _("Event Documents")
        indexes = [
            models.Index(fields=['event', 'document_type']),
            models.Index(fields=['is_public', 'document_type']),
        ]

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def get_download_url(self):
        """Get secure download URL"""
        from django.urls import reverse
        return reverse('events:download_document', kwargs={'pk': self.pk})


class EventTask(BaseModel):
    """
    Event planning and management tasks
    """
    PRIORITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("URGENT", _("Urgent")),
    )

    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("IN_PROGRESS", _("In Progress")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
        ("ON_HOLD", _("On Hold")),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Event")
    )
    title = models.CharField(max_length=200, verbose_name=_("Task Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_tasks",
        verbose_name=_("Assigned To")
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Priority")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Due Date")
    )
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed Date")
    )
    estimated_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_("Estimated Hours")
    )
    actual_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_("Actual Hours")
    )
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name="dependent_tasks",
        verbose_name=_("Dependencies")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "events_task"
        ordering = ["event", "due_date", "priority"]
        verbose_name = _("Event Task")
        verbose_name_plural = _("Event Tasks")
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['assigned_to', 'due_date']),
            models.Index(fields=['priority', 'due_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ["COMPLETED", "CANCELLED"]:
            return timezone.now() > self.due_date
        return False

    @property
    def progress_percentage(self):
        """Calculate task progress percentage"""
        if self.status == "COMPLETED":
            return 100
        elif self.status == "IN_PROGRESS":
            return 50
        elif self.status == "PENDING":
            return 0
        return 0

    def mark_complete(self):
        """Mark task as completed"""
        self.status = "COMPLETED"
        self.completed_date = timezone.now()
        self.save()

    def mark_in_progress(self):
        """Mark task as in progress"""
        self.status = "IN_PROGRESS"
        self.save()

    def can_be_completed(self):
        """Check if all dependencies are completed"""
        incomplete_dependencies = self.dependencies.filter(
            status__in=["PENDING", "IN_PROGRESS", "ON_HOLD"]
        )
        return not incomplete_dependencies.exists()


class EventExpense(BaseModel):
    """
    Event expense tracking and budget management
    """
    CATEGORY_CHOICES = (
        ("VENUE", _("Venue Rental")),
        ("CATERING", _("Catering")),
        ("EQUIPMENT", _("Equipment Rental")),
        ("MATERIALS", _("Materials & Supplies")),
        ("TRANSPORTATION", _("Transportation")),
        ("ACCOMMODATION", _("Accommodation")),
        ("MARKETING", _("Marketing & Promotion")),
        ("STAFF", _("Staff Costs")),
        ("SPEAKER", _("Speaker Fees")),
        ("ENTERTAINMENT", _("Entertainment")),
        ("OTHER", _("Other")),
    )

    PAYMENT_STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("PAID", _("Paid")),
        ("PARTIAL", _("Partially Paid")),
        ("OVERDUE", _("Overdue")),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Event")
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Expense Category")
    )
    description = models.CharField(max_length=200, verbose_name=_("Description"))
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount")
    )
    currency = models.CharField(max_length=3, default="INR", verbose_name=_("Currency"))
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Payment Status")
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Paid Amount")
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Payment Date")
    )
    vendor_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Vendor Name")
    )
    vendor_contact = models.TextField(
        blank=True,
        verbose_name=_("Vendor Contact Information")
    )
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Receipt Number")
    )
    receipt_file = models.FileField(
        upload_to=event_document_upload_path,
        null=True,
        blank=True,
        verbose_name=_("Receipt File")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "events_expense"
        ordering = ["event", "category", "payment_status"]
        verbose_name = _("Event Expense")
        verbose_name_plural = _("Event Expenses")
        indexes = [
            models.Index(fields=['event', 'category']),
            models.Index(fields=['payment_status', 'payment_date']),
        ]

    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"

    @property
    def balance_due(self):
        """Calculate balance due"""
        return self.amount - self.paid_amount

    @property
    def is_fully_paid(self):
        """Check if expense is fully paid"""
        return self.paid_amount >= self.amount

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        if self.payment_date and self.payment_status in ["PENDING", "PARTIAL"]:
            return timezone.now().date() > self.payment_date
        return False

    def make_payment(self, amount, payment_date=None):
        """Record a payment against this expense"""
        if amount <= 0:
            raise ValidationError(_("Payment amount must be positive"))
        
        if amount > self.balance_due:
            raise ValidationError(_("Payment amount exceeds balance due"))
        
        self.paid_amount += amount
        
        if self.paid_amount >= self.amount:
            self.payment_status = "PAID"
        else:
            self.payment_status = "PARTIAL"
        
        if payment_date:
            self.payment_date = payment_date
        elif not self.payment_date:
            self.payment_date = timezone.now().date()
        
        self.save()


class EventGallery(BaseModel):
    """
    Event photo and media gallery
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="gallery",
        verbose_name=_("Event")
    )
    title = models.CharField(max_length=200, verbose_name=_("Gallery Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Is Featured"))
    cover_image = models.ImageField(
        upload_to=event_image_upload_path,
        null=True,
        blank=True,
        verbose_name=_("Cover Image")
    )
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("View Count"))
    is_published = models.BooleanField(default=True, verbose_name=_("Is Published"))

    class Meta:
        db_table = "events_gallery"
        ordering = ["-created_at", "event"]
        verbose_name = _("Event Gallery")
        verbose_name_plural = _("Event Galleries")
        indexes = [
            models.Index(fields=['event', 'is_published']),
            models.Index(fields=['is_featured', 'is_published']),
        ]

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class GalleryImage(BaseModel):
    """
    Individual images in event gallery
    """
    gallery = models.ForeignKey(
        EventGallery,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Gallery")
    )
    image = models.ImageField(
        upload_to=event_image_upload_path,
        verbose_name=_("Image")
    )
    caption = models.CharField(max_length=300, blank=True, verbose_name=_("Caption"))
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Alternative Text")
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Is Featured"))
    view_count = models.PositiveIntegerField(default=0, verbose_name=_("View Count"))
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Uploaded By")
    )

    class Meta:
        db_table = "events_gallery_image"
        ordering = ["gallery", "order", "-created_at"]
        verbose_name = _("Gallery Image")
        verbose_name_plural = _("Gallery Images")
        indexes = [
            models.Index(fields=['gallery', 'is_featured']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"Image - {self.gallery.title}"

    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class EventFeedback(BaseModel):
    """
    Event feedback and ratings from attendees
    """
    RATING_CHOICES = (
        (1, "1 Star - Poor"),
        (2, "2 Stars - Fair"),
        (3, "3 Stars - Good"),
        (4, "4 Stars - Very Good"),
        (5, "5 Stars - Excellent"),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        verbose_name=_("Event")
    )
    registration = models.OneToOneField(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name=_("Registration")
    )
    
    # Ratings
    overall_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Overall Rating")
    )
    content_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Content Rating")
    )
    organization_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Organization Rating")
    )
    venue_rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Venue Rating")
    )
    
    # Feedback
    likes = models.TextField(
        verbose_name=_("What did you like?"),
        help_text=_("What aspects of the event did you enjoy most?")
    )
    improvements = models.TextField(
        verbose_name=_("Suggestions for Improvement"),
        help_text=_("What could be improved for future events?")
    )
    additional_comments = models.TextField(
        blank=True,
        verbose_name=_("Additional Comments")
    )
    
    # Willingness to participate again
    would_recommend = models.BooleanField(
        verbose_name=_("Would Recommend"),
        help_text=_("Would you recommend this event to others?")
    )
    would_attend_again = models.BooleanField(
        verbose_name=_("Would Attend Again"),
        help_text=_("Would you attend similar events in the future?")
    )
    
    # Metadata
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_("Is Anonymous")
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_("Is Approved for Display")
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Submitted At"))

    class Meta:
        db_table = "events_feedback"
        ordering = ["-submitted_at", "event"]
        verbose_name = _("Event Feedback")
        verbose_name_plural = _("Event Feedbacks")
        unique_together = [['event', 'registration']]
        indexes = [
            models.Index(fields=['event', 'overall_rating']),
            models.Index(fields=['would_recommend', 'would_attend_again']),
        ]

    def __str__(self):
        return f"Feedback - {self.event.title} - {self.overall_rating} stars"

    @property
    def average_rating(self):
        """Calculate average rating across all categories"""
        ratings = [
            self.overall_rating,
            self.content_rating,
            self.organization_rating,
            self.venue_rating
        ]
        return sum(ratings) / len(ratings)

    @property
    def attendee_name(self):
        """Get attendee name (respects anonymity)"""
        if self.is_anonymous:
            return "Anonymous"
        return self.registration.get_registrant_name()

    def clean(self):
        """Feedback validation"""
        # Ensure feedback is only submitted by attendees
        if self.registration.status != "ATTENDED":
            raise ValidationError(_("Feedback can only be submitted by event attendees"))


class RecurringEventPattern(BaseModel):
    """
    Pattern for recurring events
    """
    RECURRENCE_CHOICES = (
        ("DAILY", _("Daily")),
        ("WEEKLY", _("Weekly")),
        ("BIWEEKLY", _("Bi-weekly")),
        ("MONTHLY", _("Monthly")),
        ("YEARLY", _("Yearly")),
        ("CUSTOM", _("Custom")),
    )

    WEEKDAY_CHOICES = (
        (0, _("Monday")),
        (1, _("Tuesday")),
        (2, _("Wednesday")),
        (3, _("Thursday")),
        (4, _("Friday")),
        (5, _("Saturday")),
        (6, _("Sunday")),
    )

    base_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="recurrence_patterns",
        verbose_name=_("Base Event")
    )
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        verbose_name=_("Recurrence Type")
    )
    interval = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Interval"),
        help_text=_("Repeat every X days/weeks/months")
    )
    
    # Weekly recurrence
    weekdays = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Week Days"),
        help_text=_("Comma-separated week days (0=Monday, 6=Sunday)")
    )
    
    # Monthly recurrence
    month_day = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name=_("Day of Month")
    )
    
    # End conditions
    end_after_occurrences = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("End After Occurrences")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    
    # Generated events count
    generated_events_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Generated Events Count")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "events_recurring_pattern"
        verbose_name = _("Recurring Event Pattern")
        verbose_name_plural = _("Recurring Event Patterns")

    def __str__(self):
        return f"Recurrence - {self.base_event.title} - {self.recurrence_type}"

    def get_weekdays_list(self):
        """Get weekdays as list of integers"""
        if self.weekdays:
            return [int(day) for day in self.weekdays.split(',')]
        return []

    def generate_events(self):
        """Generate recurring events based on pattern"""
        # Implementation for generating recurring events
        # This would create new Event instances based on the recurrence pattern
        pass

    def get_next_occurrence(self, from_date=None):
        """Calculate next occurrence date"""
        if not from_date:
            from_date = timezone.now().date()
        
        # Implementation for calculating next occurrence
        # Based on recurrence type, interval, and from_date
        return None