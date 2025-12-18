import json
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model

# Import core base models
from apps.core.models import BaseModel, UUIDModel, TimeStampedModel, TenantAwareModel
from apps.academics.models import AcademicYear, SchoolClass, Subject
from apps.students.models import Student

User = get_user_model()


"""
Audit Analysis and Reporting Models
"""


class AuditAnalysisReport(UUIDModel, TimeStampedModel, TenantAwareModel):
    """
    Generated audit analysis reports
    """
    REPORT_TYPES = [
        ('DAILY_SUMMARY', 'Daily Activity Summary'),
        ('WEEKLY_COMPLIANCE', 'Weekly Compliance Report'),
        ('MONTHLY_AUDIT', 'Monthly Audit Trail'),
        ('SECURITY_REVIEW', 'Security Review'),
        ('USER_ACTIVITY', 'User Activity Report'),
        ('TENANT_ACTIVITY', 'Tenant Activity Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    FORMATS = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('HTML', 'HTML'),
    ]
    
    # Filters
    FILTER_CHOICES = [
        ('ALL', 'All Activities'),
        ('LOGIN_ONLY', 'Login Activities'),
        ('SECURITY_EVENTS', 'Security Events'),
        ('DATA_CHANGES', 'Data Changes'),
        ('FAILED_ACTIONS', 'Failed Actions'),
        ('USER_SPECIFIC', 'Specific User'),
        ('TENANT_WIDE', 'Tenant Wide'),
        ('COMPLIANCE_ONLY', 'Compliance Events'),
        ('CUSTOM', 'Custom Filter'),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMATS, default='PDF')
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    filter_type = models.CharField(
        max_length=30,
        choices=FILTER_CHOICES,
        default='ALL',
        verbose_name=_("Filter Type")
    )

    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Generated content
    file_path = models.FileField(upload_to='audit_reports/', null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(null=True, blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_audit_reports'
    )
    generation_time = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    
    # Retention
    expires_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'report_type', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['generated_by', 'created_at']),
        ]
        verbose_name = "Audit Analysis Report"
        verbose_name_plural = "Audit Analysis Reports"
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'TABLE',
                'options': {
                    'title': self.name,
                    'show_legend': True,
                    'animate': True,
                    'colors': ['#007bff', '#28a745', '#dc3545', '#ffc107']
                },
                'data': {
                    'labels': [],
                    'datasets': []
                }
            }
        super().save(*args, **kwargs)


