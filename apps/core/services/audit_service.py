# apps/core/services/audit_service.py
import uuid
import json
import traceback
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from apps.tenants.models import Tenant
from apps.core.models import AuditLog

User = get_user_model()


class AuditService:
    """
    Professional audit logging service that matches the AuditLog model
    """
    
    @classmethod
    def get_client_ip(cls, request: HttpRequest) -> Optional[str]:
        """Safely extract client IP address"""
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        except:
            return None
    
    @classmethod
    def get_user_info(cls, user) -> Dict[str, Any]:
        """Extract user information matching AuditLog model fields"""
        if not user or isinstance(user, AnonymousUser):
            return {
                'user_id': None,
                'user_email': None,
                'user_display_name': None
            }
        
        try:
            # Extract from user object
            user_id = getattr(user, 'id', None)
            user_email = getattr(user, 'email', None) or getattr(user, 'username', None)
            
            # Try to get display name
            user_display_name = getattr(user, 'get_full_name', lambda: '')()
            if not user_display_name:
                user_display_name = user_email or f"User-{user_id}" if user_id else 'Anonymous'
            
            return {
                'user_id': str(user_id) if user_id else None,
                'user_email': user_email,
                'user_display_name': user_display_name[:200]  # Match model max_length
            }
        except Exception:
            return {
                'user_id': None,
                'user_email': None,
                'user_display_name': None
            }
    
    @classmethod
    def get_tenant_info(cls, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tenant information matching AuditLog model fields"""
        if not tenant_id:
            return {'tenant_id': None, 'tenant_name': None}
        
        try:
            tenant = Tenant.objects.filter(id=tenant_id).first()
            if tenant:
                return {
                    'tenant_id': str(tenant.id),
                    'tenant_name': tenant.name[:200]  # Match model max_length
                }
        except Exception:
            pass
        
        return {
            'tenant_id': str(tenant_id) if tenant_id else None,
            'tenant_name': None
        }
    
    @classmethod
    def create_audit_entry(
        cls,
        action: str,
        resource_type: str,
        user=None,
        request: Optional[HttpRequest] = None,
        instance=None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        changes: Optional[Dict] = None,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        severity: str = 'INFO',
        status: str = 'SUCCESS',
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        extra_data: Optional[Dict] = None,
        **kwargs
    ) -> Optional[AuditLog]:
        """
        Create an audit log entry - UPDATED to match AuditLog model fields exactly
        """
        try:
            # Generate unique request ID if not provided
            request_id = getattr(request, 'request_id', None) or str(uuid.uuid4())[:32]
            
            # Get session ID
            session_id = None
            if request and hasattr(request, 'session'):
                session_id = request.session.session_key
            
            # Get user information (matching model field names)
            user_info = cls.get_user_info(user)
            
            # Get tenant information (matching model field names)
            tenant_info = cls.get_tenant_info(tenant_id)
            
            # Prepare request information
            request_path = None
            request_method = None
            user_ip = None
            user_agent = None
            
            if request:
                request_path = request.path[:500]  # Match model max_length
                request_method = request.method[:10]  # Match model max_length
                user_ip = cls.get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Match model max_length
            
            # Get resource information from instance
            if instance and not resource_id:
                resource_id = str(getattr(instance, 'id', ''))[:100]  # Match model max_length
            
            if instance and not resource_name:
                resource_name = str(instance)[:500]  # Match model max_length
            
            # Calculate changes if not provided
            if changes is None and previous_state and new_state:
                changes = cls._calculate_changes(previous_state, new_state)
            
            # Prepare audit data - EXACTLY matching AuditLog model fields
            audit_data = {
                # User information - EXACT model field names
                'user_id': user_info['user_id'],
                'user_email': user_info['user_email'],
                'user_display_name': user_info['user_display_name'],
                
                # Action information - EXACT model field names
                'action': action,
                'severity': severity,
                'status': status,
                
                # Resource information - EXACT model field names
                'resource_type': resource_type,
                'resource_id': resource_id,
                'resource_name': resource_name,
                
                # State changes - EXACT model field names
                'changes': changes,
                'previous_state': previous_state,
                'new_state': new_state,
                
                # Request information - EXACT model field names
                'request_id': request_id,
                'session_id': session_id,
                'user_ip': user_ip,
                'user_agent': user_agent,
                'request_method': request_method,
                'request_path': request_path,
                
                # Error information - EXACT model field names
                'error_message': error_message,
                
                # Tenant information - EXACT model field names
                'tenant_id': tenant_info['tenant_id'],
                'tenant_name': tenant_info['tenant_name'],
                
                # Performance - EXACT model field names
                'duration_ms': duration_ms,
                
                # Extra data - EXACT model field names
                'extra_data': extra_data or {},
            }
            
            # Add stack trace if there's an error
            if error_message:
                audit_data['stack_trace'] = traceback.format_exc()[:10000]  # Limit length
            
            # Remove None values (except for fields that can legitimately be None)
            audit_data = {k: v for k, v in audit_data.items() if v is not None}
            
            # Create the audit entry
            with transaction.atomic():
                audit_entry = AuditLog.objects.create(**audit_data)
                
                # Link to content object if available
                if instance and hasattr(instance, '_meta'):
                    try:
                        content_type = ContentType.objects.get_for_model(instance.__class__)
                        audit_entry.content_type = content_type
                        audit_entry.object_uuid = getattr(instance, 'id', None)
                        audit_entry.save(update_fields=['content_type', 'object_uuid'])
                    except Exception:
                        # Silently fail - optional feature
                        pass
            
            # Log success in development
            if settings.DEBUG:
                print(f"[AUDIT SUCCESS] Created audit entry: {audit_entry.id}")
            
            return audit_entry
            
        except Exception as e:
            # Comprehensive error handling
            error_details = {
                'error': str(e),
                'action': action,
                'resource_type': resource_type,
                'user_email': getattr(user, 'email', None) if user else None,
            }
            
            # Log to appropriate logger
            import logging
            logger = logging.getLogger('audit_service')
            logger.error(
                f"Failed to create audit entry: {error_details}",
                exc_info=True,
                extra=error_details
            )
            
            # Development logging
            if settings.DEBUG:
                print(f"[AUDIT ERROR] Failed to create audit entry: {error_details}")
                traceback.print_exc()
            
            return None
    
    @classmethod
    def _calculate_changes(cls, old_state: Dict, new_state: Dict) -> Optional[Dict]:
        """Calculate changes between two states"""
        try:
            changes = {}
            all_keys = set(old_state.keys()) | set(new_state.keys())
            
            for key in all_keys:
                old_val = old_state.get(key)
                new_val = new_state.get(key)
                
                if old_val != new_val:
                    # Sanitize sensitive data
                    if any(sensitive in key.lower() for sensitive in 
                          ['password', 'token', 'secret', 'key', 'auth']):
                        changes[key] = {'old': '***', 'new': '***'}
                    else:
                        changes[key] = {'old': old_val, 'new': new_val}
            
            return changes if changes else None
        except Exception:
            return None
    
    # Convenience methods for common operations
    @classmethod
    def log_creation(cls, user, instance, request=None, **kwargs):
        """Log creation of an instance"""
        new_state = cls._serialize_instance(instance)
        
        return cls.create_audit_entry(
            action=AuditLog.AuditAction.CREATE,
            resource_type=instance.__class__.__name__,
            user=user,
            request=request,
            instance=instance,
            resource_id=instance.id,
            resource_name=str(instance),
            new_state=new_state,
            **kwargs
        )
    
    @classmethod
    def log_update(cls, user, instance, old_instance=None, request=None, **kwargs):
        """Log update of an instance"""
        previous_state = cls._serialize_instance(old_instance) if old_instance else None
        new_state = cls._serialize_instance(instance)
        
        return cls.create_audit_entry(
            action=AuditLog.AuditAction.UPDATE,
            resource_type=instance.__class__.__name__,
            user=user,
            request=request,
            instance=instance,
            resource_id=instance.id,
            resource_name=str(instance),
            previous_state=previous_state,
            new_state=new_state,
            **kwargs
        )
    
    @classmethod
    def log_deletion(cls, user, instance, request=None, hard_delete=False, **kwargs):
        """Log deletion of an instance"""
        action = AuditLog.AuditAction.DELETE if hard_delete else AuditLog.AuditAction.SOFT_DELETE
        
        previous_state = cls._serialize_instance(instance)
        
        return cls.create_audit_entry(
            action=action,
            resource_type=instance.__class__.__name__,
            user=user,
            request=request,
            instance=instance,
            resource_id=instance.id,
            resource_name=str(instance),
            previous_state=previous_state,
            **kwargs
        )
    
    @classmethod
    def log_api_call(cls, user, request, response, duration_ms=None, **kwargs):
        """Log API call"""
        status = 'SUCCESS' if response.status_code < 400 else 'FAILED'
        severity = 'INFO' if response.status_code < 400 else 'WARNING'
        
        return cls.create_audit_entry(
            action=AuditLog.AuditAction.API_CALL,
            resource_type='API',
            user=user,
            request=request,
            severity=severity,
            status=status,
            duration_ms=duration_ms,
            extra_data={
                'response_status': response.status_code,
                'response_content_type': response.get('Content-Type', ''),
                'request_body_size': len(request.body) if hasattr(request, 'body') else 0,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            },
            **kwargs
        )
    
    @classmethod
    def _serialize_instance(cls, instance):
        """Safely serialize instance to dict"""
        if not instance:
            return None
        
        try:
            from django.db import models
            
            data = {}
            for field in instance._meta.fields:
                field_name = field.name
                try:
                    value = getattr(instance, field_name)
                    
                    # Handle special types
                    if hasattr(value, 'id'):
                        data[field_name] = str(value.id)
                    elif isinstance(value, (timezone.datetime,)):
                        data[field_name] = value.isoformat()
                    elif isinstance(value, models.Model):
                        data[field_name] = str(value)
                    else:
                        # Sanitize sensitive fields
                        if any(sensitive in field_name.lower() for sensitive in 
                              ['password', 'token', 'secret', 'key', 'auth']):
                            data[field_name] = '***'
                        else:
                            data[field_name] = value
                except:
                    continue
            return data
        except Exception:
            return {'__str__': str(instance)[:500]}