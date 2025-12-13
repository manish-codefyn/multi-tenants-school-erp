# apps/core/middleware/tenant.py
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django_tenants.utils import get_public_schema_name
import jwt

from apps.core.utils.tenant import (
    set_current_tenant, 
    clear_tenant, 
    get_current_tenant,
    set_current_user,
    clear_user,
    get_current_user
)
from apps.tenants.models import Tenant, Domain

User = get_user_model()


class TenantMiddleware(MiddlewareMixin):
    """
    Comprehensive middleware to set tenant context for each request
    """
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.public_schemas = getattr(settings, 'PUBLIC_SCHEMAS', ['public'])
        self.ignored_subdomains = getattr(settings, 'IGNORED_SUBDOMAINS', [
            'www', 'api', 'admin', 'app', 'portal', 'static', 'media'
        ])

    def process_request(self, request):
        """
        Set tenant context for the request
        """
        # Clear any previous tenant and user context
        clear_tenant()
        clear_user()
        
        # Try to get tenant from request
        tenant = self.get_tenant_from_request(request)
        
        if tenant:
            # Set tenant in thread-local storage
            set_current_tenant(tenant)
            
            # Attach tenant to request object
            request.tenant = tenant
            
            # Store in session for consistency
            if hasattr(request, 'session'):
                request.session['tenant_id'] = str(tenant.id)
        else:
            # If no tenant found, set to public schema
            request.tenant = None
            if hasattr(request, 'session'):
                request.session.pop('tenant_id', None)
        
        # Set current user in thread-local storage if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)

    def process_response(self, request, response):
        """
        Clean up tenant context after response
        """
        # Clear tenant and user context
        clear_tenant()
        clear_user()
        
        # Add tenant headers to response for API clients
        if hasattr(request, 'tenant') and request.tenant:
            response['X-Tenant-ID'] = str(request.tenant.id)
            response['X-Tenant-Name'] = request.tenant.name
        
        return response

    def process_exception(self, request, exception):
        """
        Clear tenant context on exception
        """
        clear_tenant()
        clear_user()

    def get_tenant_from_request(self, request):
        """
        Extract tenant from request using multiple strategies
        """
        # Strategy 1: Direct session/header override (for debugging/API)
        tenant_id = self._get_tenant_from_debug_header(request)
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass

        # Strategy 2: Subdomain-based tenant identification (primary method)
        tenant = self._get_tenant_from_subdomain(request)
        if tenant:
            return tenant

        # Strategy 3: Header-based tenant identification (for APIs)
        tenant = self._get_tenant_from_header(request)
        if tenant:
            return tenant

        # Strategy 4: JWT token tenant claim (for authenticated users)
        tenant = self._get_tenant_from_jwt(request)
        if tenant:
            return tenant

        # Strategy 5: Session-based tenant (for consistency across requests)
        tenant = self._get_tenant_from_session(request)
        if tenant:
            return tenant

        # Strategy 6: Path-based tenant identification (optional)
        tenant = self._get_tenant_from_path(request)
        if tenant:
            return tenant

        # No tenant found - will use public schema
        return None

    def _get_tenant_from_debug_header(self, request):
        """
        Get tenant from debug header (for development/testing)
        Only works when DEBUG=True
        """
        if settings.DEBUG:
            return request.headers.get('X-Debug-Tenant-ID')
        return None

    def _get_tenant_from_subdomain(self, request):
        """
        Extract tenant from subdomain
        """
        host = request.get_host().split(':')[0]
        
        # Handle localhost development
        if host == 'localhost' or host.startswith('127.0.0.1'):
            # Check if we have a custom domain in development
            dev_domain = request.headers.get('X-Forwarded-Host')
            if dev_domain:
                host = dev_domain
        
        # Extract subdomain
        parts = host.split('.')
        
        # Handle cases like "subdomain.example.com" or "tenant.localhost:8000"
        if len(parts) >= 2:
            subdomain = parts[0]
            
            # Skip ignored subdomains
            if subdomain in self.ignored_subdomains:
                return None
            
            # Check if this is a valid tenant domain
            try:
                # First, try to get by domain name
                domain = Domain.objects.select_related('tenant').get(
                    domain=host,
                    tenant__is_active=True
                )
                return domain.tenant
            except Domain.DoesNotExist:
                # Fallback to tenant slug/schema name
                try:
                    return Tenant.objects.get(
                        slug=subdomain,
                        is_active=True
                    )
                except (Tenant.DoesNotExist, Tenant.MultipleObjectsReturned):
                    pass
        
        return None

    def _get_tenant_from_header(self, request):
        """
        Get tenant from HTTP headers (for API requests)
        """
        tenant_header = request.headers.get('X-Tenant-ID')
        if not tenant_header:
            tenant_header = request.headers.get('Tenant-ID')
        
        if tenant_header:
            try:
                return Tenant.objects.get(
                    id=tenant_header,
                    is_active=True
                )
            except (Tenant.DoesNotExist, ValueError):
                # Try slug if ID doesn't work
                try:
                    return Tenant.objects.get(
                        slug=tenant_header,
                        is_active=True
                    )
                except (Tenant.DoesNotExist, Tenant.MultipleObjectsReturned):
                    pass
        
        return None

    def _get_tenant_from_jwt(self, request):
        """
        Extract tenant from JWT token for authenticated users
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Method 1: Direct user attribute
            tenant_id = getattr(request.user, 'tenant_id', None)
            if tenant_id:
                try:
                    return Tenant.objects.get(
                        id=tenant_id,
                        is_active=True
                    )
                except Tenant.DoesNotExist:
                    pass
            
            # Method 2: JWT token in Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    # Decode JWT token (without verification for speed)
                    # In production, you should verify the token
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    tenant_id = decoded.get('tenant_id')
                    if tenant_id:
                        return Tenant.objects.get(
                            id=tenant_id,
                            is_active=True
                        )
                except (jwt.DecodeError, jwt.InvalidTokenError, Tenant.DoesNotExist):
                    pass
        
        return None

    def _get_tenant_from_session(self, request):
        """
        Get tenant from user session
        """
        if hasattr(request, 'session'):
            tenant_id = request.session.get('tenant_id')
            if tenant_id:
                try:
                    return Tenant.objects.get(
                        id=tenant_id,
                        is_active=True
                    )
                except (Tenant.DoesNotExist, ValueError):
                    request.session.pop('tenant_id', None)
        
        return None

    def _get_tenant_from_path(self, request):
        """
        Extract tenant from URL path (e.g., /tenant-slug/dashboard/)
        """
        path = request.path_info
        
        # Skip admin paths
        if path.startswith('/admin/') or path.startswith('/api/'):
            return None
        
        # Check for tenant slug in path
        parts = path.strip('/').split('/')
        if parts:
            tenant_slug = parts[0]
            
            # Check if this looks like a tenant slug
            if tenant_slug and tenant_slug not in ['static', 'media', 'auth', 'login', 'logout']:
                try:
                    return Tenant.objects.get(
                        slug=tenant_slug,
                        is_active=True
                    )
                except (Tenant.DoesNotExist, Tenant.MultipleObjectsReturned):
                    pass
        
        return None


class TenantContextMiddleware(MiddlewareMixin):
    """
    Additional middleware to ensure tenant context is available
    even if the main tenant middleware fails
    """
    def process_request(self, request):
        """
        Ensure tenant is always available on request
        """
        if not hasattr(request, 'tenant'):
            # Try to get tenant from current thread context
            tenant = get_current_tenant()
            if tenant:
                request.tenant = tenant
            else:
                request.tenant = None
        
        # Also ensure user is set in thread-local
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
    
    def process_response(self, request, response):
        """
        Clean up after response
        """
        clear_user()
        return response


# Helper function for context processors
def get_dynamic_tenant():
    """
    Get current tenant from thread-local storage
    """
    return get_current_tenant()