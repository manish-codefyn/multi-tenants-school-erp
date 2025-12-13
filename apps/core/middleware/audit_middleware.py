import time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from apps.core.services.audit_service import AuditService
from apps.core.models import AuditLog


class SafeAuditMiddleware(MiddlewareMixin):
    """
    Production-ready audit middleware with comprehensive safety features
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.skip_paths = [
            '/health/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
        ]
    
    def process_request(self, request):
        """Add request ID to request object"""
        import uuid
        if not hasattr(request, 'request_id'):
            request.request_id = str(uuid.uuid4())[:32]
        
        # Start timer for performance measurement
        request._audit_start_time = time.time()
        
        return None
    
    def process_response(self, request, response):
        """Audit API calls after processing"""
        try:
            # Calculate request duration
            duration_ms = None
            if hasattr(request, '_audit_start_time'):
                duration_ms = (time.time() - request._audit_start_time) * 1000
            
            # Skip certain paths
            if any(request.path.startswith(path) for path in self.skip_paths):
                return response
            
            # Only log significant actions
            should_log = (
                request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and
                not request.path.startswith('/admin/') and
                response.status_code < 500  # Don't log server errors here
            )
            
            if should_log:
                # Determine severity based on status code
                severity = AuditLog.AuditSeverity.INFO
                status = 'SUCCESS'
                
                if 400 <= response.status_code < 500:
                    severity = AuditLog.AuditSeverity.WARNING
                    status = 'FAILED'
                
                # Safely create audit entry
                AuditService.create_audit_entry(
                    action=AuditLog.AuditAction.API_CALL,
                    resource_type='API',
                    user=request.user if request.user.is_authenticated else None,
                    request=request,
                    severity=severity,
                    status=status,
                    duration_ms=duration_ms,
                    details={
                        'response_status': response.status_code,
                        'content_type': response.get('Content-Type', ''),
                        'view_name': getattr(response, 'view_name', None),
                    },
                    source='API_MIDDLEWARE'
                )
            
        except Exception as e:
            # Never let audit middleware break the request
            if settings.DEBUG:
                import logging
                logging.getLogger('audit_middleware').error(
                    f"Audit middleware error: {str(e)}",
                    exc_info=True
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions separately"""
        try:
            AuditService.create_audit_entry(
                action=AuditLog.AuditAction.API_CALL,
                resource_type='API',
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                request=request,
                severity=AuditLog.AuditSeverity.ERROR,
                status='FAILED',
                error_message=str(exception),
                details={
                    'exception_type': exception.__class__.__name__,
                    'view_name': getattr(request.resolver_match, 'view_name', None) if hasattr(request, 'resolver_match') else None,
                },
                source='EXCEPTION_HANDLER'
            )
        except Exception:
            # Silently fail - exception logging is optional
            pass
        
        return None