class AuditPattern(UUIDModel, TimeStampedModel, TenantAwareModel):
    """
    Detected patterns and anomalies in audit logs
    """
    PATTERN_TYPES = [
        ('SECURITY_THREAT', 'Security Threat'),
        ('ANOMALY', 'Anomaly'),
        ('TREND', 'Trend'),
        ('COMPLIANCE_ISSUE', 'Compliance Issue'),
        ('PERFORMANCE_ISSUE', 'Performance Issue'),
        ('BEHAVIOR_PATTERN', 'Behavior Pattern'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    name = models.CharField(max_length=200)
    pattern_type = models.CharField(max_length=50, choices=PATTERN_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='MEDIUM')
    
    # Detection criteria
    detection_rules = models.JSONField(default=dict, blank=True)
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    threshold = models.FloatField(default=1.0)
    time_window_minutes = models.IntegerField(default=60)
    
    # Statistics
    occurrence_count = models.IntegerField(default=0)
    first_detected = models.DateTimeField(null=True, blank=True)
    last_detected = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_auto_remediate = models.BooleanField(default=False)
    
    # Actions
    RECOMMENDED_ACTION_CHOICES = [
        ('NO_ACTION', 'No Action Required'),
        ('NOTIFY_ADMIN', 'Notify Administrator'),
        ('NOTIFY_SECURITY', 'Notify Security Team'),
        ('LOCK_USER', 'Lock User Account'),
        ('FORCE_LOGOUT', 'Force Logout'),
        ('RESET_PASSWORD', 'Force Password Reset'),
        ('ENABLE_MFA', 'Enable Multi-Factor Authentication'),
        ('BLOCK_IP', 'Block IP Address'),
        ('ESCALATE', 'Escalate to Management'),
        ('GENERATE_REPORT', 'Generate Detailed Report'),
        ('CUSTOM', 'Custom Action'),
    ]

    recommended_action = models.CharField(
        max_length=30,
        choices=RECOMMENDED_ACTION_CHOICES,
        default='NO_ACTION',
        verbose_name=_("Recommended Action")
    )
        
    class Meta:
        ordering = ['-severity', '-last_detected']
        indexes = [
            models.Index(fields=['pattern_type', 'severity']),
            models.Index(fields=['is_active', 'last_detected']),
        ]
        verbose_name = "Audit Pattern"
        verbose_name_plural = "Audit Patterns"
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'BAR',
                'options': {
                    'title': f"{self.name} Pattern",
                    'x_axis_label': 'Time',
                    'y_axis_label': 'Occurrences',
                    'show_legend': True,
                    'stacked': False,
                    'colors': self._get_severity_colors()
                },
                'data': {
                    'labels': [],
                    'datasets': []
                }
            }
        super().save(*args, **kwargs)
    
    def _get_severity_colors(self):
        """Get colors based on severity"""
        severity_colors = {
            'LOW': ['#28a745'],
            'MEDIUM': ['#ffc107'],
            'HIGH': ['#fd7e14'],
            'CRITICAL': ['#dc3545']
        }
        return severity_colors.get(self.severity, ['#007bff'])


class AuditAlert(UUIDModel, TimeStampedModel, TenantAwareModel):
    """
    Alerts generated from audit pattern detection
    """
    ALERT_TYPES = [
        ('REAL_TIME', 'Real-time Alert'),
        ('DAILY_SUMMARY', 'Daily Summary'),
        ('WEEKLY_REVIEW', 'Weekly Review'),
        ('MONTHLY_REPORT', 'Monthly Report'),
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_REVIEW', 'In Review'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    ]
    
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    pattern = models.ForeignKey(
        AuditPattern,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Related audit logs
    related_logs = models.ManyToManyField('core.AuditLog', blank=True)
    
    # Severity and status
    severity = models.CharField(max_length=20, choices=AuditPattern.SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    # Assignment and resolution
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_alerts'
    )
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    
    # Notification
    is_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Auto-remediation
    auto_remediation_attempted = models.BooleanField(default=False)
    auto_remediation_successful = models.BooleanField(default=False)
    auto_remediation_notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at', 'severity']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['pattern', 'created_at']),
        ]
        verbose_name = "Audit Alert"
        verbose_name_plural = "Audit Alerts"
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'TABLE',
                'options': {
                    'title': self.title,
                    'show_timeline': True,
                    'show_severity': True,
                    'group_by': 'category',
                    'colors': self._get_severity_colors()
                },
                'data': {
                    'columns': ['Time', 'Event', 'Severity', 'Details'],
                    'rows': []
                }
            }
        super().save(*args, **kwargs)
    
    def _get_severity_colors(self):
        """Get colors based on severity"""
        severity_colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        return severity_colors.get(self.severity, '#007bff')


class AuditDashboard(UUIDModel, TimeStampedModel, TenantAwareModel):
    """
    Configurable audit dashboards
    """
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    
    # Layout and configuration
    layout_config = models.JSONField(default=dict, blank=True)
    widget_configs = models.JSONField(default=list, blank=True)
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Access control
    is_shared = models.BooleanField(default=False)
    shared_with_users = models.ManyToManyField(User, blank=True, related_name='shared_dashboards')
    shared_with_groups = models.ManyToManyField('auth.Group', blank=True)
    
    # Default settings
    is_default = models.BooleanField(default=False)
    refresh_interval_minutes = models.IntegerField(default=5)
    
    # Owner
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        related_name='owned_dashboards'
    )
    
    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = [['tenant', 'owner', 'name']]
        verbose_name = "Audit Dashboard"
        verbose_name_plural = "Audit Dashboards"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one default dashboard per user per tenant
        if self.is_default:
            AuditDashboard.objects.filter(
                tenant=self.tenant,
                owner=self.owner,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'GRID',
                'options': {
                    'layout': 'responsive',
                    'theme': 'light',
                    'show_grid': True,
                    'widget_spacing': 10,
                    'max_columns': 4
                },
                'widgets': []
            }
        super().save(*args, **kwargs)


class AuditMetric(UUIDModel, TimeStampedModel, TenantAwareModel):
    """
    Audit metrics for monitoring and analytics
    """
    METRIC_TYPES = [
        ('COUNT', 'Count'),
        ('SUM', 'Sum'),
        ('AVERAGE', 'Average'),
        ('RATE', 'Rate'),
        ('PERCENTAGE', 'Percentage'),
        ('DURATION', 'Duration'),
    ]
    
    name = models.CharField(max_length=200)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    description = models.TextField(null=True, blank=True)
    
    # Query configuration
    query_filter = models.JSONField(default=dict, blank=True)
    group_by_fields = models.JSONField(default=list, blank=True)
    aggregation_field = models.CharField(max_length=100, null=True, blank=True)
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Schedule
    calculation_schedule = models.CharField(
        max_length=50,
        choices=[
            ('HOURLY', 'Hourly'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('REAL_TIME', 'Real-time'),
        ],
        default='DAILY'
    )
    
    # Thresholds for alerts
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    
    # Last calculation
    last_calculated = models.DateTimeField(null=True, blank=True)
    last_value = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['metric_type', 'calculation_schedule']),
        ]
        verbose_name = "Audit Metric"
        verbose_name_plural = "Audit Metrics"
    
    def __str__(self):
        return f"{self.name} ({self.get_metric_type_display()})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'BAR',
                'options': {
                    'title': self.name,
                    'x_axis_label': 'Time',
                    'y_axis_label': self._get_y_axis_label(),
                    'show_thresholds': True,
                    'animate': True,
                    'colors': ['#007bff', '#28a745', '#dc3545']
                },
                'thresholds': {
                    'warning': self.warning_threshold,
                    'critical': self.critical_threshold
                }
            }
        super().save(*args, **kwargs)
    
    def _get_y_axis_label(self):
        """Get Y axis label based on metric type"""
        labels = {
            'COUNT': 'Count',
            'SUM': 'Total',
            'AVERAGE': 'Average',
            'RATE': 'Rate (per hour)',
            'PERCENTAGE': 'Percentage (%)',
            'DURATION': 'Duration (seconds)'
        }
        return labels.get(self.metric_type, 'Value')


