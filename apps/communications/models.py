import uuid
import os
import json
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField

# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel
from apps.students.models import Student
from apps.academics.models import SchoolClass, Section, AcademicYear

# Phone regex for validation
phone_regex = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."),
)

def communication_attachment_upload_path(instance, filename):
    """Generate upload path for communication attachments"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.communication.title)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "communication_attachments",
        str(instance.tenant.id),
        str(instance.communication.id),
        filename
    )

def template_attachment_upload_path(instance, filename):
    """Generate upload path for template attachments"""
    ext = filename.split('.')[-1]
    filename = f"{slugify(instance.name)}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        "template_attachments",
        str(instance.tenant.id),
        filename
    )

class CommunicationChannel(BaseModel):
    """
    Communication channels configuration
    """
    CHANNEL_TYPE_CHOICES = (
        ("EMAIL", _("Email")),
        ("SMS", _("SMS")),
        ("PUSH", _("Push Notification")),
        ("IN_APP", _("In-App Notification")),
        ("LETTER", _("Physical Letter")),
        ("WHATSAPP", _("WhatsApp")),
        ("VOICE", _("Voice Call")),
        ("VIDEO", _("Video Call")),
    )

    name = models.CharField(max_length=100, verbose_name=_("Channel Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Channel Code"))
    channel_type = models.CharField(
        max_length=20,
        choices=CHANNEL_TYPE_CHOICES,
        verbose_name=_("Channel Type")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    priority = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Priority")
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Channel Configuration")
    )
    rate_limit = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Rate Limit (per hour)")
    )
    cost_per_message = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0.0000,
        verbose_name=_("Cost Per Message")
    )
    
    # Status
    last_health_check = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Health Check")
    )
    is_healthy = models.BooleanField(default=True, verbose_name=_("Is Healthy"))

    class Meta:
        db_table = "communications_channel"
        ordering = ["priority", "name"]
        verbose_name = _("Communication Channel")
        verbose_name_plural = _("Communication Channels")
        indexes = [
            models.Index(fields=['channel_type', 'is_active']),
            models.Index(fields=['is_healthy', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"

    def clean(self):
        """Channel validation"""
        if self.priority < 1 or self.priority > 10:
            raise ValidationError({'priority': _('Priority must be between 1 and 10')})

    def test_connection(self):
        """Test channel connection"""
        # Implementation depends on channel type
        pass


class CommunicationTemplate(BaseModel):
    """
    Reusable communication templates
    """
    TEMPLATE_TYPE_CHOICES = (
        ("EMAIL", _("Email Template")),
        ("SMS", _("SMS Template")),
        ("PUSH", _("Push Notification Template")),
        ("LETTER", _("Letter Template")),
        ("WHATSAPP", _("WhatsApp Template")),
        ("VOICE", _("Voice Template")),
    )

    LANGUAGE_CHOICES = (
        ("en", _("English")),
        ("hi", _("Hindi")),
        ("es", _("Spanish")),
        ("fr", _("French")),
        ("de", _("German")),
        ("zh", _("Chinese")),
        ("ar", _("Arabic")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Template Name"))
    code = models.CharField(max_length=100, unique=True, verbose_name=_("Template Code"))
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        verbose_name=_("Template Type")
    )
    channel = models.ForeignKey(
        CommunicationChannel,
        on_delete=models.CASCADE,
        related_name="templates",
        verbose_name=_("Communication Channel")
    )
    
    # Content
    subject = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Subject")
    )
    body = models.TextField(verbose_name=_("Template Body"))
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="en",
        verbose_name=_("Language")
    )
    
    # Metadata
    description = models.TextField(blank=True, verbose_name=_("Description"))
    variables = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Template Variables"),
        help_text=_("List of available variables in JSON format")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_system = models.BooleanField(default=False, verbose_name=_("Is System Template"))
    
    # Approval workflow
    requires_approval = models.BooleanField(
        default=False,
        verbose_name=_("Requires Approval")
    )
    is_approved = models.BooleanField(default=True, verbose_name=_("Is Approved"))
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_templates",
        verbose_name=_("Approved By")
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Approved At"))

    class Meta:
        db_table = "communications_template"
        ordering = ["name", "template_type"]
        verbose_name = _("Communication Template")
        verbose_name_plural = _("Communication Templates")
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['template_type', 'language']),
            models.Index(fields=['is_approved', 'requires_approval']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    def clean(self):
        """Template validation"""
        # Validate variables JSON
        try:
            if self.variables and not isinstance(self.variables, list):
                raise ValidationError({
                    'variables': _('Variables must be a JSON array')
                })
        except (TypeError, ValueError):
            raise ValidationError({
                'variables': _('Invalid JSON format for variables')
            })

    def save(self, *args, **kwargs):
        """Enhanced save with approval tracking"""
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def render_template(self, context):
        """Render template with context variables"""
        rendered_body = self.body
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered_body = rendered_body.replace(placeholder, str(value))
        
        rendered_subject = self.subject
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
        
        return {
            'subject': rendered_subject,
            'body': rendered_body
        }

    def get_available_variables(self):
        """Get list of available template variables"""
        return self.variables if self.variables else []


class CommunicationCampaign(BaseModel):
    """
    Campaign management for bulk communications
    """
    CAMPAIGN_TYPE_CHOICES = (
        ("BULK", _("Bulk Communication")),
        ("SCHEDULED", _("Scheduled Campaign")),
        ("TRIGGERED", _("Triggered Campaign")),
        ("ONBOARDING", _("Onboarding Series")),
        ("MARKETING", _("Marketing Campaign")),
        ("ANNOUNCEMENT", _("Announcement")),
        ("REMINDER", _("Reminder Series")),
    )

    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("SCHEDULED", _("Scheduled")),
        ("RUNNING", _("Running")),
        ("PAUSED", _("Paused")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
        ("FAILED", _("Failed")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Campaign Name"))
    campaign_type = models.CharField(
        max_length=20,
        choices=CAMPAIGN_TYPE_CHOICES,
        verbose_name=_("Campaign Type")
    )
    template = models.ForeignKey(
        CommunicationTemplate,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name=_("Template")
    )
    
    # Scheduling
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled For")
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Start Date")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    is_recurring = models.BooleanField(default=False, verbose_name=_("Is Recurring"))
    recurrence_pattern = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Recurrence Pattern")
    )
    
    # Audience
    target_audience = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Target Audience"),
        help_text=_("JSON configuration for target audience filtering")
    )
    total_recipients = models.PositiveIntegerField(default=0, verbose_name=_("Total Recipients"))
    
    # Performance tracking
    sent_count = models.PositiveIntegerField(default=0, verbose_name=_("Sent Count"))
    delivered_count = models.PositiveIntegerField(default=0, verbose_name=_("Delivered Count"))
    opened_count = models.PositiveIntegerField(default=0, verbose_name=_("Opened Count"))
    clicked_count = models.PositiveIntegerField(default=0, verbose_name=_("Clicked Count"))
    failed_count = models.PositiveIntegerField(default=0, verbose_name=_("Failed Count"))
    
    # Budget and limits
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Campaign Budget")
    )
    cost_so_far = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Cost So Far")
    )
    rate_limit = models.PositiveIntegerField(
        default=1000,
        verbose_name=_("Messages Per Hour Limit")
    )

    class Meta:
        db_table = "communications_campaign"
        ordering = ["-created_at", "name"]
        verbose_name = _("Communication Campaign")
        verbose_name_plural = _("Communication Campaigns")
        indexes = [
            models.Index(fields=['campaign_type', 'status']),
            models.Index(fields=['scheduled_for', 'status']),
            models.Index(fields=['status', 'is_recurring']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def delivery_rate(self):
        """Calculate delivery rate"""
        if self.sent_count == 0:
            return 0
        return (self.delivered_count / self.sent_count) * 100

    @property
    def open_rate(self):
        """Calculate open rate"""
        if self.delivered_count == 0:
            return 0
        return (self.opened_count / self.delivered_count) * 100

    @property
    def click_rate(self):
        """Calculate click rate"""
        if self.delivered_count == 0:
            return 0
        return (self.clicked_count / self.delivered_count) * 100

    @property
    def is_active(self):
        """Check if campaign is currently active"""
        return self.status in ["SCHEDULED", "RUNNING"]

    def clean(self):
        """Campaign validation"""
        errors = {}
        
        if self.scheduled_for and self.scheduled_for < timezone.now():
            errors['scheduled_for'] = _('Scheduled time cannot be in the past')
        
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors['end_date'] = _('End date must be after start date')
            
        if errors:
            raise ValidationError(errors)

    def start_campaign(self):
        """Start the campaign"""
        if self.status == "DRAFT":
            self.status = "RUNNING"
            self.start_date = timezone.now()
            self.save()

    def pause_campaign(self):
        """Pause the campaign"""
        if self.status == "RUNNING":
            self.status = "PAUSED"
            self.save()

    def resume_campaign(self):
        """Resume the campaign"""
        if self.status == "PAUSED":
            self.status = "RUNNING"
            self.save()

    def complete_campaign(self):
        """Mark campaign as completed"""
        self.status = "COMPLETED"
        self.end_date = timezone.now()
        self.save()

    def get_performance_metrics(self):
        """Get campaign performance metrics"""
        return {
            'total_recipients': self.total_recipients,
            'sent_count': self.sent_count,
            'delivered_count': self.delivered_count,
            'opened_count': self.opened_count,
            'clicked_count': self.clicked_count,
            'failed_count': self.failed_count,
            'delivery_rate': self.delivery_rate,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'cost_so_far': float(self.cost_so_far)
        }


class Communication(BaseModel):
    """
    Main communication model for individual messages
    """
    PRIORITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("URGENT", _("Urgent")),
    )

    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("SCHEDULED", _("Scheduled")),
        ("SENDING", _("Sending")),
        ("SENT", _("Sent")),
        ("DELIVERED", _("Delivered")),
        ("READ", _("Read")),
        ("FAILED", _("Failed")),
        ("BOUNCED", _("Bounced")),
        ("COMPLAINED", _("Complained")),
    )

    DIRECTION_CHOICES = (
        ("OUTBOUND", _("Outbound")),
        ("INBOUND", _("Inbound")),
    )

    # Basic Information
    title = models.CharField(max_length=500, verbose_name=_("Communication Title"))
    subject = models.CharField(max_length=1000, blank=True, verbose_name=_("Subject"))
    content = models.TextField(verbose_name=_("Content"))
    summary = models.TextField(blank=True, verbose_name=_("Summary"))
    
    # Channel and Template
    channel = models.ForeignKey(
        CommunicationChannel,
        on_delete=models.CASCADE,
        related_name="communications",
        verbose_name=_("Communication Channel")
    )
    template = models.ForeignKey(
        CommunicationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name=_("Template")
    )
    campaign = models.ForeignKey(
        CommunicationCampaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name=_("Campaign")
    )
    
    # Sender and Recipient
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_communications",
        verbose_name=_("Sender")
    )
    recipient_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Recipient Type")
    )
    recipient_id = models.UUIDField(verbose_name=_("Recipient ID"))
    recipient = GenericForeignKey('recipient_type', 'recipient_id')
    
    # External recipient (for non-system users)
    external_recipient_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("External Recipient Name")
    )
    external_recipient_email = models.EmailField(
        blank=True,
        verbose_name=_("External Recipient Email")
    )
    external_recipient_phone = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name=_("External Recipient Phone")
    )
    
    # Status and Tracking
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
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        default="OUTBOUND",
        verbose_name=_("Direction")
    )
    
    # Scheduling
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled For")
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent At")
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Delivered At")
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read At")
    )
    
    # Tracking and Analytics
    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_("Tracking ID")
    )
    open_count = models.PositiveIntegerField(default=0, verbose_name=_("Open Count"))
    click_count = models.PositiveIntegerField(default=0, verbose_name=_("Click Count"))
    last_opened_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Opened At")
    )
    
    # Response tracking (for inbound)
    in_reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("In Reply To")
    )
    is_automated = models.BooleanField(default=False, verbose_name=_("Is Automated Response"))
    
    # Cost tracking
    cost = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0.0000,
        verbose_name=_("Communication Cost")
    )
    
    # Error handling
    error_message = models.TextField(blank=True, verbose_name=_("Error Message"))
    retry_count = models.PositiveIntegerField(default=0, verbose_name=_("Retry Count"))
    max_retries = models.PositiveIntegerField(default=3, verbose_name=_("Maximum Retries"))

    class Meta:
        db_table = "communications_communication"
        ordering = ["-created_at", "-priority"]
        verbose_name = _("Communication")
        verbose_name_plural = _("Communications")
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['tracking_id']),
            models.Index(fields=['recipient_type', 'recipient_id']),
            models.Index(fields=['campaign', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    @property
    def recipient_name(self):
        """Get recipient name"""
        if self.recipient:
            if hasattr(self.recipient, 'get_display_name'):
                return self.recipient.get_display_name()
            elif hasattr(self.recipient, 'get_full_name'):
                return self.recipient.get_full_name()
            else:
                return str(self.recipient)
        return self.external_recipient_name

    @property
    def recipient_contact(self):
        """Get recipient contact information"""
        if self.recipient:
            if hasattr(self.recipient, 'email'):
                return self.recipient.email
            elif hasattr(self.recipient, 'phone'):
                return self.recipient.phone
        return self.external_recipient_email or self.external_recipient_phone

    @property
    def is_scheduled(self):
        """Check if communication is scheduled"""
        return self.status == "SCHEDULED" and self.scheduled_for

    @property
    def can_retry(self):
        """Check if communication can be retried"""
        return self.status == "FAILED" and self.retry_count < self.max_retries

    def clean(self):
        """Communication validation"""
        errors = {}
        
        # Validate scheduled time
        if self.scheduled_for and self.scheduled_for < timezone.now():
            errors['scheduled_for'] = _('Scheduled time cannot be in the past')
        
        # Validate recipient information
        if not any([self.recipient_id, self.external_recipient_email, self.external_recipient_phone]):
            errors['recipient_id'] = _('Either system recipient or external contact information is required')
            
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Enhanced save with status tracking"""
        # Set sent timestamp when status changes to SENT
        if self.status == "SENT" and not self.sent_at:
            self.sent_at = timezone.now()
        
        super().save(*args, **kwargs)

    def mark_as_sent(self):
        """Mark communication as sent"""
        self.status = "SENT"
        self.sent_at = timezone.now()
        self.save()

    def mark_as_delivered(self):
        """Mark communication as delivered"""
        self.status = "DELIVERED"
        self.delivered_at = timezone.now()
        self.save()

    def mark_as_read(self):
        """Mark communication as read"""
        self.status = "READ"
        self.read_at = timezone.now()
        self.open_count += 1
        self.last_opened_at = timezone.now()
        self.save()

    def record_click(self):
        """Record a click on communication links"""
        self.click_count += 1
        self.save(update_fields=['click_count'])

    def record_failure(self, error_message):
        """Record communication failure"""
        self.status = "FAILED"
        self.error_message = error_message
        self.retry_count += 1
        self.save()

    def retry_sending(self):
        """Retry sending failed communication"""
        if self.can_retry:
            self.status = "SENDING"
            self.error_message = ""
            self.save()


