import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel


class SecurityPolicy(BaseModel):
    """
    Security policies and configurations
    """
    POLICY_TYPE_CHOICES = (
        ("PASSWORD", _("Password Policy")),
        ("SESSION", _("Session Policy")),
        ("ACCESS", _("Access Control Policy")),
        ("AUDIT", _("Audit Policy")),
        ("NETWORK", _("Network Security Policy")),
        ("DATA", _("Data Protection Policy")),
        ("COMPLIANCE", _("Compliance Policy")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Policy Name"))
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPE_CHOICES,
        verbose_name=_("Policy Type")
    )
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Policy Code"))
    
    # Policy Configuration
    description = models.TextField(verbose_name=_("Description"))
    policy_document = models.TextField(verbose_name=_("Policy Document"))
    version = models.CharField(max_length=20, default="1.0", verbose_name=_("Version"))
    
    # Enforcement
    is_mandatory = models.BooleanField(default=True, verbose_name=_("Is Mandatory"))
    enforcement_level = models.CharField(
        max_length=20,
        choices=(
            ("LOW", _("Low")),
            ("MEDIUM", _("Medium")),
            ("HIGH", _("High")),
            ("CRITICAL", _("Critical")),
        ),
        default="MEDIUM",
        verbose_name=_("Enforcement Level")
    )
    
    # Compliance
    compliance_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Compliance Standard")
    )
    requires_acknowledgement = models.BooleanField(
        default=True,
        verbose_name=_("Requires User Acknowledgement")
    )
    
    # Status
    effective_date = models.DateField(default=timezone.now, verbose_name=_("Effective Date"))
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expiry Date")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "security_policies"
        verbose_name = _("Security Policy")
        verbose_name_plural = _("Security Policies")
        ordering = ["policy_type", "name"]
        indexes = [
            models.Index(fields=['policy_type', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_policy_type_display()})"

    @property
    def is_current(self):
        today = timezone.now().date()
        if self.expiry_date:
            return self.effective_date <= today <= self.expiry_date
        return self.effective_date <= today

    @property
    def acknowledgement_count(self):
        return self.acknowledgements.filter(acknowledged=True).count()


class PasswordPolicy(BaseModel):
    """
    Password complexity and expiration policies
    """
    name = models.CharField(max_length=100, verbose_name=_("Policy Name"))
    
    # Complexity Requirements
    min_length = models.PositiveIntegerField(default=8, verbose_name=_("Minimum Length"))
    require_uppercase = models.BooleanField(default=True, verbose_name=_("Require Uppercase"))
    require_lowercase = models.BooleanField(default=True, verbose_name=_("Require Lowercase"))
    require_numbers = models.BooleanField(default=True, verbose_name=_("Require Numbers"))
    require_special_chars = models.BooleanField(default=True, verbose_name=_("Require Special Characters"))
    min_special_chars = models.PositiveIntegerField(default=1, verbose_name=_("Minimum Special Characters"))
    
    # Password History
    prevent_reuse = models.BooleanField(default=True, verbose_name=_("Prevent Password Reuse"))
    password_history_size = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Password History Size")
    )
    
    # Expiration
    password_expiry_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_("Password Expiry (days)")
    )
    warn_before_expiry = models.PositiveIntegerField(
        default=7,
        verbose_name=_("Warn Before Expiry (days)")
    )
    
    # Account Lockout
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Maximum Login Attempts")
    )
    lockout_duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Lockout Duration (minutes)")
    )
    
    # Additional Security
    require_mfa = models.BooleanField(default=False, verbose_name=_("Require MFA"))
    mfa_methods = models.JSONField(
        default=list,
        verbose_name=_("Allowed MFA Methods"),
        help_text=_("List of allowed MFA methods: ['TOTP', 'SMS', 'EMAIL']")
    )
    
    # Application Scope
    apply_to_students = models.BooleanField(default=True, verbose_name=_("Apply to Students"))
    apply_to_staff = models.BooleanField(default=True, verbose_name=_("Apply to Staff"))
    apply_to_admins = models.BooleanField(default=True, verbose_name=_("Apply to Administrators"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "security_password_policies"
        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def validate_password(self, password, user=None):
        """Validate password against policy"""
        errors = []
        
        if len(password) < self.min_length:
            errors.append(_(f"Password must be at least {self.min_length} characters long"))
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append(_("Password must contain at least one uppercase letter"))
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append(_("Password must contain at least one lowercase letter"))
        
        if self.require_numbers and not any(c.isdigit() for c in password):
            errors.append(_("Password must contain at least one number"))
        
        if self.require_special_chars:
            special_chars = sum(1 for c in password if not c.isalnum())
            if special_chars < self.min_special_chars:
                errors.append(_(f"Password must contain at least {self.min_special_chars} special characters"))
        
        # Check password history if user provided
        if user and self.prevent_reuse:
            from django.contrib.auth.hashers import check_password
            for old_password in user.previous_passwords[-self.password_history_size:]:
                if check_password(password, old_password):
                    errors.append(_("Cannot reuse previous passwords"))
                    break
        
        return errors


class SessionPolicy(BaseModel):
    """
    Session management and timeout policies
    """
    name = models.CharField(max_length=100, verbose_name=_("Policy Name"))
    
    # Session Timeout
    session_timeout_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Session Timeout (minutes)")
    )
    extend_session_on_activity = models.BooleanField(
        default=True,
        verbose_name=_("Extend Session on Activity")
    )
    
    # Concurrent Sessions
    max_concurrent_sessions = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Maximum Concurrent Sessions")
    )
    prevent_concurrent_logins = models.BooleanField(
        default=False,
        verbose_name=_("Prevent Concurrent Logins")
    )
    
    # Security Features
    require_secure_cookies = models.BooleanField(default=True, verbose_name=_("Require Secure Cookies"))
    http_only_cookies = models.BooleanField(default=True, verbose_name=_("HTTP Only Cookies"))
    same_site_cookies = models.CharField(
        max_length=10,
        choices=(
            ("LAX", "Lax"),
            ("STRICT", "Strict"),
            ("NONE", "None"),
        ),
        default="LAX",
        verbose_name=_("SameSite Cookie Policy")
    )
    
    # Application Scope
    apply_to_students = models.BooleanField(default=True, verbose_name=_("Apply to Students"))
    apply_to_staff = models.BooleanField(default=True, verbose_name=_("Apply to Staff"))
    apply_to_admins = models.BooleanField(default=True, verbose_name=_("Apply to Administrators"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "security_session_policies"
        verbose_name = _("Session Policy")
        verbose_name_plural = _("Session Policies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class AccessControlPolicy(BaseModel):
    """
    Role-based access control policies
    """
    name = models.CharField(max_length=100, verbose_name=_("Policy Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Access Rules
    ip_whitelist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("IP Whitelist"),
        help_text=_("List of allowed IP addresses/CIDR ranges")
    )
    ip_blacklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("IP Blacklist"),
        help_text=_("List of blocked IP addresses/CIDR ranges")
    )
    
    # Time-based Access
    allowed_access_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Allowed Access Hours"),
        help_text=_("JSON: {'start': '09:00', 'end': '17:00', 'days': [0,1,2,3,4]}")
    )
    
    # Geographic Restrictions
    allowed_countries = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Allowed Countries"),
        help_text=_("List of allowed country codes")
    )
    blocked_countries = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Blocked Countries"),
        help_text=_("List of blocked country codes")
    )
    
    # Device Restrictions
    allowed_user_agents = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Allowed User Agents"),
        help_text=_("List of allowed user agent patterns")
    )
    require_secure_connection = models.BooleanField(
        default=True,
        verbose_name=_("Require HTTPS")
    )
    
    # Application Scope
    apply_to_roles = models.JSONField(
        default=list,
        verbose_name=_("Apply to Roles"),
        help_text=_("List of roles this policy applies to")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "security_access_control_policies"
        verbose_name = _("Access Control Policy")
        verbose_name_plural = _("Access Control Policies")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_access_allowed(self, request):
        """Check if access is allowed based on policy"""
        # Check IP address
        client_ip = self.get_client_ip(request)
        if client_ip in self.ip_blacklist:
            return False, "IP address blocked"
        
        if self.ip_whitelist and client_ip not in self.ip_whitelist:
            return False, "IP address not in whitelist"
        
        # Check time-based access
        if not self.is_within_access_hours():
            return False, "Access not allowed at this time"
        
        # Check geographic restrictions (requires GeoIP setup)
        if not self.is_country_allowed(request):
            return False, "Access not allowed from this country"
        
        # Check user agent
        if not self.is_user_agent_allowed(request):
            return False, "User agent not allowed"
        
        # Check HTTPS requirement
        if self.require_secure_connection and not request.is_secure():
            return False, "HTTPS required"
        
        return True, "Access allowed"

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_within_access_hours(self):
        """Check if current time is within allowed access hours"""
        if not self.allowed_access_hours:
            return True
        
        now = timezone.now()
        current_time = now.time()
        current_day = now.weekday()
        
        start_time = timezone.datetime.strptime(
            self.allowed_access_hours.get('start', '00:00'), 
            '%H:%M'
        ).time()
        end_time = timezone.datetime.strptime(
            self.allowed_access_hours.get('end', '23:59'), 
            '%H:%M'
        ).time()
        allowed_days = self.allowed_access_hours.get('days', [])
        
        return (
            start_time <= current_time <= end_time and
            current_day in allowed_days
        )

    def is_country_allowed(self, request):
        """Check if country is allowed (requires GeoIP2 setup)"""
        # This is a simplified implementation
        # In production, you would use GeoIP2 or similar service
        return True

    def is_user_agent_allowed(self, request):
        """Check if user agent is allowed"""
        if not self.allowed_user_agents:
            return True
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return any(pattern in user_agent for pattern in self.allowed_user_agents)


class AuditLog(BaseModel):
    """
    Comprehensive audit logging for security events
    """
    EVENT_CATEGORY_CHOICES = (
        ("AUTHENTICATION", _("Authentication")),
        ("AUTHORIZATION", _("Authorization")),
        ("USER_MANAGEMENT", _("User Management")),
        ("DATA_ACCESS", _("Data Access")),
        ("CONFIGURATION", _("Configuration Change")),
        ("SYSTEM", _("System Event")),
        ("SECURITY", _("Security Incident")),
        ("COMPLIANCE", _("Compliance")),
    )

    EVENT_SEVERITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    )

    EVENT_OUTCOME_CHOICES = (
        ("SUCCESS", _("Success")),
        ("FAILURE", _("Failure")),
        ("WARNING", _("Warning")),
        ("UNKNOWN", _("Unknown")),
    )

    # Event Identification
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_("Event ID")
    )
    event_type = models.CharField(max_length=100, verbose_name=_("Event Type"))
    event_category = models.CharField(
        max_length=20,
        choices=EVENT_CATEGORY_CHOICES,
        verbose_name=_("Event Category")
    )
    
    # Event Details
    description = models.TextField(verbose_name=_("Description"))
    severity = models.CharField(
        max_length=10,
        choices=EVENT_SEVERITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Severity")
    )
    outcome = models.CharField(
        max_length=10,
        choices=EVENT_OUTCOME_CHOICES,
        default="UNKNOWN",
        verbose_name=_("Outcome")
    )
    
    # User Context
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name=_("User")
    )
    user_role = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("User Role")
    )
    
    # Request Context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address")
    )
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))
    request_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("HTTP Method")
    )
    request_path = models.TextField(blank=True, verbose_name=_("Request Path"))
    
    # Resource Context
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Resource Type")
    )
    resource_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Resource ID")
    )
    resource_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Resource Name")
    )
    
    # Additional Data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata")
    )
    correlation_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Correlation ID")
    )

    class Meta:
        db_table = "security_audit_logs"
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['event_category', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.created_at}"

    @classmethod
    def log_event(cls, event_type, description, user=None, severity="MEDIUM", 
                  outcome="UNKNOWN", request=None, resource=None, metadata=None):
        """Convenience method to log security events"""
        audit_log = cls(
            event_type=event_type,
            description=description,
            user=user,
            user_role=user.role if user else None,
            severity=severity,
            outcome=outcome,
            metadata=metadata or {}
        )
        
        # Extract request information
        if request:
            audit_log.ip_address = cls.get_client_ip(request)
            audit_log.user_agent = request.META.get('HTTP_USER_AGENT', '')
            audit_log.request_method = request.method
            audit_log.request_path = request.path
        
        # Extract resource information
        if resource:
            audit_log.resource_type = resource.__class__.__name__
            audit_log.resource_id = str(getattr(resource, 'id', ''))
            audit_log.resource_name = str(resource)
        
        audit_log.save()
        return audit_log

    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityIncident(BaseModel):
    """
    Security incident management and tracking
    """
    INCIDENT_TYPE_CHOICES = (
        ("UNAUTHORIZED_ACCESS", _("Unauthorized Access")),
        ("DATA_BREACH", _("Data Breach")),
        ("MALWARE", _("Malware Infection")),
        ("PHISHING", _("Phishing Attack")),
        ("DOS", _("Denial of Service")),
        ("BRUTE_FORCE", _("Brute Force Attack")),
        ("SUSPICIOUS_ACTIVITY", _("Suspicious Activity")),
        ("POLICY_VIOLATION", _("Policy Violation")),
        ("OTHER", _("Other")),
    )

    INCIDENT_STATUS_CHOICES = (
        ("OPEN", _("Open")),
        ("UNDER_INVESTIGATION", _("Under Investigation")),
        ("CONTAINED", _("Contained")),
        ("RESOLVED", _("Resolved")),
        ("CLOSED", _("Closed")),
    )

    PRIORITY_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    )

    incident_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Incident ID")
    )
    title = models.CharField(max_length=200, verbose_name=_("Incident Title"))
    incident_type = models.CharField(
        max_length=30,
        choices=INCIDENT_TYPE_CHOICES,
        verbose_name=_("Incident Type")
    )
    
    # Incident Details
    description = models.TextField(verbose_name=_("Description"))
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Priority")
    )
    status = models.CharField(
        max_length=25,
        choices=INCIDENT_STATUS_CHOICES,
        default="OPEN",
        verbose_name=_("Status")
    )
    
    # Timeline
    detected_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Detected At")
    )
    reported_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Reported At")
    )
    contained_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Contained At")
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Resolved At")
    )
    
    # Impact Assessment
    impact_level = models.CharField(
        max_length=20,
        choices=(
            ("MINIMAL", _("Minimal")),
            ("MODERATE", _("Moderate")),
            ("MAJOR", _("Major")),
            ("SEVERE", _("Severe")),
        ),
        default="MODERATE",
        verbose_name=_("Impact Level")
    )
    affected_systems = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Affected Systems")
    )
    data_compromised = models.BooleanField(
        default=False,
        verbose_name=_("Data Compromised")
    )
    data_compromised_details = models.TextField(
        blank=True,
        verbose_name=_("Data Compromised Details")
    )
    
    # Response Team
    assigned_to = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_incidents",
        verbose_name=_("Assigned To")
    )
    reporter = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reported_incidents",
        verbose_name=_("Reporter")
    )
    
    # Investigation
    root_cause = models.TextField(blank=True, verbose_name=_("Root Cause"))
    action_taken = models.TextField(blank=True, verbose_name=_("Action Taken"))
    prevention_measures = models.TextField(
        blank=True,
        verbose_name=_("Prevention Measures")
    )
    
    # Compliance
    regulatory_report_required = models.BooleanField(
        default=False,
        verbose_name=_("Regulatory Report Required")
    )
    regulatory_body = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Regulatory Body")
    )
    
    # Additional Information
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Attachments")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "security_incidents"
        verbose_name = _("Security Incident")
        verbose_name_plural = _("Security Incidents")
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=['incident_id']),
            models.Index(fields=['incident_type', 'status']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.incident_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.incident_id:
            self.incident_id = self.generate_incident_id()
        super().save(*args, **kwargs)

    def generate_incident_id(self):
        """Generate unique incident ID"""
        prefix = f"INC-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_incident = SecurityIncident.objects.filter(
            incident_id__startswith=prefix,
            tenant=self.tenant
        ).order_by('incident_id').last()
        
        if last_incident:
            last_num = int(last_incident.incident_id.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:04d}"

    def add_timeline_event(self, event_type, description, user):
        """Add event to incident timeline"""
        IncidentTimeline.objects.create(
            incident=self,
            event_type=event_type,
            description=description,
            created_by=user
        )

    def mark_contained(self, user, notes=""):
        """Mark incident as contained"""
        self.status = "CONTAINED"
        self.contained_at = timezone.now()
        self.notes = f"{self.notes}\nContained: {notes}"
        self.save()
        
        self.add_timeline_event(
            "CONTAINED",
            f"Incident contained by {user.get_full_name()}",
            user
        )

    def mark_resolved(self, user, root_cause="", action_taken=""):
        """Mark incident as resolved"""
        self.status = "RESOLVED"
        self.resolved_at = timezone.now()
        self.root_cause = root_cause
        self.action_taken = action_taken
        self.save()
        
        self.add_timeline_event(
            "RESOLVED",
            f"Incident resolved by {user.get_full_name()}",
            user
        )