class AuditMetricValue(UUIDModel, TimeStampedModel):
    """
    Historical values for audit metrics
    """
    metric = models.ForeignKey(
        AuditMetric,
        on_delete=models.CASCADE,
        related_name='values'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Value and time
    timestamp = models.DateTimeField(db_index=True)
    value = models.FloatField()
    
    # Aggregation period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    period_type = models.CharField(max_length=20)  # hour, day, week, month
    
    # Metadata
    sample_count = models.IntegerField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    avg_value = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric', 'timestamp']),
            models.Index(fields=['tenant', 'metric', 'timestamp']),
            models.Index(fields=['period_type', 'timestamp']),
        ]
        verbose_name = "Audit Metric Value"
        verbose_name_plural = "Audit Metric Values"
    
    def __str__(self):
        return f"{self.metric.name}: {self.value} @ {self.timestamp}"


"""
Analytics and Reporting Models
"""


class DataSource(BaseModel):
    """
    Data sources for analytics and reporting
    """
    SOURCE_TYPE_CHOICES = (
        ("DATABASE", _("Database")),
        ("API", _("API")),
        ("FILE", _("File")),
        ("STREAM", _("Real-time Stream")),
        ("EXTERNAL", _("External System")),
    )

    STATUS_CHOICES = (
        ("ACTIVE", _("Active")),
        ("INACTIVE", _("Inactive")),
        ("ERROR", _("Error")),
        ("MAINTENANCE", _("Maintenance")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Data Source Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        verbose_name=_("Source Type")
    )
    
    # Connection Configuration
    connection_string = models.TextField(
        blank=True,
        verbose_name=_("Connection String")
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Configuration")
    )
    credentials = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Credentials")
    )
    
    # Status and Health
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name=_("Status")
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Sync")
    )
    sync_frequency = models.CharField(
        max_length=20,
        choices=(
            ("REAL_TIME", _("Real-time")),
            ("HOURLY", _("Hourly")),
            ("DAILY", _("Daily")),
            ("WEEKLY", _("Weekly")),
            ("MONTHLY", _("Monthly")),
        ),
        default="DAILY",
        verbose_name=_("Sync Frequency")
    )
    
    # Data Quality
    data_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Data Quality Score")
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Error Count")
    )
    last_error = models.TextField(
        blank=True,
        verbose_name=_("Last Error Message")
    )
    
    # Metadata
    schema_version = models.CharField(
        max_length=20,
        default="1.0",
        verbose_name=_("Schema Version")
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Is Public")
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for health visualization")
    )

    class Meta:
        db_table = "analytics_data_source"
        ordering = ["name", "source_type"]
        verbose_name = _("Data Source")
        verbose_name_plural = _("Data Sources")
        indexes = [
            models.Index(fields=['source_type', 'status']),
            models.Index(fields=['status', 'last_sync']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'KPI_CARD',
                'options': {
                    'title': f"{self.name} Health",
                    'show_status': True,
                    'show_last_sync': True,
                    'show_quality_score': True,
                    'status_colors': {
                        'ACTIVE': '#28a745',
                        'INACTIVE': '#6c757d',
                        'ERROR': '#dc3545',
                        'MAINTENANCE': '#ffc107'
                    }
                },
                'metrics': {
                    'quality_score': float(self.data_quality_score) if self.data_quality_score else 0,
                    'error_count': self.error_count,
                    'status': self.status
                }
            }
        super().save(*args, **kwargs)

    def test_connection(self):
        """Test data source connection"""
        # Implementation depends on source type
        pass

    def get_data_quality_metrics(self):
        """Calculate data quality metrics"""
        # Implementation for data quality assessment
        pass


class KPIModel(BaseModel):
    """
    Key Performance Indicators definition and tracking
    """
    CATEGORY_CHOICES = (
        ("ACADEMIC", _("Academic")),
        ("FINANCIAL", _("Financial")),
        ("OPERATIONAL", _("Operational")),
        ("STUDENT", _("Student Performance")),
        ("STAFF", _("Staff Performance")),
        ("INFRASTRUCTURE", _("Infrastructure")),
        ("CUSTOM", _("Custom")),
    )

    FREQUENCY_CHOICES = (
        ("REAL_TIME", _("Real-time")),
        ("HOURLY", _("Hourly")),
        ("DAILY", _("Daily")),
        ("WEEKLY", _("Weekly")),
        ("MONTHLY", _("Monthly")),
        ("QUARTERLY", _("Quarterly")),
        ("YEARLY", _("Yearly")),
    )

    DIRECTION_CHOICES = (
        ("ASCENDING", _("Higher is Better")),
        ("DESCENDING", _("Lower is Better")),
        ("NEUTRAL", _("Neutral")),
    )

    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("KPI Name"))
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("KPI Code")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Category")
    )
    
    # Calculation Configuration
    calculation_query = models.TextField(
        blank=True,
        verbose_name=_("Calculation Query/Script")
    )
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="kpis",
        verbose_name=_("Data Source")
    )
    calculation_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default="DAILY",
        verbose_name=_("Calculation Frequency")
    )
    
    # Target and Thresholds
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Target Value")
    )
    min_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Minimum Threshold")
    )
    max_threshold = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Maximum Threshold")
    )
    direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
        default="ASCENDING",
        verbose_name=_("Optimization Direction")
    )
    
    # Units and Formatting
    unit = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Unit of Measurement")
    )
    format_string = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Display Format")
    )
    decimal_places = models.PositiveIntegerField(
        default=2,
        verbose_name=_("Decimal Places")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    last_calculated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Calculated")
    )
    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Current Value")
    )
    
    # Visualization
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    color_scheme = models.CharField(
        max_length=50,
        default="blue",
        verbose_name=_("Color Scheme")
    )

    class Meta:
        db_table = "analytics_kpi"
        ordering = ["category", "name"]
        verbose_name = _("KPI")
        verbose_name_plural = _("KPIs")
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['category', 'calculation_frequency']),
            models.Index(fields=['is_active', 'last_calculated']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'NUMBER',
                'options': {
                    'title': self.name,
                    'show_target': self.target_value is not None,
                    'show_thresholds': self.min_threshold is not None or self.max_threshold is not None,
                    'format': self.format_string or f"{{value:.{self.decimal_places}f}} {self.unit}",
                    'color_scheme': self.color_scheme,
                    'animate': True
                },
                'targets': {
                    'min': float(self.min_threshold) if self.min_threshold else None,
                    'max': float(self.max_threshold) if self.max_threshold else None,
                    'target': float(self.target_value) if self.target_value else None
                }
            }
        super().save(*args, **kwargs)

    @property
    def performance_status(self):
        """Calculate performance status based on current value and targets"""
        if self.current_value is None:
            return "UNKNOWN"
        
        if self.target_value is not None:
            if self.direction == "ASCENDING":
                if self.current_value >= self.target_value:
                    return "EXCELLENT"
                elif self.current_value >= self.target_value * 0.8:
                    return "GOOD"
                else:
                    return "NEEDS_IMPROVEMENT"
            else:  # DESCENDING
                if self.current_value <= self.target_value:
                    return "EXCELLENT"
                elif self.current_value <= self.target_value * 1.2:
                    return "GOOD"
                else:
                    return "NEEDS_IMPROVEMENT"
        return "NEUTRAL"

    def calculate_value(self):
        """Calculate current KPI value"""
        # Implementation depends on calculation_query and data_source
        pass

    def get_trend_data(self, period="30d"):
        """Get historical trend data for KPI"""
        # Implementation for trend analysis
        pass


