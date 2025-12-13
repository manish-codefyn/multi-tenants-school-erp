# tenants/templatetags/tenant_tags.py
from django import template
from django.template.loader import render_to_string
from django_tenants.utils import get_tenant

register = template.Library()

def get_dynamic_tenant():
    """
    Get tenant from thread-local storage
    """
    from apps.core.middleware import get_dynamic_tenant as get_thread_tenant
    return get_thread_tenant()

@register.simple_tag(takes_context=True)
def render_tenant_component(context, component_name, **kwargs):
    """
    Render tenant-specific components with fallback
    """
    tenant = context.get('tenant')
    
    if not tenant:
        return ""
    
    # Template hierarchy: tenant-specific → type-specific → default
    template_names = [
        f"tenants/{tenant.schema_name}/components/{component_name}.html",
        f"tenants/{tenant.code}/components/{component_name}.html",
        f"tenants/{tenant.type}/components/{component_name}.html",
        f"components/{component_name}.html",
    ]
    
    try:
        return render_to_string(template_names, {**context, **kwargs})
    except:
        return ""

@register.simple_tag(takes_context=True)
def tenant_feature_enabled(context, feature_name):
    """
    Check if a specific feature is enabled for current tenant
    """
    tenant = context.get('tenant')
    if not tenant:
        return False
    
    # Map feature names to tenant fields
    feature_map = {
        'blog': 'enable_blog',
        'news': 'enable_news',
        'events': 'enable_events',
        'online_classes': 'enable_online_classes',
        'library': 'enable_library_management',
        'sms': 'enable_sms_notifications',
        'email': 'enable_email_notifications',
        'fee_management': 'enable_fee_management',
        'online_payments': 'enable_online_payments',
        'dark_mode': 'enable_dark_mode',
    }
    
    field_name = feature_map.get(feature_name)
    return getattr(tenant, field_name, False) if field_name else False

@register.simple_tag(takes_context=True)
def tenant_module_enabled(context, module_code):
    """
    Check if a specific module is enabled for current tenant
    Uses your enabled_modules M2M field
    """
    tenant = context.get('tenant')
    if not tenant:
        return False
    
    enabled_modules = context.get('enabled_modules', [])
    return any(module['code'] == module_code for module in enabled_modules)

@register.filter
def get_tenant_setting(tenant, key):
    """
    Access tenant settings using your get_setting method
    """
    return tenant.get_setting(key) if tenant else None

# @register.simple_tag(takes_context=True)
# def tenant_style(context):
#     """
#     Generate dynamic CSS variables based on tenant theme
#     """
#     tenant = context.get('tenant')
#     if not tenant or not tenant.theme_color:
#         return ""
    
#     theme_color = tenant.theme_color
    
#     return f"""
#     <style>
#         :root {{
#             --tenant-primary: {theme_color};
#             --tenant-primary-dark: color-mix(in srgb, {theme_color} 80%, black);
#             --tenant-primary-light: color-mix(in srgb, {theme_color} 20%, white);
#             --tenant-primary-rgb: {hex_to_rgb(theme_color)};
#         }}
        
#         .btn-primary {{
#             background-color: {theme_color} !important;
#             border-color: {theme_color} !important;
#         }}
        
#         .btn-primary:hover {{
#             background-color: color-mix(in srgb, {theme_color} 80%, black) !important;
#             border-color: color-mix(in srgb, {theme_color} 80%, black) !important;
#         }}
        
#         .text-primary {{
#             color: {theme_color} !important;
#         }}
        
#         .bg-primary {{
#             background-color: {theme_color} !important;
#         }}
        
#         .navbar-brand, .nav-link.active {{
#             color: {theme_color} !important;
#         }}
#     </style>
#     """

@register.filter
def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB format
    """
    if not hex_color:
        return "59, 130, 246"
        
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except ValueError:
            return "59, 130, 246"
    return "59, 130, 246"  # Default blue