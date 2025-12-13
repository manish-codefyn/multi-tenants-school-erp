
import traceback
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
import uuid

from apps.core.services.audit_service import AuditService

User = get_user_model()



# Audit action constants for backward compatibility
class AuditAction:
    CREATE = 'CREATE'
    READ = 'READ'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    SOFT_DELETE = 'SOFT_DELETE'
    RESTORE = 'RESTORE'
    EXPORT = 'EXPORT'
    IMPORT = 'IMPORT'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    LOGIN_FAILED = 'LOGIN_FAILED'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    PERMISSION_CHANGE = 'PERMISSION_CHANGE'
    TENANT_SWITCH = 'TENANT_SWITCH'
    BULK_OPERATION = 'BULK_OPERATION'
    API_CALL = 'API_CALL'

# Audit severity constants
class AuditSeverity:
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


def audit_log(
    action,
    resource_type,
    user=None,
    request=None,
    instance=None,
    resource_id=None,
    resource_name=None,
    changes=None,
    previous_state=None,
    new_state=None,
    details=None,
    severity='INFO',
    status='SUCCESS',
    error_message=None,
    tenant_id=None,
    session_id=None,
    request_id=None,
    source='WEB',
    channel=None,
    tags=None,
    duration_ms=None,
    **kwargs
):
    """
    Wrapper function for backward compatibility with AuditService
    
    Args:
        All the same arguments as before
    """
    try:
        # Convert details to extra_data for AuditService
        extra_data = details or {}
        
        # Add any additional kwargs to extra_data
        if kwargs:
            extra_data.update(kwargs)
        
        # Map source to extra_data (since AuditLog model doesn't have source field)
        if source and source != 'WEB':
            extra_data['source'] = source
        
        if channel:
            extra_data['channel'] = channel
        
        if tags:
            extra_data['tags'] = tags
        
        # Use AuditService to create the audit entry
        return AuditService.create_audit_entry(
            action=action,
            resource_type=resource_type,
            user=user,
            request=request,
            instance=instance,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            previous_state=previous_state,
            new_state=new_state,
            severity=severity,
            status=status,
            error_message=error_message,
            tenant_id=tenant_id,
            duration_ms=duration_ms,
            extra_data=extra_data
        )
    except Exception as e:
        if settings.DEBUG:
            print(f"[AUDIT LOG ERROR] {str(e)}")
            traceback.print_exc()
        return None


# Helper functions for backward compatibility
def log_creation(user, instance, request=None, **kwargs):
    """Log creation of an instance"""
    return AuditService.log_creation(
        user=user,
        instance=instance,
        request=request,
        **kwargs
    )


def log_update(user, instance, old_instance=None, changes=None, request=None, **kwargs):
    """Log update of an instance"""
    return AuditService.log_update(
        user=user,
        instance=instance,
        old_instance=old_instance,
        request=request,
        **kwargs
    )


def log_deletion(user, instance, request=None, hard_delete=False, **kwargs):
    """Log deletion of an instance"""
    return AuditService.log_deletion(
        user=user,
        instance=instance,
        request=request,
        hard_delete=hard_delete,
        **kwargs
    )


def log_restoration(user, instance, request=None, **kwargs):
    """Log restoration of soft-deleted instance"""
    return audit_log(
        action=AuditAction.RESTORE,
        resource_type=instance.__class__.__name__,
        user=user,
        request=request,
        instance=instance,
        resource_id=instance.id,
        resource_name=str(instance),
        **kwargs
    )


def log_login(user, request, status='SUCCESS', error_message=None, **kwargs):
    """Log user login"""
    action = AuditAction.LOGIN if status == 'SUCCESS' else AuditAction.LOGIN_FAILED
    
    return audit_log(
        action=action,
        resource_type='User',
        user=user,
        request=request,
        resource_id=getattr(user, 'id', None) if user else None,
        resource_name=getattr(user, 'email', None) or getattr(user, 'username', None) if user else 'Unknown',
        status=status,
        error_message=error_message,
        **kwargs
    )


def log_logout(user, request, **kwargs):
    """Log user logout"""
    return audit_log(
        action=AuditAction.LOGOUT,
        resource_type='User',
        user=user,
        request=request,
        resource_id=getattr(user, 'id', None) if user else None,
        resource_name=getattr(user, 'email', None) or getattr(user, 'username', None) if user else 'Unknown',
        **kwargs
    )


def log_tenant_switch(user, from_tenant, to_tenant, request=None, **kwargs):
    """Log tenant switching"""
    return audit_log(
        action=AuditAction.TENANT_SWITCH,
        resource_type='Tenant',
        user=user,
        request=request,
        tenant_id=to_tenant.id,
        details={
            'from_tenant': {
                'id': str(from_tenant.id) if from_tenant else None,
                'name': from_tenant.name if from_tenant else None
            },
            'to_tenant': {
                'id': str(to_tenant.id),
                'name': to_tenant.name
            }
        },
        **kwargs
    )


# Utility functions
def _get_client_ip(request):
    """Extract client IP from request"""
    return AuditService.get_client_ip(request)


def _serialize_instance(instance):
    """Serialize model instance to dict"""
    if not instance:
        return None
    
    try:
        from django.utils import timezone
        from django.db import models
        
        data = {}
        for field in instance._meta.fields:
            field_name = field.name
            try:
                value = getattr(instance, field_name)
                
                # Handle special field types
                if hasattr(value, 'pk'):
                    data[field_name] = str(value.pk)
                elif isinstance(value, (timezone.datetime,)):
                    data[field_name] = value.isoformat()
                elif isinstance(value, models.Model):
                    data[field_name] = str(value)
                else:
                    data[field_name] = value
            except:
                pass
        return data
    except:
        return {'__str__': str(instance)}