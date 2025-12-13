# apps/core/utils/__init__.py
"""
Core utilities package
"""

# First import tenant utilities
from .tenant import (
    set_current_tenant,
    get_current_tenant,
    clear_tenant,
    set_current_user,
    get_current_user,
    clear_user,
    tenant_context,
    user_context,
    get_tenant_schema,
)

# Then import audit utilities
try:
    from .audit import (
        audit_log,
        AuditAction,
        AuditSeverity,
        log_creation,
        log_update,
        log_deletion,
        log_restoration,
        log_login,
        log_logout,
        log_tenant_switch,
        _get_client_ip,
        _serialize_instance,
    )
except ImportError:
    # Create stubs if import fails
    audit_log = None
    AuditAction = type('AuditAction', (), {})
    AuditSeverity = type('AuditSeverity', (), {})
    
    def stub_func(*args, **kwargs):
        return None
    
    log_creation = stub_func
    log_update = stub_func
    log_deletion = stub_func
    log_restoration = stub_func
    log_login = stub_func
    log_logout = stub_func
    log_tenant_switch = stub_func
    _get_client_ip = stub_func
    _serialize_instance = stub_func

__all__ = [
    # Tenant utilities
    'set_current_tenant',
    'get_current_tenant',
    'clear_tenant',
    'set_current_user',
    'get_current_user',
    'clear_user',
    'tenant_context',
    'user_context',
    'get_tenant_schema',
    
    # Audit utilities
    'audit_log',
    'AuditAction',
    'AuditSeverity',
    'log_creation',
    'log_update',
    'log_deletion',
    'log_restoration',
    'log_login',
    'log_logout',
    'log_tenant_switch',
    '_get_client_ip',
    '_serialize_instance',
]