class IncidentTimeline(BaseModel):
    """
    Timeline of events for security incidents
    """
    EVENT_TYPE_CHOICES = (
        ("DETECTED", _("Detected")),
        ("REPORTED", _("Reported")),
        ("ASSIGNED", _("Assigned")),
        ("INVESTIGATION_STARTED", _("Investigation Started")),
        ("EVIDENCE_COLLECTED", _("Evidence Collected")),
        ("CONTAINED", _("Contained")),
        ("RESOLVED", _("Resolved")),
        ("CLOSED", _("Closed")),
        ("NOTE", _("Note")),
        ("OTHER", _("Other")),
    )

    incident = models.ForeignKey(
        SecurityIncident,
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name=_("Incident")
    )
    event_type = models.CharField(
        max_length=25,
        choices=EVENT_TYPE_CHOICES,
        verbose_name=_("Event Type")
    )
    description = models.TextField(verbose_name=_("Description"))
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="incident_timeline_events",
        verbose_name=_("Created By")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata")
    )

    class Meta:
        db_table = "security_incident_timeline"
        verbose_name = _("Incident Timeline Event")
        verbose_name_plural = _("Incident Timeline Events")
        ordering = ["incident", "created_at"]

    def __str__(self):
        return f"{self.incident.incident_id} - {self.event_type} - {self.created_at}"


