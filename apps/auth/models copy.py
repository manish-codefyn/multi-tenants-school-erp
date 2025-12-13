from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from apps.core.models import BaseModel


class RolePermission(BaseModel):
    """
    Role-based permission system for multi-tenant applications
    """
    # Role definitions matching User model
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
        ('super_admin', 'Super Administrator'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        db_index=True
    )
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    
    # Optional: Tenant-specific permission overrides
    tenant_specific = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_role_permissions'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        unique_together = ['role', 'permission', 'tenant']

    def __str__(self):
        return f"{self.role} - {self.permission}"

    @classmethod
    def get_permissions_for_role(cls, role, tenant=None):
        """
        Get all permissions for a specific role
        """
        queryset = cls.objects.filter(role=role, is_active=True)
        
        if tenant:
            # Get tenant-specific permissions first, then global ones
            tenant_perms = queryset.filter(tenant=tenant, tenant_specific=True)
            global_perms = queryset.filter(tenant_specific=False)
            permissions = tenant_perms | global_perms
        else:
            permissions = queryset.filter(tenant_specific=False)
            
        return [rp.permission.codename for rp in permissions.distinct()]

    @classmethod
    def assign_permission_to_role(cls, role, permission_codename, tenant=None):
        """
        Assign a permission to a role
        """
        try:
            permission = Permission.objects.get(codename=permission_codename)
            role_perm, created = cls.objects.get_or_create(
                role=role,
                permission=permission,
                tenant=tenant,
                defaults={'tenant_specific': bool(tenant)}
            )
            return role_perm
        except Permission.DoesNotExist:
            return None

    @classmethod
    def create_default_permissions(cls, tenant=None):
        """
        Create default permission sets for each role
        """
        # Default permissions for each role
        role_permissions = {
            'student': [
                'view_profile', 'change_profile', 
                'view_course', 'view_grade', 'view_attendance'
            ],
            'teacher': [
                'view_profile', 'change_profile',
                'view_course', 'change_course', 'view_grade', 'change_grade',
                'view_attendance', 'change_attendance', 'view_student'
            ],
            'staff': [
                'view_profile', 'change_profile',
                'view_course', 'change_course', 'view_grade', 'change_grade',
                'view_attendance', 'change_attendance', 'view_student', 'change_student',
                'view_finance', 'view_inventory'
            ],
            'admin': [
                'view_profile', 'change_profile', 'delete_profile',
                'view_course', 'change_course', 'delete_course',
                'view_grade', 'change_grade', 'delete_grade',
                'view_attendance', 'change_attendance', 'delete_attendance',
                'view_student', 'change_student', 'delete_student',
                'view_finance', 'change_finance', 'delete_finance',
                'view_inventory', 'change_inventory', 'delete_inventory',
                'view_user', 'change_user', 'delete_user'
            ],
            'super_admin': [
                # All permissions
            ]
        }
        
        for role, permissions in role_permissions.items():
            for perm_codename in permissions:
                cls.assign_permission_to_role(role, perm_codename, tenant)


class APIToken(BaseModel):
    """
    API token authentication for programmatic access
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_tokens'
    )
    
    name = models.CharField(max_length=100, verbose_name='Token Name')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Scopes for fine-grained access control
    scopes = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'auth_api_tokens'
        verbose_name = 'API Token'
        verbose_name_plural = 'API Tokens'

    def __str__(self):
        return f"API Token for {self.user.email}"

    @property
    def is_expired(self):
        """Check if token is expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def generate_token(self):
        """Generate secure API token"""
        import secrets
        self.token = secrets.token_urlsafe(32)
        return self.token

    def has_scope(self, scope):
        """Check if token has specific scope"""
        if not self.scopes:  # No scopes means full access
            return True
        return scope in self.scopes


class SecurityEvent(BaseModel):
    """
    Security event logging for audit and monitoring
    """
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('password_change', 'Password Change'),
        ('mfa_enabled', 'MFA Enabled'),
        ('mfa_disabled', 'MFA Disabled'),
        ('user_locked', 'User Locked'),
        ('permission_denied', 'Permission Denied'),
        ('data_export', 'Data Export'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='security_events'
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='low')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'auth_security_events'
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class LoginAttempt(BaseModel):
    """
    Track login attempts for security monitoring
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_attempts'
    )
    
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    mfa_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Login {status} - {self.email} - {self.created_at}"