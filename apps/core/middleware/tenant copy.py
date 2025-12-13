from django.utils.deprecation import MiddlewareMixin
from apps.core.utils.tenant import set_current_tenant, clear_tenant
from apps.tenants.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to set tenant context for each request
    """
    def process_request(self, request):
        # Clear any previous tenant context
        clear_tenant()
        
        tenant = self.get_tenant_from_request(request)
        if tenant:
            set_current_tenant(tenant)
            request.tenant = tenant

    def process_response(self, request, response):
        # Clear tenant context after response
        clear_tenant()
        return response

    def process_exception(self, request, exception):
        # Clear tenant context on exception
        clear_tenant()

    def get_tenant_from_request(self, request):
        """
        Extract tenant from request (subdomain, header, or JWT token)
        """
        # Method 1: Subdomain-based tenant identification
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]
        
        if subdomain and subdomain not in ['www', 'api', 'admin']:
            try:
                # Use domains__domain to query the related Domain model
                return Tenant.objects.get(
                    domains__domain=host,
                    is_active=True
                )
            except Tenant.DoesNotExist:
                pass
        
        # Method 2: Header-based tenant identification
        tenant_header = request.headers.get('X-Tenant-ID')
        if tenant_header:
            try:
                return Tenant.objects.get(
                    id=tenant_header,
                    is_active=True
                )
            except (Tenant.DoesNotExist, ValueError):
                pass
        
        # Method 3: JWT token tenant claim
        if hasattr(request, 'user') and request.user.is_authenticated:
            tenant_id = getattr(request.user, 'tenant_id', None)
            if tenant_id:
                try:
                    return Tenant.objects.get(
                        id=tenant_id,
                        is_active=True
                    )
                except Tenant.DoesNotExist:
                    pass
        
        return None