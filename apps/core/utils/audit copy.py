
import uuid
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.core.managers import (
    SoftDeleteManager,
    TenantManager,
    AuditManager,
    TenantSoftDeleteManager,
)


User = get_user_model()



class AuditLog(models.Model):
    """Audit logging model matching the AuditService"""
    
    class AuditSeverity(models.TextChoices):
        DEBUG = 'DEBUG', 'Debug'
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CRITICAL = 'CRITICAL', 'Critical'
    
    class AuditAction(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        READ = 'READ', 'Read'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        SOFT_DELETE = 'SOFT_DELETE', 'Soft Delete'
        RESTORE = 'RESTORE', 'Restore'
        EXPORT = 'EXPORT', 'Export'
        IMPORT = 'IMPORT', 'Import'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Change'
        PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Permission Change'
        TENANT_SWITCH = 'TENANT_SWITCH', 'Tenant Switch'
        BULK_OPERATION = 'BULK_OPERATION', 'Bulk Operation'
        API_CALL = 'API_CALL', 'API Call'
    
    class AuditStatus(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # User Information (as strings, not foreign keys)
    user_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    user_email = models.EmailField(null=True, blank=True, db_index=True)
    user_display_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Action Information
    action = models.CharField(max_length=50, choices=AuditAction.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=AuditSeverity.choices, default=AuditSeverity.INFO)
    status = models.CharField(max_length=20, choices=AuditStatus.choices, default=AuditStatus.SUCCESS)
    
    # Resource Information
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    resource_name = models.CharField(max_length=500, null=True, blank=True)
    
    # Changes and State
    changes = models.JSONField(null=True, blank=True)
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    
    # Request Information
    request_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    request_path = models.CharField(max_length=500, null=True, blank=True)
    
    # Error Information
    error_message = models.TextField(null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)
    
    # Tenant Information
    tenant_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    tenant_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Performance
    duration_ms = models.FloatField(null=True, blank=True)
    
    # Generic Foreign Key for related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_uuid = models.CharField(max_length=100, null=True, blank=True)  # Changed from object_id
    content_object = GenericForeignKey('content_type', 'object_uuid')
    
    # Extra data
    extra_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user_email', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['tenant_id', 'timestamp']),
            models.Index(fields=['request_id']),
            models.Index(fields=['session_id']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.user_email or 'System'} - {self.action} - {self.resource_type}"
