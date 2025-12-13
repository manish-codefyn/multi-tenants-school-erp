from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
import pyotp
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets
from encrypted_model_fields.fields import EncryptedCharField
from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    """
    Custom user manager with tenant support
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        from apps.core.utils.tenant import get_current_tenant
        current_tenant = get_current_tenant()
        
        if current_tenant:
            return queryset.filter(tenant=current_tenant)
        return queryset

    def create_user(self, email, password=None, tenant=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        # Allow tenant to be None if it's a superuser
        if not tenant and not extra_fields.get('is_superuser'):
            raise ValueError('The Tenant field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, tenant=tenant, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, tenant=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, tenant, **extra_fields)




class User(AbstractUser, BaseModel):
    """
    Enhanced User model with tenant relationship and role-based permissions
    """
    # Remove username, use email as primary identifier
    username = None
    email = models.EmailField(unique=True, db_index=True)
    
    # Role & Permissions
    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher' 
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'
    ROLE_SUPER_ADMIN = 'super_admin'

    # NEW ROLES
    ROLE_PRINCIPAL = 'principal'
    ROLE_HEADMASTER = 'headmaster'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_LIBRARIAN = 'librarian'
    ROLE_PARENT = 'parent'
    ROLE_GUARDIAN = 'guardian'
    ROLE_COUNSELOR = 'counselor'
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_VICE_PRINCIPAL = 'vice_principal'
    ROLE_DEPARTMENT_HEAD = 'department_head'
    ROLE_CLERK = 'clerk'
    ROLE_HR = 'hr'
    ROLE_IT_STAFF = 'it_staff'
    ROLE_LAB_ASSISTANT = 'lab_assistant'

    # NEW: Add Applicant/Admission Seeker role
    ROLE_APPLICANT = 'applicant'

    # Categorized Role Groups (Updated with ROLE_APPLICANT)
    ACADEMIC_ROLES = [ROLE_TEACHER, ROLE_LIBRARIAN, ROLE_COUNSELOR, ROLE_LAB_ASSISTANT]
    ADMINISTRATIVE_ROLES = [ROLE_STAFF, ROLE_ACCOUNTANT, ROLE_CLERK, ROLE_HR, ROLE_IT_STAFF]
    LEADERSHIP_ROLES = [ROLE_PRINCIPAL, ROLE_HEADMASTER, ROLE_VICE_PRINCIPAL, ROLE_DEPARTMENT_HEAD, ROLE_SUPERVISOR]
    STUDENT_FAMILY_ROLES = [ROLE_APPLICANT, ROLE_STUDENT, ROLE_PARENT, ROLE_GUARDIAN]  # Updated
    SYSTEM_ROLES = [ROLE_ADMIN, ROLE_SUPER_ADMIN]

    ROLE_HIERARCHY = {
        ROLE_APPLICANT: 0,  # Lowest hierarchy for applicants
        ROLE_STUDENT: 1,
        ROLE_PARENT: 2,
        ROLE_GUARDIAN: 2,
        ROLE_LAB_ASSISTANT: 3,
        ROLE_LIBRARIAN: 4,
        ROLE_COUNSELOR: 4,
        ROLE_TEACHER: 5,
        ROLE_CLERK: 6,
        ROLE_IT_STAFF: 6,
        ROLE_HR: 6,
        ROLE_ACCOUNTANT: 7,
        ROLE_STAFF: 7,
        ROLE_SUPERVISOR: 8,
        ROLE_DEPARTMENT_HEAD: 9,
        ROLE_VICE_PRINCIPAL: 10,
        ROLE_PRINCIPAL: 11,
        ROLE_HEADMASTER: 12,
        ROLE_ADMIN: 13,
        ROLE_SUPER_ADMIN: 14,
    }

    ROLE_CHOICES = [
        (ROLE_APPLICANT, 'Applicant/Admission Seeker'),  # NEW
        (ROLE_STUDENT, 'Student'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STAFF, 'Staff'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_SUPER_ADMIN, 'Super Administrator'),
        (ROLE_PRINCIPAL, 'Principal'),
        (ROLE_HEADMASTER, 'Headmaster'),
        (ROLE_ACCOUNTANT, 'Accountant'),
        (ROLE_LIBRARIAN, 'Librarian'),
        (ROLE_PARENT, 'Parent'),
        (ROLE_GUARDIAN, 'Guardian'),
        (ROLE_COUNSELOR, 'Counselor'),
        (ROLE_SUPERVISOR, 'Supervisor'),
        (ROLE_VICE_PRINCIPAL, 'Vice Principal'),
        (ROLE_DEPARTMENT_HEAD, 'Department Head'),
        (ROLE_CLERK, 'Clerk'),
        (ROLE_HR, 'Human Resources'),
        (ROLE_IT_STAFF, 'IT Staff'),
        (ROLE_LAB_ASSISTANT, 'Lab Assistant'),
    ]

    # TENANT RELATIONSHIP - FIXED
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Organization',
        null=True,
        blank=True
    )
    
    
    # Enhanced Personal Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Security & Verification
    is_verified = models.BooleanField(default=False, db_index=True)
    verification_token = models.CharField(max_length=64, blank=True, editable=False)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = EncryptedCharField(max_length=32, blank=True, null=True)
    
    # Login Security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    current_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    
    # Profile
    avatar = models.ImageField(upload_to='user_avatars/', null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Role field with NULL as default (allowing no role assignment initially)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        null=True,  # Allow NULL
        blank=True,  # Allow blank in forms
        db_index=True
    )
        
    # Academic Information
    student_id = models.CharField(max_length=50, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Custom manager
    objects = UserManager()

    # Set email as username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta(BaseModel.Meta):
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'tenant'],
                name='unique_email_per_tenant',
                condition=models.Q(tenant__isnull=False)
            ),
        ]
    

    def __str__(self):
        role_display = self.get_role_display() if self.role else "No Role"
        return f"{self.get_full_name()} ({self.email}) - {role_display}"

    def clean(self):
        super().clean()
        
        # Require tenant for non-superusers
        if not self.tenant and not self.is_superuser:
            from django.core.exceptions import ValidationError
            raise ValidationError({'tenant': 'Tenant is required for regular users'})
        
        # For superusers, allow no role
        if not self.is_superuser and not self.role:
            # Allow no role temporarily during signup, but require it before verification
            # or when the user becomes active
            pass
            
        # Email uniqueness is now scoped to tenant via unique_together

    @property
    def has_role(self):
        """Check if user has a role assigned"""
        return self.role is not None

    @property
    def is_applicant(self):
        """Check if user is an applicant"""
        return self.role == self.ROLE_APPLICANT

    @property
    def get_role_display(self):
        """Custom get_role_display that handles None role"""
        if not self.role:
            return "Pending Role Assignment"
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def set_role(self, role, save=True):
        """Helper method to set role with validation"""
        if role not in dict(self.ROLE_CHOICES).keys():
            raise ValueError(f"Invalid role: {role}")
        
        self.role = role
        if save:
            self.save(update_fields=['role'])
    
    @property
    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False

    def set_password(self, raw_password):
        """Enhanced password setting"""
        super().set_password(raw_password)
        self.password_changed_at = timezone.now()
        self.failed_login_attempts = 0
        self.locked_until = None

    def get_role_permissions(self):
        """Get permissions based on role"""
        from apps.auth.models import RolePermission
        if not self.role:
            # Return minimal permissions for users without a role
            return []
        return RolePermission.get_permissions_for_role(self.role)

    def has_perm(self, perm, obj=None):
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        
        if not self.role:
            # Users without a role have minimal permissions
            return False
            
        user_perms = self.get_role_permissions()
        return perm in user_perms

    def has_module_perms(self, app_label):
        """Check if user has any permissions in the given app"""
        if self.is_superuser:
            return True
        
        if not self.role:
            # Users without a role have no module permissions
            return False
            
        user_perms = self.get_role_permissions()
        return any(perm.startswith(f"{app_label}.") for perm in user_perms)
    

    def generate_verification_token(self):
        """Generate email verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['verification_token'])
        return self.verification_token

    def send_verification_email(self):
        """Send email verification message"""
        token = self.generate_verification_token()
        
        subject = 'Verify Your Email Address'
        html_message = render_to_string('emails/verify_email.html', {
            'user': self,
            'verification_token': token,
            'tenant': self.tenant,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            'noreply@erpsystem.com',
            [self.email],
            html_message=html_message,
            fail_silently=False,
        )

    def generate_password_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_created = timezone.now()
        self.save(update_fields=['password_reset_token', 'password_reset_token_created'])
        return self.password_reset_token

    def generate_mfa_secret(self):
        """Generate MFA secret"""
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
            self.save(update_fields=['mfa_secret'])
        return self.mfa_secret

    def get_mfa_provisioning_uri(self):
        """Get MFA provisioning URI for authenticator apps"""
        if not self.mfa_secret:
            self.generate_mfa_secret()
        
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,
            issuer_name=f"{self.tenant.name} ERP"
        )

    def verify_mfa_token(self, token):
        """Verify MFA token"""
        if not self.mfa_secret:
            return False
        
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token)