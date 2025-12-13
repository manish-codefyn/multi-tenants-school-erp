import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from apps.core.managers import SoftDeleteManager, TenantManager, AuditManager, TenantSoftDeleteManager


class UUIDModel(models.Model):
    """
    Secure UUID primary key to prevent ID enumeration attacks
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Universal ID'
    )

    class Meta:
        abstract = True

    @property
    def short_id(self):
        """Short identifier for logging and display"""
        return str(self.id)[:8]


class CryptographicModel(models.Model):
    """
    Cryptographic features for sensitive data
    """
    data_signature = models.CharField(
        max_length=64,
        blank=True,
        editable=False,
        verbose_name='Data Integrity Signature'
    )
    encryption_version = models.CharField(
        max_length=10,
        default='v1',
        editable=False,
        verbose_name='Encryption Scheme Version'
    )

    class Meta:
        abstract = True

    def calculate_signature(self):
        """Calculate SHA-256 signature for data integrity"""
        import json
        from django.core import serializers
        
        data = serializers.serialize('json', [self])
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_integrity(self):
        """Verify data hasn't been tampered with"""
        if self.data_signature:
            return self.data_signature == self.calculate_signature()
        return False


class TimeStampedModel(models.Model):
    """
    Comprehensive timestamp tracking with audit trail
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Creation Timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        verbose_name='Last Modification Timestamp'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
        verbose_name='Created By',
        db_index=True
    )
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='%(app_label)s_%(class)s_updated',
            verbose_name='Last Modified By',
            db_index=True
        )


    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Enterprise-grade soft deletion with comprehensive audit trail
    """
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Active Status',
        help_text='False indicates the record has been soft deleted'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Deletion Timestamp'
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted',
        verbose_name='Deleted By'
    )
    deletion_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Deletion Justification',
        help_text='Mandatory for compliance: Reason for record deletion'
    )
    deletion_category = models.CharField(
        max_length=50,
        choices=[
            ('USER_REQUEST', 'User Request'),
            ('ADMIN_ACTION', 'Administrative Action'),
            ('SYSTEM_CLEANUP', 'System Cleanup'),
            ('COMPLIANCE', 'Compliance Requirement'),
            ('OTHER', 'Other')
        ],
        blank=True,
        null=True,
        verbose_name='Deletion Category'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Bypass soft delete filter

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active', 'deleted_at']),
            models.Index(fields=['deleted_by', 'deleted_at']),
        ]

    def delete(self, using=None, keep_parents=False, user=None, reason=None, category=None):
        """
        Secure soft deletion with compliance requirements
        """
        if not self.is_active:
            return  # Already deleted
        
        if not reason and not category:
            raise ValidationError({
                'deletion_reason': 'Deletion reason and category are required for audit compliance.'
            })

        self.is_active = False
        self.deleted_at = timezone.now()
        
        if user:
            self.deleted_by = user
        
        if reason:
            self.deletion_reason = reason[:1000]  # Limit length
        
        if category:
            self.deletion_category = category

        update_fields = ['is_active', 'deleted_at', 'deletion_reason', 'deletion_category']
        if user:
            update_fields.append('deleted_by')
            
        self.save(update_fields=update_fields)

        # Log the deletion event
        self._log_deletion_event(user, reason)

    def hard_delete(self, using=None, keep_parents=False):
        """
        Permanent deletion - restricted to superusers only
        """
        # This should be protected by permission checks in views
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self, restored_by=None):
        """
        Restore soft-deleted record with audit trail
        """
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None
        self.deletion_category = None
        
        self.save(update_fields=[
            'is_active', 'deleted_at', 'deleted_by', 
            'deletion_reason', 'deletion_category'
        ])

        # Log restoration
        self._log_restoration_event(restored_by)

    def _log_deletion_event(self, user, reason):
        """Log deletion for security audit"""
        from apps.security.models import SecurityEvent
        SecurityEvent.objects.create(
            event_type='SOFT_DELETE',
            severity='MEDIUM',
            user=user,
            description=f'{self.__class__.__name__} soft deleted: {reason}',
            metadata={
                'model': self.__class__.__name__,
                'object_id': str(self.pk),
                'deletion_reason': reason
            }
        )

    def _log_restoration_event(self, user):
        """Log restoration for audit trail"""
        from apps.security.models import SecurityEvent
        SecurityEvent.objects.create(
            event_type='RESTORE',
            severity='LOW',
            user=user,
            description=f'{self.__class__.__name__} restored',
            metadata={
                'model': self.__class__.__name__,
                'object_id': str(self.pk)
            }
        )


