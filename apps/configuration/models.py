import uuid
import json
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from decimal import Decimal
import re
# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel
from apps.academics.models import AcademicYear

class SystemSetting(BaseModel):
    """
    System-wide configuration settings with hierarchical organization
    """
    SETTING_TYPE_CHOICES = (
        ("STRING", _("String")),
        ("TEXT", _("Text")),
        ("INTEGER", _("Integer")),
        ("DECIMAL", _("Decimal")),
        ("BOOLEAN", _("Boolean")),
        ("JSON", _("JSON")),
        ("DATETIME", _("DateTime")),
        ("DATE", _("Date")),
        ("TIME", _("Time")),
        ("FILE", _("File")),
        ("IMAGE", _("Image")),
        ("CHOICE", _("Choice")),
        ("MULTI_CHOICE", _("Multiple Choice")),
    )

    CATEGORY_CHOICES = (
        ("GENERAL", _("General")),
        ("ACADEMIC", _("Academic")),
        ("FINANCE", _("Finance")),
        ("COMMUNICATION", _("Communication")),
        ("SECURITY", _("Security")),
        ("APPEARANCE", _("Appearance")),
        ("INTEGRATION", _("Integration")),
        ("BACKUP", _("Backup & Recovery")),
        ("NOTIFICATION", _("Notifications")),
        ("SYSTEM", _("System")),
        ("CUSTOM", _("Custom")),
    )

    # Basic Information
    key = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_("Setting Key"),
        help_text=_("Unique identifier for the setting (e.g., 'site.title', 'email.host')")
    )
    name = models.CharField(max_length=500, verbose_name=_("Setting Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="GENERAL",
        verbose_name=_("Category")
    )
    group = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Group"),
        help_text=_("Sub-group for organizing related settings")
    )
    
    # Value Configuration
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPE_CHOICES,
        default="STRING",
        verbose_name=_("Setting Type")
    )
    value_string = models.CharField(max_length=2000, blank=True, verbose_name=_("String Value"))
    value_text = models.TextField(blank=True, verbose_name=_("Text Value"))
    value_integer = models.IntegerField(null=True, blank=True, verbose_name=_("Integer Value"))
    value_decimal = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Decimal Value")
    )
    value_boolean = models.BooleanField(null=True, blank=True, verbose_name=_("Boolean Value"))
    value_json = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("JSON Value")
    )
    value_datetime = models.DateTimeField(null=True, blank=True, verbose_name=_("DateTime Value"))
    value_date = models.DateField(null=True, blank=True, verbose_name=_("Date Value"))
    value_time = models.TimeField(null=True, blank=True, verbose_name=_("Time Value"))
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('TABLE', _('Table')),
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Configuration
    is_encrypted = models.BooleanField(
        default=False,
        verbose_name=_("Is Encrypted"),
        help_text=_("Whether the setting value should be encrypted in database")
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Is Public"),
        help_text=_("Whether this setting can be exposed via API")
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name=_("Is Required"),
        help_text=_("Whether this setting must have a value")
    )
    is_readonly = models.BooleanField(
        default=False,
        verbose_name=_("Is Read Only"),
        help_text=_("Whether this setting can be modified via UI/API")
    )
    
    # Validation
    validation_regex = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Validation Regex")
    )
    validation_message = models.TextField(
        blank=True,
        verbose_name=_("Validation Message")
    )
    min_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Minimum Value")
    )
    max_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Maximum Value")
    )
    choices = models.TextField(
        blank=True,
        verbose_name=_("Available Choices"),
        help_text=_("Comma-separated list of choices for CHOICE and MULTI_CHOICE types")
    )
    
    # Metadata
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    depends_on = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dependent_settings",
        verbose_name=_("Depends On"),
        help_text=_("Parent setting that this setting depends on")
    )
    version = models.PositiveIntegerField(default=1, verbose_name=_("Version"))

    tenant = models.ForeignKey(
        'tenants.Tenant',  # Adjust based on your tenant model
        on_delete=models.CASCADE,
        null=True,  # Allow null for system-wide settings
        blank=True,  # Allow blank in forms
        related_name='system_settings'
    )
    
    class Meta:
        db_table = "configuration_system_setting"
        ordering = ["category", "group", "order", "key"]
        verbose_name = _("System Setting")
        verbose_name_plural = _("System Settings")
        indexes = [
            models.Index(fields=['key', 'category']),
            models.Index(fields=['category', 'group']),
            models.Index(fields=['is_public', 'is_encrypted']),
            models.Index(fields=['setting_type', 'is_required']),
            models.Index(fields=['chart_field']),
        ]
        
    def __str__(self):
        return f"{self.key} ({self.get_setting_type_display()})"

    @property
    def value(self):
        """Get the appropriate value based on setting type"""
        field_name = f"value_{self.setting_type.lower()}"
        return getattr(self, field_name, None)

    @value.setter
    def value(self, new_value):
        """Set the appropriate value based on setting type"""
        field_name = f"value_{self.setting_type.lower()}"
        if hasattr(self, field_name):
            setattr(self, field_name, new_value)

    def clean(self):
        """Comprehensive setting validation"""
        errors = {}
        
        # Key validation - allow dots for hierarchical keys
        key_pattern = r'^[a-zA-Z_][a-zA-Z0-9._-]*$'
        if not re.match(key_pattern, self.key):
            errors['key'] = _('Key must start with a letter or underscore and contain only letters, numbers, underscores, dots, or hyphens')

    def save(self, *args, **kwargs):
        """Enhanced save with validation and encryption handling"""
        self.full_clean()
        
        # Handle encryption if required
        if self.is_encrypted and self.value_string:
            # In a real implementation, you'd encrypt the value here
            # For now, we'll just mark it as needing encryption
            pass
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('configuration:setting_detail', kwargs={'pk': self.pk})

    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value by key"""
        try:
            setting = cls.objects.get(key=key, tenant=get_current_tenant())
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value):
        """Set setting value by key"""
        from apps.core.utils.tenant import get_current_tenant
        tenant = get_current_tenant()
        
        setting, created = cls.objects.get_or_create(
            key=key,
            tenant=tenant,
            defaults={'name': key.replace('.', ' ').title()}
        )
        
        # Determine the correct field to set based on value type
        if isinstance(value, bool):
            setting.setting_type = 'BOOLEAN'
            setting.value_boolean = value
        elif isinstance(value, int):
            setting.setting_type = 'INTEGER'
            setting.value_integer = value
        elif isinstance(value, float):
            setting.setting_type = 'DECIMAL'
            setting.value_decimal = value
        elif isinstance(value, (list, dict)):
            setting.setting_type = 'JSON'
            setting.value_json = value
        else:
            setting.setting_type = 'STRING'
            setting.value_string = str(value)
        
        setting.save()
        return setting


class AcademicConfiguration(BaseModel):
    """
    Academic-specific configuration and policies
    """
    academic_year_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Academic Year Name")
    )
    academic_year_start = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Academic Year Start")
    )
    academic_year_end = models.DateField(
        null=True, 
        blank=True,
        verbose_name=_("Academic Year End")
    )
    
    # Grading Configuration
    grading_system_name = models.CharField(
        max_length=100,
        default="Standard Grading",
        verbose_name=_("Grading System Name")
    )
    pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=35.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Minimum Pass Percentage")
    )
    grace_marks = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Maximum Grace Marks")
    )
    
    # Attendance Configuration
    min_attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=75.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Minimum Attendance Percentage")
    )
    working_days_per_week = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name=_("Working Days Per Week")
    )
    periods_per_day = models.PositiveIntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name=_("Periods Per Day")
    )
    
    # Examination Configuration
    exam_types = models.TextField(
        blank=True,
        verbose_name=_("Exam Types"),
        help_text=_("Comma-separated list of exam types")
    )
    practical_marks_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00,
        verbose_name=_("Practical Marks Weight (%)")
    )
    theory_marks_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,
        verbose_name=_("Theory Marks Weight (%)")
    )
    
    # Promotion Rules
    promotion_conditions = models.TextField(
        blank=True,
        verbose_name=_("Promotion Conditions")
    )
    max_failed_subjects = models.PositiveIntegerField(
        default=2,
        verbose_name=_("Maximum Failed Subjects for Promotion")
    )
    
    # Academic Calendar
    term_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Term Start Date")
    )
    term_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Term End Date")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Fee Configuration
    late_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        verbose_name=_("Late Fee Percentage")
    )
    late_fee_grace_days = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Late Fee Grace Period (Days)")
    )

    class Meta:
        db_table = "configuration_academic"
        verbose_name = _("Academic Configuration")
        verbose_name_plural = _("Academic Configurations")
        unique_together = [['tenant']]
        indexes = [
            models.Index(fields=['academic_year_name']),
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"Academic Configuration - {self.academic_year_name}"

    def clean(self):
        """Academic configuration validation"""
        if self.practical_marks_weight + self.theory_marks_weight != 100:
            raise ValidationError({
                'practical_marks_weight': _('Practical and theory weights must sum to 100%')
            })

    @classmethod
    def get_for_tenant(cls, tenant):
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj


class FinancialConfiguration(BaseModel):
    """
    Financial system configuration and policies
    """
    # Currency and Locale
    base_currency = models.CharField(
        max_length=3,
        default="INR",
        verbose_name=_("Base Currency")
    )
    currency_symbol = models.CharField(
        max_length=5,
        default="₹",
        verbose_name=_("Currency Symbol")
    )
    decimal_places = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        verbose_name=_("Decimal Places")
    )
    
    # Tax Configuration
    tax_enabled = models.BooleanField(default=True, verbose_name=_("Tax Enabled"))
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        verbose_name=_("Tax Rate (%)")
    )
    tax_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tax Identification Number")
    )
    
    # Invoice Configuration
    invoice_prefix = models.CharField(
        max_length=10,
        default="INV",
        verbose_name=_("Invoice Prefix")
    )
    invoice_start_number = models.PositiveIntegerField(
        default=1000,
        verbose_name=_("Invoice Start Number")
    )
    invoice_terms = models.TextField(
        blank=True,
        verbose_name=_("Invoice Terms and Conditions")
    )
    invoice_notes = models.TextField(
        blank=True,
        verbose_name=_("Invoice Notes")
    )
    
    # Payment Configuration
    payment_methods = models.TextField(
        blank=True,
        verbose_name=_("Available Payment Methods"),
        help_text=_("Comma-separated list of payment methods")
    )
    online_payment_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Online Payment Enabled")
    )
    payment_gateway_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Payment Gateway Name")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Fee Configuration
    auto_late_fee = models.BooleanField(
        default=True,
        verbose_name=_("Auto Calculate Late Fees")
    )
    late_fee_calculation = models.CharField(
        max_length=20,
        choices=(
            ("FIXED", _("Fixed Amount")),
            ("PERCENTAGE", _("Percentage of Due")),
            ("DAILY", _("Daily Compound")),
        ),
        default="PERCENTAGE",
        verbose_name=_("Late Fee Calculation Method")
    )
    
    # Bank Account Configuration
    bank_accounts_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Number of Bank Accounts")
    )
    default_bank_account_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Default Bank Account Name")
    )
    
    # Financial Year
    financial_year_start = models.DateField(verbose_name=_("Financial Year Start"))
    financial_year_end = models.DateField(verbose_name=_("Financial Year End"))
    
    # Reporting
    default_report_period = models.CharField(
        max_length=20,
        choices=(
            ("MONTHLY", _("Monthly")),
            ("QUARTERLY", _("Quarterly")),
            ("YEARLY", _("Yearly")),
        ),
        default="MONTHLY",
        verbose_name=_("Default Report Period")
    )

    class Meta:
        db_table = "configuration_financial"
        verbose_name = _("Financial Configuration")
        verbose_name_plural = _("Financial Configurations")
        indexes = [
            models.Index(fields=['base_currency']),
            models.Index(fields=['chart_field']),
        ]
        unique_together = [['tenant']]

    def __str__(self):
        return f"Financial Configuration - {self.tenant}"

    @classmethod
    def get_for_tenant(cls, tenant):
        """Get or create financial config with defaults"""
        today = timezone.now().date()
        current_year = today.year
        
        # Default to April 1st - March 31st (standard fiscal year)
        if today.month < 4:
            start_date = today.replace(year=current_year - 1, month=4, day=1)
            end_date = today.replace(year=current_year, month=3, day=31)
        else:
            start_date = today.replace(month=4, day=1)
            end_date = today.replace(year=current_year + 1, month=3, day=31)
            
        obj, created = cls.objects.get_or_create(
            tenant=tenant,
            defaults={
                'financial_year_start': start_date,
                'financial_year_end': end_date
            }
        )
        return obj

    def clean(self):
        """Financial configuration validation"""
        if self.financial_year_start and self.financial_year_end:
            if self.financial_year_start >= self.financial_year_end:
                raise ValidationError({
                    'financial_year_end': _('Financial year end must be after start')
                })


class SecurityConfiguration(BaseModel):
    """
    Security and access control configuration
    """
    # Password Policy
    password_min_length = models.PositiveIntegerField(
        default=8,
        verbose_name=_("Minimum Password Length")
    )
    password_require_uppercase = models.BooleanField(
        default=True,
        verbose_name=_("Require Uppercase Letters")
    )
    password_require_lowercase = models.BooleanField(
        default=True,
        verbose_name=_("Require Lowercase Letters")
    )
    password_require_numbers = models.BooleanField(
        default=True,
        verbose_name=_("Require Numbers")
    )
    password_require_symbols = models.BooleanField(
        default=True,
        verbose_name=_("Require Symbols")
    )
    password_expiry_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_("Password Expiry (Days)")
    )
    password_history_count = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Password History Count")
    )
    
    # Session Management
    session_timeout_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Session Timeout (Minutes)")
    )
    max_concurrent_sessions = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Maximum Concurrent Sessions")
    )
    force_logout_on_password_change = models.BooleanField(
        default=True,
        verbose_name=_("Force Logout on Password Change")
    )
    
    # Login Security
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Maximum Login Attempts")
    )
    lockout_duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Account Lockout Duration (Minutes)")
    )
    require_2fa = models.BooleanField(
        default=False,
        verbose_name=_("Require Two-Factor Authentication")
    )
    allowed_2fa_methods = models.TextField(
        blank=True,
        verbose_name=_("Allowed 2FA Methods"),
        help_text=_("Comma-separated list of 2FA methods")
    )
    
    # IP Security
    ip_whitelist = models.TextField(
        blank=True,
        verbose_name=_("IP Whitelist"),
        help_text=_("Comma-separated list of allowed IP addresses")
    )
    ip_blacklist = models.TextField(
        blank=True,
        verbose_name=_("IP Blacklist"),
        help_text=_("Comma-separated list of blocked IP addresses")
    )
    enable_ip_restriction = models.BooleanField(
        default=False,
        verbose_name=_("Enable IP Restrictions")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Data Security
    data_encryption_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Data Encryption Enabled")
    )
    auto_logout_on_inactivity = models.BooleanField(
        default=True,
        verbose_name=_("Auto Logout on Inactivity")
    )
    audit_log_retention_days = models.PositiveIntegerField(
        default=365,
        verbose_name=_("Audit Log Retention (Days)")
    )
    
    # API Security
    api_rate_limit = models.PositiveIntegerField(
        default=1000,
        verbose_name=_("API Rate Limit (requests per hour)")
    )
    api_key_expiry_days = models.PositiveIntegerField(
        default=365,
        verbose_name=_("API Key Expiry (Days)")
    )

    class Meta:
        db_table = "configuration_security"
        verbose_name = _("Security Configuration")
        verbose_name_plural = _("Security Configurations")
        unique_together = [['tenant']]
        indexes = [
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"Security Configuration - {self.tenant}"

    @classmethod
    def get_for_tenant(cls, tenant):
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj

    def clean(self):
        """Security configuration validation"""
        if self.password_min_length < 6:
            raise ValidationError({
                'password_min_length': _('Minimum password length must be at least 6 characters')
            })


class NotificationConfiguration(BaseModel):
    """
    Notification and communication system configuration
    """
    # Email Configuration
    email_enabled = models.BooleanField(default=True, verbose_name=_("Email Enabled"))
    email_host = models.CharField(max_length=200, blank=True, verbose_name=_("Email Host"))
    email_port = models.PositiveIntegerField(default=587, verbose_name=_("Email Port"))
    email_username = models.CharField(max_length=200, blank=True, verbose_name=_("Email Username"))
    email_password = EncryptedCharField(max_length=500, blank=True, verbose_name=_("Email Password"))
    email_use_tls = models.BooleanField(default=True, verbose_name=_("Use TLS"))
    email_from_address = models.EmailField(blank=True, verbose_name=_("From Email Address"))
    email_from_name = models.CharField(max_length=200, blank=True, verbose_name=_("From Name"))
    
    # SMS Configuration
    sms_enabled = models.BooleanField(default=False, verbose_name=_("SMS Enabled"))
    sms_provider = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("SMS Provider")
    )
    sms_api_key = EncryptedCharField(max_length=500, blank=True, verbose_name=_("SMS API Key"))
    sms_api_secret = EncryptedCharField(max_length=500, blank=True, verbose_name=_("SMS API Secret"))
    sms_from_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("SMS From Number")
    )
    
    # Push Notification Configuration
    push_enabled = models.BooleanField(default=False, verbose_name=_("Push Notifications Enabled"))
    push_provider = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Push Provider")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # WhatsApp Configuration
    whatsapp_enabled = models.BooleanField(default=False, verbose_name=_("WhatsApp Enabled"))
    whatsapp_business_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("WhatsApp Business ID")
    )
    whatsapp_access_token = EncryptedCharField(
        max_length=500,
        blank=True,
        verbose_name=_("WhatsApp Access Token")
    )
    
    # Notification Preferences
    default_notification_channels = models.TextField(
        blank=True,
        verbose_name=_("Default Notification Channels"),
        help_text=_("Comma-separated list of channels: EMAIL,SMS,PUSH,WHATSAPP")
    )
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
    
    # Template Configuration
    default_email_template = models.TextField(
        blank=True,
        verbose_name=_("Default Email Template")
    )
    default_sms_template = models.TextField(
        blank=True,
        verbose_name=_("Default SMS Template")
    )

    class Meta:
        db_table = "configuration_notification"
        verbose_name = _("Notification Configuration")
        verbose_name_plural = _("Notification Configurations")
        unique_together = [['tenant']]
        indexes = [
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"Notification Configuration - {self.tenant}"

    @classmethod
    def get_for_tenant(cls, tenant):
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj

    def clean(self):
        """Notification configuration validation"""
        if self.email_enabled and not all([self.email_host, self.email_username]):
            raise ValidationError({
                'email_host': _('Email host and username are required when email is enabled')
            })


class AppearanceConfiguration(BaseModel):
    """
    System appearance and branding configuration
    """
    # Branding
    institution_name = models.CharField(
        max_length=200,
        default="Educational Institution",
        verbose_name=_("Institution Name")
    )
    institution_logo = models.ImageField(
        upload_to='configuration/branding/',
        null=True,
        blank=True,
        verbose_name=_("Institution Logo")
    )
    institution_favicon = models.ImageField(
        upload_to='configuration/branding/',
        null=True,
        blank=True,
        verbose_name=_("Favicon")
    )
    primary_color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name=_("Primary Color")
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#1E40AF",
        verbose_name=_("Secondary Color")
    )
    accent_color = models.CharField(
        max_length=7,
        default="#10B981",
        verbose_name=_("Accent Color")
    )
    
    # Theme
    theme_mode = models.CharField(
        max_length=20,
        choices=(
            ("LIGHT", _("Light")),
            ("DARK", _("Dark")),
            ("AUTO", _("Auto")),
        ),
        default="LIGHT",
        verbose_name=_("Theme Mode")
    )
    custom_css = models.TextField(
        blank=True,
        verbose_name=_("Custom CSS")
    )
    custom_js = models.TextField(
        blank=True,
        verbose_name=_("Custom JavaScript")
    )
    
    # Layout
    layout_type = models.CharField(
        max_length=20,
        choices=(
            ("SIDEBAR", _("Sidebar Layout")),
            ("TOPNAV", _("Top Navigation")),
            ("COMPACT", _("Compact")),
        ),
        default="SIDEBAR",
        verbose_name=_("Layout Type")
    )
    sidebar_collapsed = models.BooleanField(
        default=False,
        verbose_name=_("Sidebar Collapsed by Default")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Login Page
    login_background = models.ImageField(
        upload_to='configuration/login/',
        null=True,
        blank=True,
        verbose_name=_("Login Background Image")
    )
    login_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Login Page Title")
    )
    login_subtitle = models.TextField(
        blank=True,
        verbose_name=_("Login Page Subtitle")
    )
    
    # Dashboard
    default_dashboard_view = models.CharField(
        max_length=50,
        default="OVERVIEW",
        verbose_name=_("Default Dashboard View")
    )
    
    # Footer
    footer_text = models.TextField(
        blank=True,
        verbose_name=_("Footer Text")
    )
    show_version_in_footer = models.BooleanField(
        default=True,
        verbose_name=_("Show Version in Footer")
    )

    class Meta:
        db_table = "configuration_appearance"
        verbose_name = _("Appearance Configuration")
        verbose_name_plural = _("Appearance Configurations")
        unique_together = [['tenant']]
        indexes = [
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"Appearance Configuration - {self.tenant}"

    @classmethod
    def get_for_tenant(cls, tenant):
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj


class IntegrationConfiguration(BaseModel):
    """
    Third-party integrations and API configurations
    """
    INTEGRATION_STATUS_CHOICES = (
        ("ACTIVE", _("Active")),
        ("INACTIVE", _("Inactive")),
        ("CONFIGURING", _("Configuring")),
        ("ERROR", _("Error")),
    )

    # Integration Metadata
    name = models.CharField(max_length=200, verbose_name=_("Integration Name"))
    provider = models.CharField(max_length=100, verbose_name=_("Provider"))
    integration_type = models.CharField(
        max_length=50,
        verbose_name=_("Integration Type")
    )
    version = models.CharField(max_length=20, default="1.0", verbose_name=_("Version"))
    
    # Configuration
    is_enabled = models.BooleanField(default=False, verbose_name=_("Is Enabled"))
    status = models.CharField(
        max_length=20,
        choices=INTEGRATION_STATUS_CHOICES,
        default="INACTIVE",
        verbose_name=_("Status")
    )
    config_data = models.TextField(
        blank=True,
        verbose_name=_("Configuration Data")
    )
    api_keys = models.TextField(
        blank=True,
        verbose_name=_("API Keys and Secrets")
    )
    
    # Authentication
    auth_type = models.CharField(
        max_length=50,
        choices=(
            ("API_KEY", _("API Key")),
            ("OAUTH2", _("OAuth 2.0")),
            ("BASIC", _("Basic Auth")),
            ("TOKEN", _("Token")),
        ),
        default="API_KEY",
        verbose_name=_("Authentication Type")
    )
    
    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Endpoints
    base_url = models.URLField(blank=True, verbose_name=_("Base URL"))
    endpoints = models.TextField(
        blank=True,
        verbose_name=_("API Endpoints")
    )
    
    # Webhooks
    webhook_url = models.URLField(blank=True, verbose_name=_("Webhook URL"))
    webhook_secret = EncryptedCharField(
        max_length=500,
        blank=True,
        verbose_name=_("Webhook Secret")
    )
    webhook_events = models.TextField(
        blank=True,
        verbose_name=_("Webhook Events")
    )
    
    # Rate Limiting
    rate_limit = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Rate Limit (requests per minute)")
    )
    retry_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Retry Attempts")
    )
    
    # Monitoring
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Sync")
    )
    sync_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Last Sync Status")
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message")
    )
    health_check_url = models.URLField(
        blank=True,
        verbose_name=_("Health Check URL")
    )

    class Meta:
        db_table = "configuration_integration"
        ordering = ["name", "provider"]
        verbose_name = _("Integration Configuration")
        verbose_name_plural = _("Integration Configurations")
        unique_together = [['name', 'tenant']]
        indexes = [
            models.Index(fields=['integration_type', 'is_enabled']),
            models.Index(fields=['status', 'last_sync']),
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def test_connection(self):
        """Test integration connection"""
        # Implementation depends on integration type
        pass

    def sync_data(self):
        """Sync data with integration"""
        # Implementation depends on integration type
        pass

    @classmethod
    def get_integration(cls, name, tenant):
        return cls.objects.filter(name=name, tenant=tenant).first()


class BackupConfiguration(BaseModel):
    """
    Backup and recovery system configuration
    """
    # Backup Settings
    auto_backup_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Auto Backup Enabled")
    )
    backup_frequency = models.CharField(
        max_length=20,
        choices=(
            ("DAILY", _("Daily")),
            ("WEEKLY", _("Weekly")),
            ("MONTHLY", _("Monthly")),
        ),
        default="DAILY",
        verbose_name=_("Backup Frequency")
    )
    backup_time = models.TimeField(
        default="02:00",
        verbose_name=_("Backup Time")
    )
    retain_backup_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Retain Backups (Days)")
    )
    max_backup_files = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Maximum Backup Files")
    )

    # Storage Configuration
    storage_type = models.CharField(
        max_length=20,
        choices=(
            ("LOCAL", _("Local Storage")),
            ("AWS_S3", _("Amazon S3")),
            ("GOOGLE_CLOUD", _("Google Cloud Storage")),
            ("AZURE", _("Azure Blob Storage")),
        ),
        default="LOCAL",
        verbose_name=_("Storage Type")
    )
    backup_path = models.CharField(
        max_length=500,
        default="/backups/",
        verbose_name=_("Backup Path")
    )

    # What to Backup
    backup_databases = models.BooleanField(
        default=True,
        verbose_name=_("Backup Databases")
    )
    backup_media = models.BooleanField(
        default=True,
        verbose_name=_("Backup Media Files")
    )
    backup_code = models.BooleanField(
        default=False,
        verbose_name=_("Backup Application Code")
    )
    excluded_tables = models.TextField(
        blank=True,
        verbose_name=_("Excluded Database Tables"),
        help_text=_("Comma-separated list of table names")
    )

    # Encryption
    encrypt_backups = models.BooleanField(
        default=True,
        verbose_name=_("Encrypt Backups")
    )
    encryption_key = EncryptedCharField(
        max_length=500,
        blank=True,
        verbose_name=_("Encryption Key")
    )

    chart_field = models.CharField(
        max_length=20,
        choices=[
            ('BAR', _('Bar Chart')),
            ('PIE', _('Pie Chart')),
            ('LINE', _('Line Chart')),
            ('TABLE', _('Data Table')),
        ],
        default='TABLE',
        verbose_name=_("Chart Type")
    )
    
    # Notification
    notify_on_backup = models.BooleanField(
        default=True,
        verbose_name=_("Notify on Backup Completion")
    )
    notify_on_failure = models.BooleanField(
        default=True,
        verbose_name=_("Notify on Backup Failure")
    )
    notification_emails = models.TextField(
        blank=True,
        verbose_name=_("Notification Emails"),
        help_text=_("Comma-separated list of email addresses")
    )

    # Monitoring
    last_backup = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Backup")
    )
    last_backup_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Last Backup Status")
    )
    last_backup_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Last Backup Size (bytes)")
    )
    next_backup = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Next Scheduled Backup")
    )

    class Meta:
        db_table = "configuration_backup"
        verbose_name = _("Backup Configuration")
        verbose_name_plural = _("Backup Configurations")
        unique_together = [['tenant']]
        indexes = [
            models.Index(fields=["auto_backup_enabled"]),
            models.Index(fields=["backup_frequency"]),
            models.Index(fields=["storage_type"]),
            models.Index(fields=['chart_field']),
        ]

    def __str__(self):
        return f"Backup Configuration - {self.tenant}"

    # ---------------------------
    # Validation
    # ---------------------------
    def clean(self):
        if self.encrypt_backups and not self.encryption_key:
            raise ValidationError({
                'encryption_key': _("Encryption key is required when encryption is enabled.")
            })

    # ---------------------------
    # Logic: Calculate Next Backup
    # ---------------------------
    def calculate_next_backup(self):
        """
        Calculates the next backup datetime based on last backup and frequency
        """
        from datetime import timedelta, datetime

        if not self.last_backup:
            # First-time: schedule for today's date with backup_time
            today = datetime.now().replace(
                hour=self.backup_time.hour,
                minute=self.backup_time.minute,
                second=0,
                microsecond=0
            )
            return today

        # Frequency logic
        if self.backup_frequency == "DAILY":
            next_backup = self.last_backup + timedelta(days=1)
        elif self.backup_frequency == "WEEKLY":
            next_backup = self.last_backup + timedelta(weeks=1)
        else:  # MONTHLY
            next_backup = self.last_backup + timedelta(days=30)

        # Replace only time
        next_backup = next_backup.replace(
            hour=self.backup_time.hour,
            minute=self.backup_time.minute,
            second=0,
            microsecond=0
        )

        return next_backup

    # ---------------------------
    # Auto Assign Next Backup on Save
    # ---------------------------
    def save(self, *args, **kwargs):
        self.next_backup = self.calculate_next_backup()
        super().save(*args, **kwargs)

    # ---------------------------
    # Common Pattern: Get Config for Tenant
    # ---------------------------
    @classmethod
    def get_for_tenant(cls, tenant):
        obj, created = cls.objects.get_or_create(tenant=tenant)
        return obj