class KPIValue(BaseModel):
    """
    Historical values for KPIs
    """
    kpi = models.ForeignKey(
        KPIModel,
        on_delete=models.CASCADE,
        related_name="historical_values",
        verbose_name=_("KPI")
    )
    
    # Value and Period
    value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name=_("KPI Value")
    )
    period_start = models.DateTimeField(verbose_name=_("Period Start"))
    period_end = models.DateTimeField(verbose_name=_("Period End"))
    period_type = models.CharField(
        max_length=20,
        choices=(
            ("HOUR", _("Hour")),
            ("DAY", _("Day")),
            ("WEEK", _("Week")),
            ("MONTH", _("Month")),
            ("QUARTER", _("Quarter")),
            ("YEAR", _("Year")),
        ),
        verbose_name=_("Period Type")
    )
    
    # Context
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Academic Year")
    )
    class_name = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Class")
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Subject")
    )
    
    # Metadata
    data_points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Data Points Count")
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Confidence Level")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "analytics_kpi_value"
        ordering = ["kpi", "-period_end"]
        verbose_name = _("KPI Value")
        verbose_name_plural = _("KPI Values")
        indexes = [
            models.Index(fields=['kpi', 'period_end']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['academic_year', 'class_name']),
        ]
        unique_together = [['kpi', 'period_start', 'period_end']]

    def __str__(self):
        return f"{self.kpi.name}: {self.value} ({self.period_start} - {self.period_end})"

    @property
    def period_duration(self):
        """Calculate period duration"""
        return self.period_end - self.period_start