class CommunicationAttachment(BaseModel):
    """
    Attachments for communications
    """
    communication = models.ForeignKey(
        Communication,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Communication")
    )
    file = models.FileField(
        upload_to=communication_attachment_upload_path,
        verbose_name=_("File")
    )
    file_name = models.CharField(max_length=500, verbose_name=_("Original File Name"))
    file_size = models.PositiveIntegerField(default=0, verbose_name=_("File Size (bytes)"))
    file_type = models.CharField(max_length=100, verbose_name=_("File Type"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    download_count = models.PositiveIntegerField(default=0, verbose_name=_("Download Count"))
    is_inline = models.BooleanField(
        default=False,
        verbose_name=_("Is Inline Attachment"),
        help_text=_("Whether this attachment should be displayed inline in the content")
    )

    class Meta:
        db_table = "communications_attachment"
        ordering = ["communication", "file_name"]
        verbose_name = _("Communication Attachment")
        verbose_name_plural = _("Communication Attachments")
        indexes = [
            models.Index(fields=['communication', 'file_type']),
        ]

    def __str__(self):
        return f"{self.file_name} - {self.communication.title}"

    def clean(self):
        """Attachment validation"""
        # File size validation (25MB max)
        if self.file and self.file.size > 25 * 1024 * 1024:
            raise ValidationError(_('File size must be less than 25MB'))

    def save(self, *args, **kwargs):
        """Enhanced save with file processing"""
        if self.file:
            self.file_name = self.file.name
            self.file_size = self.file.size
            # Extract file type from extension
            import os
            name, ext = os.path.splitext(self.file_name)
            self.file_type = ext.lower().lstrip('.') if ext else 'unknown'
            
        super().save(*args, **kwargs)

    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save(update_fields=['download_count'])

    def get_download_url(self):
        """Get secure download URL"""
        from django.urls import reverse
        return reverse('communications:download_attachment', kwargs={'pk': self.pk})


class Notification(BaseModel):
    """
    In-app notification system
    """
    NOTIFICATION_TYPE_CHOICES = (
        ("SYSTEM", _("System Notification")),
        ("ACADEMIC", _("Academic Update")),
        ("FINANCIAL", _("Financial Alert")),
        ("EVENT", _("Event Reminder")),
        ("SECURITY", _("Security Alert")),
        ("ANNOUNCEMENT", _("General Announcement")),
        ("MESSAGE", _("New Message")),
        ("TASK", _("Task Assignment")),
        ("OTHER", _("Other")),
    )

    PRIORITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("URGENT", _("Urgent")),
    )

    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Recipient")
    )
    
    # Content
    title = models.CharField(max_length=500, verbose_name=_("Notification Title"))
    message = models.TextField(verbose_name=_("Notification Message"))
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="SYSTEM",
        verbose_name=_("Notification Type")
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Priority")
    )
    
    # Action and Link
    action_url = models.URLField(blank=True, verbose_name=_("Action URL"))
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Action Text")
    )
    
    # Status and Tracking
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Read At"))
    is_dismissed = models.BooleanField(default=False, verbose_name=_("Is Dismissed"))
    dismissed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Dismissed At"))
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At")
    )
    
    # Related object tracking
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Content Type")
    )
    object_id = models.UUIDField(null=True, blank=True, verbose_name=_("Object ID"))
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        db_table = "communications_notification"
        ordering = ["-created_at", "-priority"]
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'priority']),
            models.Index(fields=['expires_at', 'is_dismissed']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient}"

    @property
    def is_expired(self):
        """Check if notification is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_active(self):
        """Check if notification is active (not read, dismissed, or expired)"""
        return not (self.is_read or self.is_dismissed or self.is_expired)

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def dismiss(self):
        """Dismiss notification"""
        if not self.is_dismissed:
            self.is_dismissed = True
            self.dismissed_at = timezone.now()
            self.save()

    def clean(self):
        """Notification validation"""
        if self.expires_at and self.expires_at < timezone.now():
            raise ValidationError({'expires_at': _('Expiration date cannot be in the past')})


class MessageThread(BaseModel):
    """
    Message threads for conversations
    """
    THREAD_TYPE_CHOICES = (
        ("DIRECT", _("Direct Message")),
        ("GROUP", _("Group Conversation")),
        ("SUPPORT", _("Support Ticket")),
        ("BROADCAST", _("Broadcast")),
    )

    title = models.CharField(max_length=500, verbose_name=_("Thread Title"))
    thread_type = models.CharField(
        max_length=20,
        choices=THREAD_TYPE_CHOICES,
        default="DIRECT",
        verbose_name=_("Thread Type")
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="message_threads",
        verbose_name=_("Participants")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_threads",
        verbose_name=_("Created By")
    )
    
    # Group thread specific
    is_private = models.BooleanField(default=True, verbose_name=_("Is Private"))
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="managed_threads",
        blank=True,
        verbose_name=_("Thread Administrators")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Message At")
    )
    
    # Metadata
    description = models.TextField(blank=True, verbose_name=_("Description"))
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags")
    )

    class Meta:
        db_table = "communications_message_thread"
        ordering = ["-last_message_at", "-created_at"]
        verbose_name = _("Message Thread")
        verbose_name_plural = _("Message Threads")
        indexes = [
            models.Index(fields=['thread_type', 'is_active']),
            models.Index(fields=['is_active', 'last_message_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_thread_type_display()})"

    @property
    def participant_count(self):
        """Get number of participants"""
        return self.participants.count()

    @property
    def last_message(self):
        """Get last message in thread"""
        return self.messages.order_by('-created_at').first()

    def add_participant(self, user, added_by=None):
        """Add participant to thread"""
        if user not in self.participants.all():
            self.participants.add(user)
            
            # Create system message for participant addition
            if added_by:
                SystemMessage.objects.create(
                    thread=self,
                    message_type="PARTICIPANT_ADDED",
                    content=f"{added_by.get_full_name()} added {user.get_full_name()} to the conversation",
                    created_by=added_by
                )

    def remove_participant(self, user, removed_by=None):
        """Remove participant from thread"""
        if user in self.participants.all():
            self.participants.remove(user)
            
            # Create system message for participant removal
            if removed_by:
                SystemMessage.objects.create(
                    thread=self,
                    message_type="PARTICIPANT_REMOVED",
                    content=f"{removed_by.get_full_name()} removed {user.get_full_name()} from the conversation",
                    created_by=removed_by
                )

class Message(BaseModel):
    """
    Internal messaging system
    """
    sender = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name=_("Sender")
    )
    subject = models.CharField(
        max_length=200,
        verbose_name=_("Subject")
    )
    body = models.TextField(
        verbose_name=_("Message Body")
    )
    message_type = models.CharField(
        max_length=20,
        choices=(
            ("ANNOUNCEMENT", _("Announcement")),
            ("NOTICE", _("Notice")),
            ("MESSAGE", _("Personal Message")),
            ("ALERT", _("Alert")),
        ),
        default="MESSAGE",
        verbose_name=_("Message Type")
    )
    priority = models.CharField(
        max_length=10,
        choices=(
            ("LOW", _("Low")),
            ("NORMAL", _("Normal")),
            ("HIGH", _("High")),
            ("URGENT", _("Urgent")),
        ),
        default="NORMAL",
        verbose_name=_("Priority")
    )
    is_important = models.BooleanField(
        default=False,
        verbose_name=_("Is Important")
    )

    class Meta:
        db_table = "communications_messages"
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} - {self.sender}"


class MessageRecipient(BaseModel):
    """
    Message recipient relationship
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="recipients"
    )
    recipient = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="received_messages"
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Received At")
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Is Read")
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read At")
    )

    class Meta:
        db_table = "communications_message_recipients"
        verbose_name = _("Message Recipient")
        verbose_name_plural = _("Message Recipients")
        unique_together = [['message', 'recipient']]

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()



