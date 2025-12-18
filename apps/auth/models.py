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
    # Updated Role definitions
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
        ('super_admin', 'Super Administrator'),
        ('principal', 'Principal'),
        ('headmaster', 'Headmaster'),
        ('accountant', 'Accountant'),
        ('librarian', 'Librarian'),
        ('parent', 'Parent'),
        ('guardian', 'Guardian'),
        ('counselor', 'Counselor'),
        ('supervisor', 'Supervisor'),
        ('vice_principal', 'Vice Principal'),
        ('department_head', 'Department Head'),
        ('clerk', 'Clerk'),
        ('hr', 'Human Resources'),
        ('it_staff', 'IT Staff'),
        ('lab_assistant', 'Lab Assistant'),
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
    
    # Module/App context for permissions
    module = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    
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
    def get_permissions_with_modules(cls, role, tenant=None):
        """
        Get permissions grouped by module
        """
        permissions = cls.get_permissions_for_role(role, tenant)
        modules = {}
        
        for perm_codename in permissions:
            if '.' in perm_codename:
                app_label, perm_name = perm_codename.split('.', 1)
                if app_label not in modules:
                    modules[app_label] = []
                modules[app_label].append(perm_name)
        
        return modules

    @classmethod
    def assign_permission_to_role(cls, role, permission_codename, tenant=None, module=None):
        """
        Assign a permission to a role
        """
        try:
            permission = Permission.objects.get(codename=permission_codename)
            role_perm, created = cls.objects.get_or_create(
                role=role,
                permission=permission,
                tenant=tenant,
                defaults={
                    'tenant_specific': bool(tenant),
                    'module': module
                }
            )
            return role_perm
        except Permission.DoesNotExist:
            # If permission doesn't exist, create it
            app_label, codename = permission_codename.split('.', 1) if '.' in permission_codename else ('auth', permission_codename)
            
            try:
                content_type = ContentType.objects.filter(app_label=app_label).first()
                if content_type:
                    permission, created = Permission.objects.get_or_create(
                        codename=codename,
                        content_type=content_type,
                        defaults={'name': f'Can {codename.replace("_", " ")}'}
                    )
                    
                    role_perm, created = cls.objects.get_or_create(
                        role=role,
                        permission=permission,
                        tenant=tenant,
                        defaults={
                            'tenant_specific': bool(tenant),
                            'module': module
                        }
                    )
                    return role_perm
            except Exception as e:
                print(f"Error creating permission {permission_codename}: {e}")
                return None

    @classmethod
    def create_default_permissions(cls, tenant=None):
        """
        Create default permission sets for each role
        """
        # First, ensure basic Django permissions exist
        from django.contrib.auth.management import create_permissions
        
        from django.apps import apps
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)
            app_config.models_module = None
        
        # Default permissions for each role by module
        # Note: These permissions should be in format 'app_label.permission_codename'
        role_permissions = {
            'student': {
                'auth': ['auth.view_user', 'auth.change_user'],
                'academics': ['academics.view_subject', 'academics.view_timetable', 'academics.view_studymaterial', 'academics.view_academics'],
                'attendance': ['attendance.view_studentattendance'],
                'library': ['library.view_book', 'library.view_borrowing'],
                'events': ['events.view_event'],
                'exams': ['exams.view_exam', 'exams.view_examresult'],
                'students': ['students.view_student'],
            },
            'parent': {
                'auth': ['auth.view_user'],
                'academics': ['academics.view_subject', 'academics.view_timetable', 'academics.view_studymaterial'],
                'attendance': ['attendance.view_studentattendance'],
                'events': ['events.view_event'],
                'exams': ['exams.view_exam', 'exams.view_examresult'],
                'finance': ['finance.view_invoice', 'finance.view_payment'],
                'students': ['students.view_student'],
            },
            'teacher': {
                'auth': ['auth.view_user'],
                'academics': ['academics.view_subject', 'academics.view_timetable', 'academics.view_studymaterial', 'academics.add_studymaterial', 'academics.change_studymaterial', 'academics.view_academics'],
                'attendance': ['attendance.view_studentattendance', 'attendance.add_studentattendance', 'attendance.change_studentattendance', 'attendance.view_attendance'],
                'events': ['events.view_event'],
                'exams': ['exams.view_exam', 'exams.view_examresult', 'exams.add_examresult', 'exams.change_examresult'],
                'students': ['students.view_student', 'students.view_studentdocument'],
                'library': ['library.view_book'],
            },
            'accountant': {
                'auth': ['auth.view_user'],
                'finance': ['finance.view_feestructure', 'finance.add_feestructure', 'finance.change_feestructure', 
                           'finance.view_invoice', 'finance.add_invoice', 'finance.change_invoice',
                           'finance.view_payment', 'finance.add_payment', 'finance.change_payment',
                           'finance.view_expense', 'finance.add_expense', 'finance.change_expense',
                           'finance.view_budget', 'finance.view_finance'],
                'students': ['students.view_student'],
            },
            'librarian': {
                'auth': ['auth.view_user'],
                'library': ['library.view_book', 'library.add_book', 'library.change_book', 'library.delete_book',
                           'library.view_borrowing', 'library.add_borrowing', 'library.change_borrowing',
                           'library.view_library'],
                'students': ['students.view_student'],
                'hr': ['hr.view_staff'],
            },
            'hr': {
                 'auth': ['auth.view_user', 'auth.add_user', 'auth.change_user', 'users.view_user', 'users.add_user', 'users.change_user'],
                 'hr': ['hr.view_staff', 'hr.add_staff', 'hr.change_staff', 'hr.view_department', 'hr.view_jobposition', 
                        'hr.view_leaveapplication', 'hr.add_leaveapplication', 'hr.change_leaveapplication', 'hr.view_attendance', 'hr.view_hr'],
                 'attendance': ['attendance.view_staffattendance', 'attendance.add_staffattendance', 'attendance.change_staffattendance'],
                 'tenants': ['tenants.view_tenant'], 
            },
            'principal': {
                'auth': ['auth.view_user', 'auth.change_user', 'auth.view_group', 'users.view_user', 'users.change_user'],
                'academics': ['academics.view_subject', 'academics.view_timetable', 'academics.view_studymaterial', 'academics.view_academics'],
                'admission': ['admission.view_admissionapplication', 'admission.change_admissionapplication'],
                'attendance': ['attendance.view_studentattendance', 'attendance.view_staffattendance', 'attendance.view_attendance'],
                'events': ['events.view_event', 'events.add_event', 'events.change_event', 'events.delete_event'],
                'exams': ['exams.view_exam', 'exams.view_examresult'],
                'finance': ['finance.view_feestructure', 'finance.view_invoice', 'finance.view_payment', 'finance.view_budget', 'finance.view_finance'],
                'hr': ['hr.view_staff', 'hr.view_leaveapplication', 'hr.change_leaveapplication', 'hr.view_hr'],
                'library': ['library.view_book', 'library.view_borrowing'],
                'students': ['students.view_student', 'students.view_studentdocument', 'students.view_student_dashboard'],
                'reports': ['reports.view_report', 'analytics.view_dashboard'],
                'configuration': ['configuration.view_systemsetting'],
                'communications': ['communications.view_message', 'communications.add_message'],
            },
            'admin': {
                '*': ['*'],  # Admin gets all permissions via special handling in iteration
            },
            'super_admin': {
                '*': ['*'],  # Super admin gets everything
            },
            'staff': {  # General staff fallback
                'auth': ['auth.view_user'],
                'events': ['events.view_event'],
            }
        }
        
        print(f"Creating default permissions for tenant: {tenant}")
        
        # Track created permissions
        created_count = 0
        skipped_count = 0
        
        for role, modules in role_permissions.items():
            if role == 'admin' or role == 'super_admin':
                # Special handling for admin roles - they get all permissions
                continue
                
            for module, permissions in modules.items():
                for perm_codename in permissions:
                    result = cls.assign_permission_to_role(role, perm_codename, tenant, module)
                    if result:
                        created_count += 1
                    else:
                        skipped_count += 1
        
        print(f"Created {created_count} permissions, skipped {skipped_count}")
        
        # For admin and super_admin, assign all existing permissions
        all_permissions = Permission.objects.all()
        for role in ['admin', 'super_admin']:
            for permission in all_permissions:
                role_perm, created = cls.objects.get_or_create(
                    role=role,
                    permission=permission,
                    tenant=tenant,
                    defaults={
                        'tenant_specific': bool(tenant),
                        'module': '*'
                    }
                )
                if created:
                    created_count += 1
        
        print(f"Total permissions created: {created_count}")
        return created_count


        
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