class Report(BaseModel):
    """
    Analytics reports and dashboards
    """
    REPORT_TYPE_CHOICES = (
        ("DASHBOARD", _("Dashboard")),
        ("TABULAR", _("Tabular Report")),
        ("VISUALIZATION", _("Visualization")),
        ("SUMMARY", _("Summary Report")),
        ("DETAILED", _("Detailed Report")),
        ("COMPARATIVE", _("Comparative Analysis")),
    )

    ACCESS_LEVEL_CHOICES = (
        ("PUBLIC", _("Public")),
        ("PRIVATE", _("Private")),
        ("ROLE_BASED", _("Role Based")),
        ("DEPARTMENT", _("Department")),
    )

    # Basic Information
    title = models.CharField(max_length=200, verbose_name=_("Report Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_("Report Type")
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Report Configuration")
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Default Filters")
    )
    parameters = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Report Parameters")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Access Control
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default="PRIVATE",
        verbose_name=_("Access Level")
    )
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Allowed Roles")
    )
    is_scheduled = models.BooleanField(
        default=False,
        verbose_name=_("Is Scheduled")
    )
    
    # Scheduling
    schedule_frequency = models.CharField(
        max_length=20,
        choices=(
            ("DAILY", _("Daily")),
            ("WEEKLY", _("Weekly")),
            ("MONTHLY", _("Monthly")),
            ("QUARTERLY", _("Quarterly")),
            ("YEARLY", _("Yearly")),
        ),
        blank=True,
        verbose_name=_("Schedule Frequency")
    )
    schedule_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Schedule Time")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_template = models.BooleanField(
        default=False,
        verbose_name=_("Is Template")
    )
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Generated")
    )
    
    # Performance
    generation_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Last Generation Time")
    )
    data_source_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Data Source Count")
    )

    class Meta:
        db_table = "analytics_report"
        ordering = ["title", "report_type"]
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        indexes = [
            models.Index(fields=['report_type', 'is_active']),
            models.Index(fields=['access_level', 'is_template']),
            models.Index(fields=['is_scheduled', 'schedule_frequency']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'TABLE',
                'options': {
                    'title': self.title,
                    'show_filters': bool(self.filters),
                    'exportable': True,
                    'searchable': True,
                    'paginate': True,
                    'page_size': 20,
                    'sortable': True
                },
                'columns': [],
                'data': []
            }
        super().save(*args, **kwargs)

    def generate_report(self, parameters=None):
        """Generate report with given parameters"""
        # Implementation depends on report type and configuration
        pass

    def get_report_url(self):
        """Get report URL"""
        return reverse('analytics:report_view', kwargs={'pk': self.pk})

    def schedule_generation(self):
        """Schedule report generation"""
        if self.is_scheduled:
            # Implementation for scheduling
            pass


class ReportExecution(BaseModel):
    """
    Report execution history and results
    """
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("RUNNING", _("Running")),
        ("COMPLETED", _("Completed")),
        ("FAILED", _("Failed")),
        ("CANCELLED", _("Cancelled")),
    )

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="executions",
        verbose_name=_("Report")
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        related_name="report_executions",
        verbose_name=_("Executed By")
    )
    
    # Execution Details
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Execution Parameters")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for result visualization")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    
    # Timing
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Started At")
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed At")
    )
    execution_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Execution Duration")
    )
    
    # Results
    result_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Result Data")
    )
    result_size = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Result Size (bytes)")
    )
    row_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Row Count")
    )
    
    # Error Handling
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message")
    )
    stack_trace = models.TextField(
        blank=True,
        verbose_name=_("Stack Trace")
    )
    
    # Output
    output_format = models.CharField(
        max_length=20,
        choices=(
            ("JSON", _("JSON")),
            ("CSV", _("CSV")),
            ("EXCEL", _("Excel")),
            ("PDF", _("PDF")),
            ("HTML", _("HTML")),
        ),
        default="JSON",
        verbose_name=_("Output Format")
    )
    output_file = models.FileField(
        upload_to='analytics/reports/',
        null=True,
        blank=True,
        verbose_name=_("Output File")
    )

    class Meta:
        db_table = "analytics_report_execution"
        ordering = ["-started_at", "report"]
        verbose_name = _("Report Execution")
        verbose_name_plural = _("Report Executions")
        indexes = [
            models.Index(fields=['report', 'started_at']),
            models.Index(fields=['executed_by', 'status']),
            models.Index(fields=['status', 'completed_at']),
        ]

    def __str__(self):
        return f"Execution of {self.report.title} by {self.executed_by}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'TABLE',
                'options': {
                    'title': f"Results: {self.report.title}",
                    'show_execution_info': True,
                    'show_status': True,
                    'exportable': True,
                    'status_colors': {
                        'COMPLETED': '#28a745',
                        'FAILED': '#dc3545',
                        'RUNNING': '#007bff',
                        'PENDING': '#6c757d',
                        'CANCELLED': '#ffc107'
                    }
                },
                'execution_info': {
                    'started_at': self.started_at.isoformat() if self.started_at else None,
                    'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                    'duration': str(self.execution_duration) if self.execution_duration else None,
                    'status': self.status
                }
            }
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return self.status == "COMPLETED"

    @property
    def is_failed(self):
        return self.status == "FAILED"

    def start_execution(self):
        """Start report execution"""
        self.status = "RUNNING"
        self.started_at = timezone.now()
        self.save()

    def complete_execution(self, result_data=None):
        """Complete report execution"""
        self.status = "COMPLETED"
        self.completed_at = timezone.now()
        self.execution_duration = self.completed_at - self.started_at
        if result_data:
            self.result_data = result_data
            self.row_count = len(result_data) if isinstance(result_data, list) else 0
        self.save()

    def fail_execution(self, error_message, stack_trace=""):
        """Mark execution as failed"""
        self.status = "FAILED"
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.save()