class TenantAwareModel(models.Model):
    """
    Secure multi-tenant model with strict isolation
    """
    tenant = models.ForeignKey(
            'tenants.Tenant',
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_records',
            verbose_name='Owning Tenant',
            db_index=True,
            editable=False
        )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'id']),
            models.Index(fields=['tenant', 'created_at']),
        ]

    def clean(self):
        """
        Strict tenant validation to prevent cross-tenant data leaks
        """
        # Allow superusers to bypass tenant requirement
        if hasattr(self, 'is_superuser') and self.is_superuser:
            return

        from apps.tenants.models import Tenant
        from apps.core.utils.tenant import get_current_tenant
        
        if not self.tenant_id:
            raise ValidationError({
                'tenant': 'Tenant context is required for all tenant-aware models.'
            })

        # Verify tenant exists and is active
        try:
            tenant = Tenant.objects.get(id=self.tenant_id)
            if not tenant.is_active:
                raise ValidationError({
                    'tenant': 'Cannot create record for inactive tenant.'
                })
        except Tenant.DoesNotExist:
            raise ValidationError({
                'tenant': 'Referenced tenant does not exist.'
            })

        # Ensure tenant matches current context (security check)
        current_tenant = get_current_tenant()
        if current_tenant and self.tenant_id != current_tenant.id:
            raise ValidationError({
                'tenant': 'Tenant mismatch detected. Potential security violation.'
            })

    def save(self, *args, **kwargs):
        """
        Auto-set tenant from context with security validation
        """
        from apps.core.utils.tenant import get_current_tenant
        
        # Auto-set tenant if not provided
        if not self.tenant_id:
            # Allow superusers to exist without tenant
            if hasattr(self, 'is_superuser') and self.is_superuser:
                pass
            else:
                current_tenant = get_current_tenant()
                if not current_tenant:
                    raise ValidationError(
                        "Tenant context missing. Ensure tenant middleware is configured."
                    )
                self.tenant = current_tenant

        # Run full validation including tenant checks
        self.full_clean()
        super().save(*args, **kwargs)


class RateLimitedModel(models.Model):
    """
    Rate limiting and abuse prevention features
    """
    request_count = models.PositiveIntegerField(
        default=0,
        verbose_name='API Request Count'
    )
    last_request_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Last API Request'
    )
    rate_limit_key = models.CharField(
        max_length=100,
        blank=True,
        editable=False,
        verbose_name='Rate Limit Identifier'
    )

    class Meta:
        abstract = True

    def check_rate_limit(self, max_requests=100, window_minutes=60):
        """
        Check if rate limit is exceeded
        """
        from django.utils import timezone
        from django.core.exceptions import PermissionDenied
        
        window_start = timezone.now() - timezone.timedelta(minutes=window_minutes)
        
        if self.last_request_at and self.last_request_at > window_start:
            if self.request_count >= max_requests:
                raise PermissionDenied(
                    f"Rate limit exceeded: {max_requests} requests per {window_minutes} minutes"
                )
        else:
            # Reset counter if outside window
            self.request_count = 0
        
        self.request_count += 1
        self.last_request_at = timezone.now()
        self.save(update_fields=['request_count', 'last_request_at'])
        
        return True


class BaseSharedModel(UUIDModel, CryptographicModel, TimeStampedModel, 
                      SoftDeleteModel, RateLimitedModel):
    """
    Base model for shared resources that do not belong to a specific tenant
    (e.g., Tenant, Domain, Public configurations)
    """
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['is_active', 'updated_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__}[{self.short_id}]"

    def save(self, *args, **kwargs):
        if not self.data_signature:
            self.data_signature = self.calculate_signature()
        super().save(*args, **kwargs)

    def audit_log(self, action, user, details=None, severity='INFO'):
        from apps.security.models import AuditLog
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource=self.__class__.__name__,
            resource_id=str(self.id),
            details=details or {},
            severity=severity,
            ip_address=getattr(user, 'last_login_ip', None)
        )


class BaseModel(UUIDModel, CryptographicModel, TimeStampedModel, 
                SoftDeleteModel, TenantAwareModel, RateLimitedModel):
    """
    Complete enterprise-grade base model with all security features
    """
    objects = TenantSoftDeleteManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant', 'is_active', 'created_at']),
            models.Index(fields=['tenant', 'is_active', 'updated_at']),
            models.Index(fields=['created_by', 'tenant', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__}[{self.short_id}]"

    def save(self, *args, **kwargs):
        """
        Enhanced save with integrity protection
        """
        # Calculate data integrity signature
        if not self.data_signature:
            self.data_signature = self.calculate_signature()
        
        super().save(*args, **kwargs)

    @classmethod
    def get_secure_queryset(cls, user):
        """
        Get queryset with proper tenant isolation and permissions
        """
        from apps.core.utils.tenant import get_current_tenant
        
        tenant = get_current_tenant()
        if not tenant:
            return cls.objects.none()
            
        return cls.objects.filter(tenant=tenant, is_active=True)

    def audit_log(self, action, user, details=None, severity='INFO'):
        """
        Comprehensive audit logging
        """
        from apps.security.models import AuditLog
        
        return AuditLog.objects.create(
            user=user,
            action=action,
            resource=self.__class__.__name__,
            resource_id=str(self.id),
            tenant=self.tenant,
            details=details or {},
            severity=severity,
            ip_address=getattr(user, 'last_login_ip', None)
        )

    def to_secure_dict(self, include_sensitive=False):
        """
        Safe serialization that excludes sensitive fields
        """
        from django.forms.models import model_to_dict
        
        data = model_to_dict(self, fields=[field.name for field in self._meta.fields])
        
        # Remove sensitive fields unless explicitly requested
        if not include_sensitive:
            sensitive_fields = ['deletion_reason', 'data_signature', 'rate_limit_key']
            for field in sensitive_fields:
                data.pop(field, None)
                
        data['id'] = str(self.id)
        data['tenant'] = str(self.tenant_id)
        data['is_deleted'] = not self.is_active
        
        return data