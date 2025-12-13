from django import template
from apps.core.utils.tenant import get_current_tenant

register = template.Library()

@register.simple_tag
def tenant_feature_enabled(feature_name):
    """
    Check if a feature is enabled for the current tenant.
    Usage: {% tenant_feature_enabled 'blog' as blog_enabled %}
    """
    tenant = get_current_tenant()
    if not tenant:
        return False
        
    # Check if tenant has configuration and if the feature is in allowed_modules
    # This assumes 'allowed_modules' or similar logic exists.
    # Adjust based on actual model structure.
    if hasattr(tenant, 'configuration') and tenant.configuration:
        config = tenant.configuration
        # Map feature names to config fields
        feature_map = {
            'library': config.enable_library,
            'finance': config.enable_finance,
            'inventory': config.enable_inventory,
        }
        
        if feature_name in feature_map:
            return feature_map[feature_name]
            
    # Default to True for features not explicitly controlled by config yet (blog, news, events)
    # to ensure they appear in the UI as requested.
    return True