class ThreatIntelligence(BaseModel):
    """
    Threat intelligence and indicators of compromise
    """
    THREAT_TYPE_CHOICES = (
        ("MALWARE", _("Malware")),
        ("PHISHING", _("Phishing")),
        ("RANSOMWARE", _("Ransomware")),
        ("BOTNET", _("Botnet")),
        ("DDoS", _("DDoS")),
        ("EXPLOIT", _("Exploit")),
        ("OTHER", _("Other")),
    )

    CONFIDENCE_LEVEL_CHOICES = (
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CONFIRMED", _("Confirmed")),
    )

    indicator = models.CharField(
        max_length=500,
        unique=True,
        verbose_name=_("Indicator")
    )
    indicator_type = models.CharField(
        max_length=20,
        choices=(
            ("IP_ADDRESS", _("IP Address")),
            ("DOMAIN", _("Domain")),
            ("URL", _("URL")),
            ("HASH", _("File Hash")),
            ("EMAIL", _("Email Address")),
            ("OTHER", _("Other")),
        ),
        verbose_name=_("Indicator Type")
    )
    threat_type = models.CharField(
        max_length=20,
        choices=THREAT_TYPE_CHOICES,
        verbose_name=_("Threat Type")
    )
    
    # Threat Details
    description = models.TextField(verbose_name=_("Description"))
    confidence_level = models.CharField(
        max_length=15,
        choices=CONFIDENCE_LEVEL_CHOICES,
        default="MEDIUM",
        verbose_name=_("Confidence Level")
    )
    severity = models.CharField(
        max_length=10,
        choices=AuditLog.EVENT_SEVERITY_CHOICES,
        default="MEDIUM",
        verbose_name=_("Severity")
    )
    
    # Source and Validity
    source = models.CharField(max_length=200, verbose_name=_("Source"))
    first_seen = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("First Seen")
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Seen")
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Valid Until")
    )
    
    # Additional Information
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Tags")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "security_threat_intelligence"
        verbose_name = _("Threat Intelligence")
        verbose_name_plural = _("Threat Intelligence")
        ordering = ["-first_seen"]
        indexes = [
            models.Index(fields=['indicator', 'is_active']),
            models.Index(fields=['indicator_type', 'threat_type']),
            models.Index(fields=['confidence_level', 'severity']),
        ]

    def __str__(self):
        return f"{self.indicator} - {self.get_threat_type_display()}"

    @property
    def is_valid(self):
        if self.valid_until:
            return timezone.now() <= self.valid_until
        return True

    def check_match(self, value):
        """Check if value matches this threat indicator"""
        if self.indicator_type == "IP_ADDRESS":
            return value == self.indicator
        elif self.indicator_type == "DOMAIN":
            return self.indicator in value
        elif self.indicator_type == "URL":
            return self.indicator in value
        elif self.indicator_type == "HASH":
            return value.lower() == self.indicator.lower()
        elif self.indicator_type == "EMAIL":
            return value == self.indicator
        return False