class SystemMessage(BaseModel):
    """
    System-generated messages for automated communications
    """
    MESSAGE_TYPE_CHOICES = (
        ("PARTICIPANT_ADDED", _("Participant Added")),
        ("PARTICIPANT_REMOVED", _("Participant Removed")),
        ("THREAD_CREATED", _("Thread Created")),
        ("THREAD_ARCHIVED", _("Thread Archived")),
        ("NAME_CHANGED", _("Thread Name Changed")),
        ("TOPIC_CHANGED", _("Topic Changed")),
        ("OTHER", _("Other System Message")),
    )

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name="system_messages",
        verbose_name=_("Thread")
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        verbose_name=_("Message Type")
    )
    content = models.TextField(verbose_name=_("Content"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("Created By")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata")
    )

    class Meta:
        db_table = "communications_system_message"
        ordering = ["created_at"]
        verbose_name = _("System Message")
        verbose_name_plural = _("System Messages")

    def __str__(self):
        return f"System: {self.get_message_type_display()} - {self.thread.title}"


class CommunicationPreference(BaseModel):
    """
    User communication preferences and settings
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communication_preferences",
        verbose_name=_("User")
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True, verbose_name=_("Email Enabled"))
    sms_enabled = models.BooleanField(default=True, verbose_name=_("SMS Enabled"))
    push_enabled = models.BooleanField(default=True, verbose_name=_("Push Notifications Enabled"))
    in_app_enabled = models.BooleanField(default=True, verbose_name=_("In-App Notifications Enabled"))
    whatsapp_enabled = models.BooleanField(default=False, verbose_name=_("WhatsApp Enabled"))
    
    # Notification categories
    academic_notifications = models.BooleanField(default=True, verbose_name=_("Academic Notifications"))
    financial_notifications = models.BooleanField(default=True, verbose_name=_("Financial Notifications"))
    event_notifications = models.BooleanField(default=True, verbose_name=_("Event Notifications"))
    security_notifications = models.BooleanField(default=True, verbose_name=_("Security Notifications"))
    marketing_notifications = models.BooleanField(default=False, verbose_name=_("Marketing Notifications"))
    system_notifications = models.BooleanField(default=True, verbose_name=_("System Notifications"))
    
    # Timing preferences
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Quiet Hours Start")
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Quiet Hours End")
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        verbose_name=_("Timezone")
    )
    
    # Language preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=CommunicationTemplate.LANGUAGE_CHOICES,
        default="en",
        verbose_name=_("Preferred Language")
    )
    
    # Digest preferences
    daily_digest = models.BooleanField(default=True, verbose_name=_("Daily Digest"))
    weekly_digest = models.BooleanField(default=True, verbose_name=_("Weekly Digest"))
    digest_time = models.TimeField(
        default="18:00",
        verbose_name=_("Digest Delivery Time")
    )

    class Meta:
        db_table = "communications_preference"
        verbose_name = _("Communication Preference")
        verbose_name_plural = _("Communication Preferences")

    def __str__(self):
        return f"Communication Preferences - {self.user}"

    @property
    def is_quiet_hours(self):
        """Check if currently in quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
            
        now = timezone.now()
        current_time = now.time()
        
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end

    def can_receive_notification(self, notification_type, channel):
        """Check if user can receive specific notification type via channel"""
        channel_enabled = getattr(self, f"{channel.lower()}_enabled", False)
        category_enabled = getattr(self, f"{notification_type.lower()}_notifications", False)
        
        return channel_enabled and category_enabled and not self.is_quiet_hours


class CommunicationAnalytics(BaseModel):
    """
    Analytics and reporting for communications
    """
    date = models.DateField(verbose_name=_("Date"))
    channel = models.ForeignKey(
        CommunicationChannel,
        on_delete=models.CASCADE,
        related_name="analytics",
        verbose_name=_("Channel")
    )
    
    # Volume metrics
    total_sent = models.PositiveIntegerField(default=0, verbose_name=_("Total Sent"))
    total_delivered = models.PositiveIntegerField(default=0, verbose_name=_("Total Delivered"))
    total_failed = models.PositiveIntegerField(default=0, verbose_name=_("Total Failed"))
    total_bounced = models.PositiveIntegerField(default=0, verbose_name=_("Total Bounced"))
    
    # Engagement metrics
    total_opened = models.PositiveIntegerField(default=0, verbose_name=_("Total Opened"))
    total_clicked = models.PositiveIntegerField(default=0, verbose_name=_("Total Clicked"))
    total_replied = models.PositiveIntegerField(default=0, verbose_name=_("Total Replied"))
    total_complained = models.PositiveIntegerField(default=0, verbose_name=_("Total Complained"))
    total_unsubscribed = models.PositiveIntegerField(default=0, verbose_name=_("Total Unsubscribed"))
    
    # Performance metrics
    delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Delivery Rate (%)")
    )
    open_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Open Rate (%)")
    )
    click_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Click Rate (%)")
    )
    
    # Cost metrics
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Cost")
    )
    cost_per_message = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0.0000,
        verbose_name=_("Cost Per Message")
    )

    class Meta:
        db_table = "communications_analytics"
        unique_together = [['date', 'channel']]
        ordering = ["-date", "channel"]
        verbose_name = _("Communication Analytics")
        verbose_name_plural = _("Communication Analytics")
        indexes = [
            models.Index(fields=['date', 'channel']),
        ]

    def __str__(self):
        return f"Analytics - {self.date} - {self.channel.name}"

    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.open_rate = (self.total_opened / self.total_delivered) * 100 if self.total_delivered > 0 else 0
            self.click_rate = (self.total_clicked / self.total_delivered) * 100 if self.total_delivered > 0 else 0
            self.cost_per_message = self.total_cost / self.total_sent if self.total_sent > 0 else 0

    def save(self, *args, **kwargs):
        """Enhanced save with metric calculation"""
        self.calculate_metrics()
        super().save(*args, **kwargs)