class Dashboard(BaseModel):
    """
    Interactive analytics dashboards
    """
    LAYOUT_CHOICES = (
        ("GRID", _("Grid Layout")),
        ("FLEX", _("Flexible Layout")),
        ("SINGLE", _("Single Column")),
        ("CUSTOM", _("Custom Layout")),
    )

    # Basic Information
    title = models.CharField(max_length=200, verbose_name=_("Dashboard Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    layout_type = models.CharField(
        max_length=20,
        choices=LAYOUT_CHOICES,
        default="GRID",
        verbose_name=_("Layout Type")
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Dashboard Configuration")
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Global Filters")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for layout visualization")
    )
    
    theme = models.CharField(
        max_length=50,
        default="light",
        verbose_name=_("Theme")
    )
    
    # Access Control
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Is Public")
    )
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Allowed Roles")
    )
    is_template = models.BooleanField(
        default=False,
        verbose_name=_("Is Template")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    refresh_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Refresh Interval (seconds)")
    )
    last_refresh = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Refresh")
    )

    class Meta:
        db_table = "analytics_dashboard"
        ordering = ["title", "-created_at"]
        verbose_name = _("Dashboard")
        verbose_name_plural = _("Dashboards")
        indexes = [
            models.Index(fields=['is_active', 'is_public']),
            models.Index(fields=['layout_type', 'is_template']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'GRID',
                'options': {
                    'title': self.title,
                    'layout': self.layout_type,
                    'theme': self.theme,
                    'show_grid': True,
                    'widget_spacing': 20,
                    'max_columns': 4,
                    'responsive': True,
                    'allow_reorder': True,
                    'allow_resize': True
                },
                'widgets': []
            }
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('analytics:dashboard_view', kwargs={'pk': self.pk})

    def add_widget(self, widget_config):
        """Add widget to dashboard"""
        if 'widgets' not in self.config:
            self.config['widgets'] = []
        self.config['widgets'].append(widget_config)
        self.save()

    def refresh_data(self):
        """Refresh dashboard data"""
        self.last_refresh = timezone.now()
        self.save()


class DashboardWidget(BaseModel):
    """
    Individual widgets for dashboards
    """
    WIDGET_TYPE_CHOICES = (
        ("KPI", _("KPI Card")),
        ("CHART", _("Chart")),
        ("TABLE", _("Data Table")),
        ("HEATMAP", _("Heat Map")),
        ("MAP", _("Geographic Map")),
        ("TEXT", _("Text Widget")),
        ("FILTER", _("Filter Widget")),
    )

    CHART_TYPE_CHOICES = (
        ("LINE", _("Line Chart")),
        ("BAR", _("Bar Chart")),
        ("PIE", _("Pie Chart")),
        ("SCATTER", _("Scatter Plot")),
        ("AREA", _("Area Chart")),
        ("RADAR", _("Radar Chart")),
        ("GAUGE", _("Gauge Chart")),
    )

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="widgets",
        verbose_name=_("Dashboard")
    )
    
    # Basic Information
    title = models.CharField(max_length=200, verbose_name=_("Widget Title"))
    widget_type = models.CharField(
        max_length=20,
        choices=WIDGET_TYPE_CHOICES,
        verbose_name=_("Widget Type")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Widget Configuration")
    )
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Data Source")
    )
    kpi = models.ForeignKey(
        KPIModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("KPI")
    )
    
    # Layout
    position_x = models.PositiveIntegerField(default=0, verbose_name=_("X Position"))
    position_y = models.PositiveIntegerField(default=0, verbose_name=_("Y Position"))
    width = models.PositiveIntegerField(default=4, verbose_name=_("Width"))
    height = models.PositiveIntegerField(default=3, verbose_name=_("Height"))
    
    # Styling
    color_scheme = models.CharField(
        max_length=50,
        default="default",
        verbose_name=_("Color Scheme")
    )
    custom_css = models.TextField(
        blank=True,
        verbose_name=_("Custom CSS")
    )
    
    # Behavior
    refresh_interval = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Refresh Interval (seconds)")
    )
    is_interactive = models.BooleanField(
        default=True,
        verbose_name=_("Is Interactive")
    )
    drill_down_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Drill Down Enabled")
    )

    class Meta:
        db_table = "analytics_dashboard_widget"
        ordering = ["dashboard", "position_y", "position_x"]
        verbose_name = _("Dashboard Widget")
        verbose_name_plural = _("Dashboard Widgets")
        indexes = [
            models.Index(fields=['dashboard', 'widget_type']),
        ]

    def __str__(self):
        return f"{self.title} - {self.dashboard.title}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            default_configs = {
                'KPI': {
                    'type': 'NUMBER',
                    'options': {
                        'title': self.title,
                        'show_change': True,
                        'animate': True,
                        'color_scheme': self.color_scheme
                    }
                },
                'CHART': {
                    'type': 'LINE',
                    'options': {
                        'title': self.title,
                        'x_axis_label': 'Time',
                        'y_axis_label': 'Value',
                        'show_legend': True,
                        'animate': True,
                        'color_scheme': self.color_scheme
                    }
                },
                'TABLE': {
                    'type': 'TABLE',
                    'options': {
                        'title': self.title,
                        'exportable': True,
                        'searchable': True,
                        'paginate': True,
                        'page_size': 10,
                        'sortable': True
                    }
                },
                'HEATMAP': {
                    'type': 'HEATMAP',
                    'options': {
                        'title': self.title,
                        'show_values': True,
                        'color_scale': 'viridis',
                        'animate': True
                    }
                }
            }
            
            default_config = default_configs.get(self.widget_type, {
                'type': 'TEXT',
                'options': {
                    'title': self.title,
                    'content': 'Configure widget content...'
                }
            })
            
            self.chart_config = default_config
        super().save(*args, **kwargs)

    def get_data(self, filters=None):
        """Get widget data with optional filters"""
        # Implementation depends on widget type and data source
        pass

    def update_position(self, x, y, width, height):
        """Update widget position and size"""
        self.position_x = x
        self.position_y = y
        self.width = width
        self.height = height
        self.save()


