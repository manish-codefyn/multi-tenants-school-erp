from django.db import models
from django.utils.text import slugify

from django_tenants.models import TenantMixin, DomainMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from apps.core.models import UUIDModel, TimeStampedModel, BaseModel, BaseSharedModel

class Tenant(TenantMixin, BaseSharedModel):
    """
    Secure multi-tenant implementation with enterprise features
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Organization Name',
        help_text='Legal name of the institution/organization'
    )
    display_name = models.CharField(
        max_length=255,
        verbose_name='Display Name',
        help_text='Public-facing name for the institution'
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True)

    # Tenant Status & Configuration
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_TRIAL = 'trial'
    STATUS_EXPIRED = 'expired'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_TRIAL, 'Trial'),
        (STATUS_EXPIRED, 'Expired'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TRIAL,
        db_index=True,
        verbose_name='Tenant Status'
    )
    
    # Subscription & Limits
    PLAN_BASIC = 'basic'
    PLAN_PROFESSIONAL = 'professional'
    PLAN_ENTERPRISE = 'enterprise'
    
    PLAN_CHOICES = [
        (PLAN_BASIC, 'Basic'),
        (PLAN_PROFESSIONAL, 'Professional'),
        (PLAN_ENTERPRISE, 'Enterprise'),
    ]
    
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_BASIC,
        verbose_name='Subscription Plan'
    )
    
    max_users = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        verbose_name='Maximum Users',
        help_text='Maximum number of active users allowed'
    )
    
    max_storage_mb = models.PositiveIntegerField(
        default=1024,  # 1GB
        verbose_name='Storage Limit (MB)',
        help_text='Maximum storage space in megabytes'
    )
    
    # Contact Information
    contact_email = models.EmailField(
        verbose_name='Contact Email',
        help_text='Primary contact email for administrative communications'
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Contact Phone',
        help_text='Primary contact phone number'
    )
    
    # Security & Compliance
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Active Status',
        help_text='Designates whether this tenant can access the system'
    )
    
    force_password_reset = models.BooleanField(
        default=False,
        verbose_name='Force Password Reset',
        help_text='Require all users to reset their passwords on next login'
    )
    
    mfa_required = models.BooleanField(
        default=False,
        verbose_name='MFA Required',
        help_text='Require multi-factor authentication for all users'
    )
    
    password_policy = models.JSONField(
        default=dict,
        verbose_name='Password Policy',
        help_text='Custom password policy configuration'
    )
    
    # Subscription Management
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Trial End Date'
    )
    
    subscription_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Subscription End Date'
    )
    
    # Auto-create schema for new tenants
    auto_create_schema = True

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        indexes = [
            models.Index(fields=['schema_name']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['plan', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    @property
    def branding_info(self):
        """Get complete branding information"""
        if hasattr(self, 'configuration'):
            config = self.configuration
            return {
                'name': self.name,
                'logo': config.logo.url if config.logo else '/static/images/logo.png',
                'primary_color': config.primary_color,
                'secondary_color': config.secondary_color,
                'mfa_required': self.mfa_required,
            }
        return {
            'name': self.name,
            'logo': '/static/images/logo.png',
            'primary_color': '#3B82F6',  # Default from TenantConfiguration
            'secondary_color': '#1E40AF',  # Default from TenantConfiguration
            'mfa_required': self.mfa_required,
        }
        
    def audit_log(self, action, user=None, metadata=None, severity='MEDIUM'):
        """Create security audit log entry"""
        from apps.auth.models import SecurityEvent  # Adjust import path
        
        SecurityEvent.objects.create(
            tenant=self,
            user=user,
            event_type=action,
            severity=severity,
            description=f"Tenant {self.name}: {action}",
            metadata=metadata or {}
        )

    def clean(self):
        """
        Comprehensive tenant validation
        """
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validate schema name format
        if self.schema_name:
            if not self.schema_name.replace('_', '').isalnum():
                raise ValidationError({
                    'schema_name': 'Schema name can only contain alphanumeric characters and underscores.'
                })
            if len(self.schema_name) > 63:
                raise ValidationError({
                    'schema_name': 'Schema name cannot exceed 63 characters.'
                })

    @property
    def is_trial(self):
        """Check if tenant is in trial period"""
        from django.utils import timezone
        return (self.status == self.STATUS_TRIAL and 
                self.trial_ends_at and 
                self.trial_ends_at > timezone.now())

    @property
    def is_subscription_active(self):
        """Check if subscription is active"""
        from django.utils import timezone
        return (self.status == self.STATUS_ACTIVE and
                (not self.subscription_ends_at or 
                 self.subscription_ends_at > timezone.now()))

    def get_user_count(self):
        """Get current active user count"""
        from apps.users.models import User
        return User.objects.filter(tenant=self, is_active=True).count()

    def can_add_user(self):
        """Check if tenant can add more users"""
        return self.get_user_count() < self.max_users

    def suspend(self, reason="Administrative action"):
        """Suspend tenant access"""
        self.status = self.STATUS_SUSPENDED
        self.is_active = False
        self.save(update_fields=['status', 'is_active'])
        
        # Log suspension
        self.audit_log('TENANT_SUSPENDED', None, {'reason': reason}, 'HIGH')

    def activate(self):
        """Activate tenant"""
        self.status = self.STATUS_ACTIVE
        self.is_active = True
        self.save(update_fields=['status', 'is_active'])
        
        # Log activation
        self.audit_log('TENANT_ACTIVATED', None, {}, 'MEDIUM')

    def validate_tenant_limits(self):
        """Validate tenant against plan limits"""
        errors = {}
        
        user_count = self.get_user_count()
        if user_count > self.max_users:
            errors['max_users'] = f'User limit exceeded: {user_count}/{self.max_users}'
            
        # Add storage validation when storage tracking is implemented
        return errors

    def save(self, *args, **kwargs):
        """Override save to handle slug, validation, and auto-schema creation."""
        
        # Auto-generate slug if missing
        if not getattr(self, "slug", None) or self.slug == '':
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        
        # Run model validation
        self.clean()

        # Check if new tenant
        is_new = self._state.adding

        # Save tenant first
        super().save(*args, **kwargs)

        # After save: auto create schema & configuration
        if is_new and getattr(self, "auto_create_schema", False):
            from django_tenants.utils import schema_context
            from apps.tenants.models import TenantConfiguration
            from apps.auth.models import RolePermission

            # Create schema
            self.create_schema(check_if_exists=True)

            # Create per-tenant default configuration & permissions
            with schema_context(self.schema_name):
                TenantConfiguration.objects.create(tenant=self)
                RolePermission.create_default_permissions(tenant=self)


class Domain(DomainMixin, BaseModel):
    """
    Custom domain model with enhanced security features
    """
    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Primary Domain',
        help_text='Designates the primary domain for this tenant'
    )
    
    ssl_enabled = models.BooleanField(
        default=True,
        verbose_name='SSL Enabled',
        help_text='Enable SSL for this domain'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Domain Verified',
        help_text='Domain ownership has been verified'
    )
    
    verification_token = models.CharField(
        max_length=64,
        blank=True,
        editable=False,
        verbose_name='Domain Verification Token'
    )

    class Meta:
        db_table = 'tenant_domains'
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'
        indexes = [
            models.Index(fields=['domain', 'is_primary']),
            models.Index(fields=['tenant', 'is_primary']),
        ]

    def clean(self):
        """
        Domain validation
        """
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Ensure only one primary domain per tenant
        if self.is_primary:
            existing_primary = Domain.objects.filter(
                tenant=self.tenant, 
                is_primary=True
            ).exclude(id=self.id)
            
            if existing_primary.exists():
                raise ValidationError({
                    'is_primary': 'Only one domain can be set as primary per tenant.'
                })

    def generate_verification_token(self):
        """Generate domain verification token"""
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['verification_token'])
        return self.verification_token

    def verify_domain(self, token):
        """Verify domain ownership"""
        if self.verification_token == token:
            self.is_verified = True
            self.verification_token = ''  # Clear token after verification
            self.save(update_fields=['is_verified', 'verification_token'])
            return True
        return False

    def save(self, *args, **kwargs):
        """Ensure only one primary domain per tenant"""
        if self.is_primary:
            # Remove primary status from other domains
            Domain.objects.filter(
                tenant=self.tenant, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @property
    def verification_url(self):
        """Generate domain verification URL"""
        if self.verification_token:
            return f"https://{self.domain}/verify-domain/{self.verification_token}/"
        return None

    @property
    def logo(self):
        """Get tenant logo from configuration"""
        if hasattr(self, 'configuration') and self.configuration.logo:
            return self.configuration.logo
        return None
    
    @property
    def branding(self):
        """Get complete branding information"""
        if hasattr(self, 'configuration'):
            return {
                'logo': self.configuration.logo,
                'primary_color': self.configuration.primary_color,
                'secondary_color': self.configuration.secondary_color,
            }
        return None

class TenantConfiguration(UUIDModel, TimeStampedModel):
    """
    Tenant-specific configuration and settings
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='configuration',
        verbose_name='Tenant'
    )
    
    # Academic Configuration
    academic_year = models.CharField(
        max_length=20,
        default='2024-2025',
        verbose_name='Current Academic Year'
    )
    
    # Localization
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name='Default Timezone'
    )
    
    language = models.CharField(
        max_length=10,
        default='en',
        verbose_name='Default Language'
    )
    
    currency = models.CharField(
        max_length=3,
        default='INR',
        verbose_name='Default Currency'
    )
    
    date_format = models.CharField(
        max_length=20,
        default='YYYY-MM-DD',
        verbose_name='Date Format'
    )
    
    # Security Settings
    session_timeout = models.PositiveIntegerField(
        default=30,
        verbose_name='Session Timeout (minutes)'
    )
    
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name='Maximum Login Attempts'
    )
    
    password_expiry_days = models.PositiveIntegerField(
        default=90,
        verbose_name='Password Expiry (days)'
    )
    
    # Feature Flags
    enable_library = models.BooleanField(
        default=True,
        verbose_name='Enable Library Module'
    )
    
    enable_finance = models.BooleanField(
        default=True,
        verbose_name='Enable Finance Module'
    )
    
    enable_inventory = models.BooleanField(
        default=True,
        verbose_name='Enable Inventory Module'
    )
    
    # Custom Branding
    logo = models.ImageField(
        upload_to='tenant_logos/',
        null=True,
        blank=True,
        verbose_name='Organization Logo'
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name='Primary Brand Color'
    )
    
    secondary_color = models.CharField(
        max_length=7,
        default='#1E40AF',
        verbose_name='Secondary Brand Color'
    )

    class Meta:
        db_table = 'tenant_configurations'
        verbose_name = 'Tenant Configuration'
        verbose_name_plural = 'Tenant Configurations'

    def __str__(self):
        return f"Configuration for {self.tenant.name}"

    def get_password_policy(self):
        """Get comprehensive password policy"""
        base_policy = {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special_chars': True,
            'prevent_common_passwords': True,
            'prevent_user_attributes': True,
            'expiry_days': self.password_expiry_days,
            'max_attempts': self.max_login_attempts,
        }
        
        # Merge with tenant-specific overrides
        if hasattr(self.tenant, 'password_policy'):
            base_policy.update(self.tenant.password_policy)
            
        return base_policy


    def get_available_modules(self):
        """Get list of enabled modules"""
        modules = []
        if self.enable_library:
            modules.append('library')
        if self.enable_finance:
            modules.append('finance')
        if self.enable_inventory:
            modules.append('inventory')
        return modules
    
    def validate_storage_limit(self, file_size_mb):
        """Check if file upload is within storage limits"""
        # Implement storage tracking logic
        current_usage = 0  # Get from storage tracking model
        return current_usage + file_size_mb <= self.tenant.max_storage_mb