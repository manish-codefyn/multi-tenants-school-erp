
from django.core.cache import cache
from django.conf import settings
from django_tenants.utils import get_public_schema_name
from apps.core.middleware import get_dynamic_tenant
from apps.core.utils.tenant import get_current_tenant


def tenant_context(request):
    """
    Enhanced tenant context processor for your Tenant model
    """
    # Get tenant from request object (set by middleware)
    tenant = getattr(request, 'tenant', None) or get_current_tenant()
    # If no tenant or public schema, return minimal context
    if not tenant or tenant.schema_name == get_public_schema_name():
        return {
            'site_name': getattr(settings, 'PROJECT_NAME', 'EduERP'),
            'is_public_tenant': True,
        }
    
    # Cache key for tenant data
    cache_key = f"tenant_context_{tenant.schema_name}_{tenant.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Build comprehensive tenant context based on your model
    tenant_data = {
        # Basic tenant info
        'tenant': tenant,
        'tenant_name': tenant.name,
        'display_name': tenant.display_name,
        'tenant_code': tenant.slug,  # Using slug as code
        'tenant_slug': tenant.slug,
        
        # Status & Plan
        'tenant_status': tenant.status,
        'subscription_plan': tenant.plan,
        'is_trial': tenant.is_trial,
        'is_trial_active': tenant.is_trial,
        'is_subscription_active': tenant.is_subscription_active,
        'tenant_is_active': tenant.is_active,
        
        # Limits
        'max_users': tenant.max_users,
        'max_storage_mb': tenant.max_storage_mb,
        
        # Contact Information
        'tenant_email': tenant.contact_email,
        'tenant_phone': tenant.contact_phone,
        
        # Security
        'force_password_reset': tenant.force_password_reset,
        'mfa_required': tenant.mfa_required,
        
        # Dates
        'trial_ends_at': tenant.trial_ends_at,
        'subscription_ends_at': tenant.subscription_ends_at,
        
        # Site info
        'site_name': tenant.display_name or tenant.name,
        'site_title': tenant.display_name or tenant.name,
        
        # Branding (from configuration if available)
        'tenant_logo': None,
        'theme_color': '#3B82F6',  # Default
        'primary_color': '#3B82F6',
        'secondary_color': '#1E40AF',
        
        # User count
        'current_users': tenant.get_user_count() if hasattr(tenant, 'get_user_count') else 0,
        
        # Public flag
        'is_public_tenant': False,
    }
    
    # Add configuration data if available
    if hasattr(tenant, 'configuration') and tenant.configuration:
        config = tenant.configuration
        tenant_data.update({
            # Branding from configuration
            'tenant_logo': config.logo,
            'primary_color': config.primary_color,
            'secondary_color': config.secondary_color,
            'theme_color': config.primary_color,
            
            # Academic settings
            'academic_year': config.academic_year,
            
            # Localization
            'timezone': config.timezone,
            'language': config.language,
            'currency': config.currency,
            'date_format': config.date_format,
            
            # Security settings
            'session_timeout': config.session_timeout,
            'max_login_attempts': config.max_login_attempts,
            'password_expiry_days': config.password_expiry_days,
            
            # Feature flags
            'enabled_features': {
                'library': config.enable_library,
                'finance': config.enable_finance,
                'inventory': config.enable_inventory,
            },
            
            # Available modules
            'available_modules': config.get_available_modules() if hasattr(config, 'get_available_modules') else [],
            
            # Password policy
            'password_policy': config.get_password_policy() if hasattr(config, 'get_password_policy') else {},
        })
    
    # Add social media if you have it in your model
    # Uncomment and modify if you have these fields
    # tenant_data['social_media'] = {
    #     'facebook': getattr(tenant, 'facebook_url', None),
    #     'twitter': getattr(tenant, 'twitter_url', None),
    #     'linkedin': getattr(tenant, 'linkedin_url', None),
    #     'instagram': getattr(tenant, 'instagram_url', None),
    #     'youtube': getattr(tenant, 'youtube_url', None),
    # }
    
    # Cache for 1 hour (3600 seconds)
    cache.set(cache_key, tenant_data, 3600)
    
    return tenant_data


def user_permissions(request):
    """
    Add user permissions to template context
    """
    context = {}
    
    if not request.user.is_authenticated:
        return context
    
    # Add user info
    context.update({
        'user': request.user,
        'user_role': getattr(request.user, 'role', None),
        'user_display_name': request.user.get_full_name() or request.user.username,
    })
    
    # Add permissions
    try:
        context['user_permissions'] = request.user.get_all_permissions()
        
        # Module access permissions
        context['can_access'] = {
            'academics': request.user.has_perm('academics.view_course'),
            'finance': request.user.has_perm('finance.view_finance'),
            'library': request.user.has_perm('library.view_book'),
            'reports': request.user.has_perm('reports.view_report'),
            'settings': request.user.has_perm('settings.change_settings'),
            'inventory': request.user.has_perm('inventory.view_item'),
        }
        
    except Exception as e:
        # Fallback if permissions aren't available
        context['user_permissions'] = set()
        context['can_access'] = {}
    
    # Add tenant-specific user data if tenant exists
    tenant = getattr(request, 'tenant', None)
    if tenant and tenant.schema_name != get_public_schema_name():
        
        # Check user count against limits
        if hasattr(tenant, 'get_user_count') and hasattr(tenant, 'max_users'):
            context['user_count'] = tenant.get_user_count()
            context['user_limit'] = tenant.max_users
            context['can_add_users'] = tenant.get_user_count() < tenant.max_users
        
        # Add notifications count if notifications app exists
        try:
            from apps.notifications.models import Notification
            unread_notifications = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
            context['unread_notifications'] = unread_notifications
        except (ImportError, Exception):
            context['unread_notifications'] = 0
        
        # Add cart items count if store module is enabled
        if tenant.configuration and hasattr(tenant.configuration, 'enable_store'):
            if tenant.configuration.enable_store:
                try:
                    from apps.store.models import Cart
                    cart_items_count = Cart.objects.filter(user=request.user).count()
                    context['cart_items_count'] = cart_items_count
                except (ImportError, Exception):
                    context['cart_items_count'] = 0
    
    return context


def system_settings(request):
    """
    Add system-wide settings to template context
    """
    context = {}
    
    # Debug mode
    context['DEBUG'] = settings.DEBUG
    
    # Project name
    context['PROJECT_NAME'] = getattr(settings, 'PROJECT_NAME', 'EduERP')
    context['PROJECT_VERSION'] = getattr(settings, 'PROJECT_VERSION', '1.0.0')
    
    # Features
    context['ENABLE_REGISTRATION'] = getattr(settings, 'ENABLE_REGISTRATION', True)
    context['ENABLE_SSO'] = getattr(settings, 'ENABLE_SSO', False)
    
    # API settings
    context['API_BASE_URL'] = getattr(settings, 'API_BASE_URL', '/api/')
    
    # Static and media URLs
    context['STATIC_URL'] = settings.STATIC_URL
    context['MEDIA_URL'] = settings.MEDIA_URL
    context['version'] = settings.APP_VERSION
    
    return context


# Optional: Combined context processor for all context
def combined_context(request):
    """
    Combine all context processors into one for efficiency
    """
    context = {}
    
    # Add tenant context
    tenant_ctx = tenant_context(request)
    context.update(tenant_ctx)
    
    # Add user permissions
    user_ctx = user_permissions(request)
    context.update(user_ctx)
    
    # Add system settings
    system_ctx = system_settings(request)
    context.update(system_ctx)
    
    return context