class PredictiveModel(BaseModel):
    """
    Machine learning and predictive analytics models
    """
    MODEL_TYPE_CHOICES = (
        ("CLASSIFICATION", _("Classification")),
        ("REGRESSION", _("Regression")),
        ("CLUSTERING", _("Clustering")),
        ("FORECASTING", _("Forecasting")),
        ("ANOMALY_DETECTION", _("Anomaly Detection")),
        ("RECOMMENDATION", _("Recommendation")),
    )

    STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("TRAINING", _("Training")),
        ("TRAINED", _("Trained")),
        ("DEPLOYED", _("Deployed")),
        ("ERROR", _("Error")),
        ("ARCHIVED", _("Archived")),
    )

    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("Model Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        verbose_name=_("Model Type")
    )
    
    # Configuration
    algorithm = models.CharField(max_length=100, verbose_name=_("Algorithm"))
    hyperparameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Hyperparameters")
    )
    feature_columns = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Feature Columns")
    )
    target_column = models.CharField(
        max_length=100,
        verbose_name=_("Target Column")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Data Source
    training_data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="predictive_models",
        verbose_name=_("Training Data Source")
    )
    training_query = models.TextField(
        blank=True,
        verbose_name=_("Training Data Query")
    )
    
    # Status and Performance
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Accuracy Score")
    )
    precision = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Precision Score")
    )
    recall = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Recall Score")
    )
    f1_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("F1 Score")
    )
    
    # Training Information
    trained_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Trained At")
    )
    training_duration = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Training Duration")
    )
    model_file = models.FileField(
        upload_to='analytics/models/',
        null=True,
        blank=True,
        verbose_name=_("Model File")
    )
    
    # Monitoring
    last_prediction = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Prediction")
    )
    prediction_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Prediction Count")
    )

    class Meta:
        db_table = "analytics_predictive_model"
        ordering = ["name", "model_type"]
        verbose_name = _("Predictive Model")
        verbose_name_plural = _("Predictive Models")
        indexes = [
            models.Index(fields=['model_type', 'status']),
            models.Index(fields=['algorithm', 'status']),
            models.Index(fields=['status', 'trained_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'LINE',
                'options': {
                    'title': f"{self.name} Performance",
                    'x_axis_label': 'Iterations',
                    'y_axis_label': 'Score',
                    'show_legend': True,
                    'show_metrics': True,
                    'animate': True,
                    'colors': ['#007bff', '#28a745', '#dc3545', '#ffc107']
                },
                'metrics': {
                    'accuracy': float(self.accuracy) if self.accuracy else 0,
                    'precision': float(self.precision) if self.precision else 0,
                    'recall': float(self.recall) if self.recall else 0,
                    'f1_score': float(self.f1_score) if self.f1_score else 0
                }
            }
        super().save(*args, **kwargs)

    def train_model(self):
        """Train the predictive model"""
        self.status = "TRAINING"
        self.save()
        # Implementation for model training
        pass

    def predict(self, input_data):
        """Make prediction using the model"""
        if self.status != "DEPLOYED":
            raise ValidationError(_("Model is not deployed"))
        
        # Implementation for prediction
        pass

    def evaluate_model(self, test_data):
        """Evaluate model performance"""
        # Implementation for model evaluation
        pass


class StudentPerformanceAnalytics(BaseModel):
    """
    Comprehensive student performance analytics
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="performance_analytics",
        verbose_name=_("Student")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="student_analytics",
        verbose_name=_("Academic Year")
    )
    
    # Academic Performance
    overall_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Overall Percentage")
    )
    class_rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Class Rank")
    )
    total_students = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Students in Class")
    )
    
    # Subject-wise Performance
    subject_performance = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Subject-wise Performance")
    )
    strong_subjects = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Strong Subjects")
    )
    weak_subjects = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Weak Subjects")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Attendance Analytics
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Attendance Percentage")
    )
    total_present = models.PositiveIntegerField(default=0, verbose_name=_("Total Present"))
    total_absent = models.PositiveIntegerField(default=0, verbose_name=_("Total Absent"))
    total_leave = models.PositiveIntegerField(default=0, verbose_name=_("Total Leave"))
    
    # Behavioral Analytics
    participation_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Participation Score")
    )
    discipline_incidents = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Discipline Incidents")
    )
    awards_count = models.PositiveIntegerField(default=0, verbose_name=_("Awards Count"))
    
    # Growth Metrics
    performance_trend = models.CharField(
        max_length=20,
        choices=(
            ("IMPROVING", _("Improving")),
            ("DECLINING", _("Declining")),
            ("STABLE", _("Stable")),
            ("FLUCTUATING", _("Fluctuating")),
        ),
        blank=True,
        verbose_name=_("Performance Trend")
    )
    growth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Growth Percentage")
    )
    
    # Predictive Analytics
    at_risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("At-Risk Score")
    )
    predicted_performance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Predicted Performance")
    )
    recommendation = models.TextField(
        blank=True,
        verbose_name=_("Recommendation")
    )

    class Meta:
        db_table = "analytics_student_performance"
        unique_together = [['student', 'academic_year']]
        ordering = ["academic_year", "class_rank"]
        verbose_name = _("Student Performance Analytics")
        verbose_name_plural = _("Student Performance Analytics")
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['overall_percentage', 'class_rank']),
            models.Index(fields=['at_risk_score']),
        ]

    def __str__(self):
        return f"Performance Analytics - {self.student} - {self.academic_year}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'RADAR',
                'options': {
                    'title': f"Performance Analysis - {self.student.get_full_name()}",
                    'show_subjects': True,
                    'show_average': True,
                    'show_trend': True,
                    'animate': True,
                    'colors': ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8']
                },
                'subjects': list(self.subject_performance.keys()) if self.subject_performance else [],
                'scores': list(self.subject_performance.values()) if self.subject_performance else []
            }
        super().save(*args, **kwargs)

    @property
    def percentile_rank(self):
        """Calculate percentile rank"""
        if self.class_rank and self.total_students:
            return ((self.total_students - self.class_rank) / self.total_students) * 100
        return None

    def calculate_improvement_areas(self):
        """Calculate areas for improvement"""
        # Implementation for improvement area analysis
        pass

    def generate_study_plan(self):
        """Generate personalized study plan"""
        # Implementation for study plan generation
        pass


class InstitutionalAnalytics(BaseModel):
    """
    Institutional-level analytics and insights
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="institutional_analytics",
        verbose_name=_("Academic Year")
    )
    
    # Student Demographics
    total_students = models.PositiveIntegerField(default=0, verbose_name=_("Total Students"))
    male_students = models.PositiveIntegerField(default=0, verbose_name=_("Male Students"))
    female_students = models.PositiveIntegerField(default=0, verbose_name=_("Female Students"))
    other_gender_students = models.PositiveIntegerField(default=0, verbose_name=_("Other Gender Students"))
    
    # Financial Metrics
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Revenue")
    )
    total_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Expenses")
    )
    fee_collection_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fee Collection Percentage")
    )
    
    # Staff Metrics
    total_staff = models.PositiveIntegerField(default=0, verbose_name=_("Total Staff"))
    student_teacher_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Student-Teacher Ratio")
    )
    
    # Academic Metrics
    average_attendance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Average Attendance")
    )
    pass_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Pass Percentage")
    )
    
    chart_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Chart Configuration"),
        help_text=_("JSON configuration for visualization")
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True, verbose_name=_("Calculated At"))

    class Meta:
        db_table = "analytics_institutional"
        verbose_name = _("Institutional Analytics")
        verbose_name_plural = _("Institutional Analytics")
        ordering = ["-academic_year"]

    def __str__(self):
        return f"Institutional Analytics - {self.academic_year}"
    
    def save(self, *args, **kwargs):
        # Set default chart config if empty
        if not self.chart_config:
            self.chart_config = {
                'type': 'KPI_CARD',
                'options': {
                    'title': f"Institutional Overview - {self.academic_year.name}",
                    'layout': 'grid',
                    'show_financials': True,
                    'show_demographics': True,
                    'show_academics': True,
                    'theme': 'corporate',
                    'animate': True
                },
                'metrics': {
                    'total_students': self.total_students,
                    'total_revenue': float(self.total_revenue),
                    'total_expenses': float(self.total_expenses),
                    'average_attendance': float(self.average_attendance),
                    'pass_percentage': float(self.pass_percentage),
                    'student_teacher_ratio': float(self.student_teacher_ratio) if self.student_teacher_ratio else None
                }
            }
        super().save(*args, **kwargs)

    def calculate_metrics(self):
        """Calculate institutional metrics"""
        # Implementation for calculating all metrics
        pass