class SecurityScan(BaseModel):
    """
    Security vulnerability scans and assessments
    """
    SCAN_TYPE_CHOICES = (
        ("VULNERABILITY", _("Vulnerability Scan")),
        ("COMPLIANCE", _("Compliance Scan")),
        ("PENETRATION_TEST", _("Penetration Test")),
        ("CODE_REVIEW", _("Code Review")),
        ("CONFIGURATION", _("Configuration Audit")),
    )

    SCAN_STATUS_CHOICES = (
        ("SCHEDULED", _("Scheduled")),
        ("IN_PROGRESS", _("In Progress")),
        ("COMPLETED", _("Completed")),
        ("FAILED", _("Failed")),
        ("CANCELLED", _("Cancelled")),
    )

    scan_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Scan ID")
    )
    scan_type = models.CharField(
        max_length=20,
        choices=SCAN_TYPE_CHOICES,
        verbose_name=_("Scan Type")
    )
    target = models.CharField(max_length=500, verbose_name=_("Target"))
    
    # Scan Configuration
    description = models.TextField(blank=True, verbose_name=_("Description"))
    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Scan Parameters")
    )
    
    # Schedule
    scheduled_at = models.DateTimeField(verbose_name=_("Scheduled At"))
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
    
    # Results
    status = models.CharField(
        max_length=15,
        choices=SCAN_STATUS_CHOICES,
        default="SCHEDULED",
        verbose_name=_("Status")
    )
    findings_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Findings Count")
    )
    critical_findings = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Critical Findings")
    )
    high_findings = models.PositiveIntegerField(
        default=0,
        verbose_name=_("High Findings")
    )
    scan_report = models.FileField(
        upload_to='security/scans/reports/',
        null=True,
        blank=True,
        verbose_name=_("Scan Report")
    )
    
    # Initiator
    initiated_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="initiated_scans",
        verbose_name=_("Initiated By")
    )
    scanner = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Scanner Tool")
    )

    class Meta:
        db_table = "security_scans"
        verbose_name = _("Security Scan")
        verbose_name_plural = _("Security Scans")
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=['scan_id']),
            models.Index(fields=['scan_type', 'status']),
            models.Index(fields=['scheduled_at']),
        ]

    def __str__(self):
        return f"{self.scan_id} - {self.scan_type} - {self.target}"

    def save(self, *args, **kwargs):
        if not self.scan_id:
            self.scan_id = self.generate_scan_id()
        super().save(*args, **kwargs)

    def generate_scan_id(self):
        """Generate unique scan ID"""
        prefix = f"SCAN-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_scan = SecurityScan.objects.filter(
            scan_id__startswith=prefix,
            tenant=self.tenant
        ).order_by('scan_id').last()
        
        if last_scan:
            last_num = int(last_scan.scan_id.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:04d}"

    def start_scan(self):
        """Start the security scan"""
        self.status = "IN_PROGRESS"
        self.started_at = timezone.now()
        self.save()
        # Implementation to trigger actual scan
        pass