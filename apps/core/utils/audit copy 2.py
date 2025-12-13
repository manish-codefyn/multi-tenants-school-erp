
import json
import uuid
import traceback
import hashlib
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.core import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.tenants.models import Tenant
from apps.core.managers import AuditTrailManager

User = get_user_model()

class AuditSeverity:
    """Audit severity levels"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class AuditAction:
    """Audit action types aligned with your base model patterns"""
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
    API_CALL = 'API_CALL'  # Added missing action

# AuditLog model moved to apps.core.models
from apps.core.models import AuditLog



# Rest of your functions continue here...
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
    Create an audit log entry with enhanced features
    
    Args:
        action (str): Audit action
        resource_type (str): Type of resource
        user (User): Django user
        request (HttpRequest): Django request
        instance (Model): Model instance
        resource_id (str): Resource ID
        resource_name (str): Resource name
        changes (dict): Field changes
        previous_state (dict): Previous state
        new_state (dict): New state
        details (dict): Additional details
        severity (str): Severity level
        status (str): Status
        error_message (str): Error message
        tenant_id (str): Tenant ID
        session_id (str): Session ID
        request_id (str): Request ID
        source (str): Source system
        channel (str): Channel
        tags (list): Tags for categorization
        duration_ms (float): Duration in ms
        **kwargs: Additional metadata
    """
    try:
        from django.contrib.auth.models import AnonymousUser
        import uuid as uuid_lib
        
        # Prepare user info
        user_email = None
        user_role = None
        user_department = None
        user_obj = None
        
        if user:
            if isinstance(user, str):
                user_email = user
            elif not isinstance(user, AnonymousUser):
                user_email = getattr(user, 'email', None) or getattr(user, 'username', None)
                user_obj = user if hasattr(user, 'id') else None
                
                # Get additional user info
                user_role = getattr(user, 'role', None) or ', '.join(user.groups.values_list('name', flat=True))
                user_department = getattr(user, 'department', None)
        
        # Prepare resource info from instance if provided
        if instance and not resource_id:
            resource_id = str(getattr(instance, 'id', None))
        
        if instance and not resource_name:
            resource_name = str(instance)
        
        # Get tenant info
        tenant_name = None
        if tenant_id:
            try:
                from apps.tenants.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
                tenant_name = tenant.name
            except:
                pass
        
        # Prepare request info
        request_path = None
        request_method = None
        user_ip = None
        user_agent = None
        request_query = None
        
        if request:
            request_path = request.path
            request_method = request.method
            user_ip = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            request_query = dict(request.GET)
        
        # Generate IDs if not provided
        if not session_id and request and hasattr(request, 'session'):
            session_id = request.session.session_key
        
        if not request_id:
            request_id = str(uuid_lib.uuid4())[:32]
        
        # Calculate diff if changes not provided
        if changes is None and previous_state and new_state:
            changes = _calculate_diff(previous_state, new_state)
        
        # Create metadata
        metadata = {
            'python_version': kwargs.get('python_version'),
            'django_version': kwargs.get('django_version'),
            'app_version': kwargs.get('app_version'),
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        # Combine all details
        all_details = details or {}
        if kwargs:
            # Add remaining kwargs to details
            remaining_kwargs = {k: v for k, v in kwargs.items() if k not in [
                'python_version', 'django_version', 'app_version'
            ]}
            all_details.update(remaining_kwargs)
        
        # Create audit log entry
        audit_entry = AuditLog.objects.create(
            # User Information
            user=user_obj,
            user_email=user_email,
            user_role=user_role,
            user_department=user_department,
            
            # Session and Request
            session_id=session_id,
            request_id=request_id,
            user_ip=user_ip,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            request_query=request_query,
            
            # Action Details
            action=action,
            severity=severity,
            
            # Resource Information
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            
            # Changes and State
            changes=changes,
            previous_state=previous_state,
            new_state=new_state,
            diff_summary=_generate_diff_summary(changes) if changes else None,
            
            # Context
            details=all_details if all_details else None,
            metadata=metadata if metadata else None,
            tags=tags,
            
            # Performance
            duration_ms=duration_ms,
            
            # Status
            status=status,
            error_message=error_message,
            stack_trace=traceback.format_exc() if error_message else None,
            
            # Tenant
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            
            # Source
            source=source,
            channel=channel,
        )
        
        # Link to content object if possible
        if instance and hasattr(instance, 'id'):
            content_type = ContentType.objects.get_for_model(instance.__class__)
            audit_entry.content_type = content_type
            audit_entry.object_id = instance.id
            audit_entry.save(update_fields=['content_type', 'object_id'])
        
        # Log to console in development
        if settings.DEBUG:
            print(f"[AUDIT] {audit_entry.timestamp} - {user_email or 'System'} - {action} - {resource_type}")
        
        return audit_entry
        
    except Exception as e:
        # Fallback logging if database is not available
        error_msg = f"Error creating audit log: {str(e)}"
        print(error_msg)
        
        # Try to log to file as fallback
        try:
            import logging
            logging.getLogger('audit').error(error_msg)
        except:
            pass
        
        return None


# Helper functions for common audit scenarios
def log_creation(user, instance, request=None, **kwargs):
    """Log creation of an instance"""
    return audit_log(
        action=AuditAction.CREATE,
        resource_type=instance.__class__.__name__,
        user=user,
        request=request,
        instance=instance,
        resource_id=instance.pk,
        resource_name=str(instance),
        new_state=_serialize_instance(instance),
        **kwargs
    )


def log_update(user, instance, old_instance=None, changes=None, request=None, **kwargs):
    """Log update of an instance"""
    if changes is None and old_instance:
        changes = _get_changes(old_instance, instance)
    
    return audit_log(
        action=AuditAction.UPDATE,
        resource_type=instance.__class__.__name__,
        user=user,
        request=request,
        instance=instance,
        resource_id=instance.pk,
        resource_name=str(instance),
        changes=changes,
        previous_state=_serialize_instance(old_instance) if old_instance else None,
        new_state=_serialize_instance(instance),
        **kwargs
    )


def log_deletion(user, instance, request=None, hard_delete=False, **kwargs):
    """Log deletion of an instance"""
    action = AuditAction.DELETE if hard_delete else AuditAction.SOFT_DELETE
    
    return audit_log(
        action=action,
        resource_type=instance.__class__.__name__,
        user=user,
        request=request,
        instance=instance,
        resource_id=instance.pk,
        resource_name=str(instance),
        previous_state=_serialize_instance(instance),
        details={
            'hard_delete': hard_delete,
            'deletion_time': timezone.now().isoformat()
        },
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
        resource_id=instance.pk,
        resource_name=str(instance),
        new_state=_serialize_instance(instance),
        **kwargs
    )


def log_login(user, request, status='SUCCESS', error_message=None, **kwargs):
    """Log user login"""
    return audit_log(
        action=AuditAction.LOGIN if status == 'SUCCESS' else AuditAction.LOGIN_FAILED,
        resource_type='User',
        user=user,
        request=request,
        resource_id=user.pk if user else None,
        resource_name=user.email if user else 'Unknown',
        status=status,
        error_message=error_message,
        details={
            'login_time': timezone.now().isoformat(),
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else None
        },
        **kwargs
    )


def log_logout(user, request, **kwargs):
    """Log user logout"""
    return audit_log(
        action=AuditAction.LOGOUT,
        resource_type='User',
        user=user,
        request=request,
        resource_id=user.pk if user else None,
        resource_name=user.email if user else 'Unknown',
        details={'logout_time': timezone.now().isoformat()},
        **kwargs
    )


def log_tenant_switch(user, from_tenant, to_tenant, request=None, **kwargs):
    """Log tenant switching"""
    return audit_log(
        action=AuditAction.TENANT_SWITCH,
        resource_type='Tenant',
        user=user,
        request=request,
        details={
            'from_tenant': {
                'id': str(from_tenant.id) if from_tenant else None,
                'name': from_tenant.name if from_tenant else None
            },
            'to_tenant': {
                'id': str(to_tenant.id),
                'name': to_tenant.name
            },
            'switch_time': timezone.now().isoformat()
        },
        tenant_id=to_tenant.id,
        **kwargs
    )


# Utility functions
def _get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _serialize_instance(instance):
    """Serialize model instance to dict"""
    if not instance:
        return None
    
    try:
        data = {}
        for field in instance._meta.fields:
            field_name = field.name
            try:
                value = getattr(instance, field_name)
                
                # Handle special field types
                if hasattr(value, 'pk'):
                    data[field_name] = str(value.pk)
                elif isinstance(value, (datetime, timezone.datetime)):
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


def _get_changes(old_instance, new_instance):
    """Get changed fields between two instances"""
    changes = {}
    
    for field in new_instance._meta.fields:
        field_name = field.name
        
        # Skip sensitive fields
        sensitive_fields = ['password', 'secret_key', 'api_key', 'token']
        if field_name in sensitive_fields:
            continue
        
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(new_instance, field_name, None)
        
        # Skip if values are equal
        if old_value == new_value:
            continue
        
        # Handle special field types
        if hasattr(old_value, 'pk'):
            old_value = str(old_value.pk)
        if hasattr(new_value, 'pk'):
            new_value = str(new_value.pk)
        
        changes[field_name] = {
            'old': old_value,
            'new': new_value
        }
    
    return changes if changes else None


def _calculate_diff(old_state, new_state):
    """Calculate difference between two states"""
    diff = {}
    
    all_keys = set(old_state.keys()) | set(new_state.keys())
    
    for key in all_keys:
        old_val = old_state.get(key)
        new_val = new_state.get(key)
        
        if old_val != new_val:
            diff[key] = {
                'old': old_val,
                'new': new_val
            }
    
    return diff if diff else None


def _generate_diff_summary(changes):
    """Generate human-readable diff summary"""
    if not changes:
        return None
    
    summary = []
    for field, change in changes.items():
        summary.append(f"{field}: {change.get('old')} → {change.get('new')}")
    
    return "; ".join(summary)


# Middleware for automatic request logging
class AuditMiddleware:
    """Middleware to automatically log requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import time
        
        # Skip certain paths
        skip_paths = ['/health/', '/static/', '/media/', '/favicon.ico']
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)
        
        # Start timer
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log API calls (skip for non-authenticated users or certain methods)
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                audit_log(
                    action=AuditAction.API_CALL,
                    resource_type='API',
                    user=request.user,
                    request=request,
                    details={
                        'response_status': response.status_code,
                        'response_content_type': response.get('Content-Type', ''),
                        'request_body_size': len(request.body) if hasattr(request, 'body') else 0,
                        'response_size': len(response.content) if hasattr(response, 'content') else 0,
                    },
                    severity=AuditSeverity.INFO if response.status_code < 400 else AuditSeverity.WARNING,
                    status='SUCCESS' if response.status_code < 400 else 'FAILED',
                    duration_ms=duration_ms,
                    source='API_MIDDLEWARE'
                )
            except Exception as e:
                # Don't break the request if audit logging fails
                if settings.DEBUG:
                    print(f"Audit middleware error: {str(e)}")
        
        return response