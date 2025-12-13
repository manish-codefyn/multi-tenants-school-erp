from django.conf import settings
from apps.core.utils.tenant import get_current_tenant

def tenant_context(request):
    """
    Add tenant information to the template context
    """
    tenant = get_current_tenant()
    
    context = {
        'tenant': tenant,
        'site_name': tenant.name if tenant else 'EduERP',
    }
    
    # Add tenant configuration if available
    if tenant and hasattr(tenant, 'configuration'):
        context['tenant_config'] = tenant.configuration
        
    return context


def user_permissions(request):
    """
    Add user permissions to template context
    """
    if not request.user.is_authenticated:
        return {}
    
    from apps.core.permissions.utils import get_user_permissions_summary
    
    return {
        'user_permissions': request.user.get_all_permissions(),
        'user_role': request.user.role,
        'can_access': {
            'academics': request.user.has_perm('academics.view_course'),
            'finance': request.user.has_perm('finance.view_finance'),
            'library': request.user.has_perm('library.view_book'),
            'reports': request.user.has_perm('reports.view_report'),
            'settings': request.user.has_perm('settings.change_settings'),
        }
    }