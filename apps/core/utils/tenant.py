# apps/core/utils/tenant.py
import threading
from contextlib import contextmanager
from django.db import connection
from django.contrib.auth import get_user_model

# Thread-local storage for tenant context
_thread_locals = threading.local()


def set_current_tenant(tenant):
    """
    Set the current tenant in thread-local storage
    """
    _thread_locals.tenant = tenant


def get_current_tenant():
    """
    Get the current tenant from thread-local storage
    """
    return getattr(_thread_locals, 'tenant', None)


def clear_tenant():
    """
    Clear tenant from thread-local storage
    """
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')


# Add user-related thread-local storage functions
def set_current_user(user):
    """
    Set the current user in thread-local storage
    """
    _thread_locals.user = user


def get_current_user():
    """
    Get the current user from thread-local storage
    """
    return getattr(_thread_locals, 'user', None)


def clear_user():
    """
    Clear user from thread-local storage
    """
    if hasattr(_thread_locals, 'user'):
        delattr(_thread_locals, 'user')


@contextmanager
def tenant_context(tenant):
    """
    Context manager for temporary tenant switching
    """
    old_tenant = get_current_tenant()
    set_current_tenant(tenant)
    try:
        yield
    finally:
        set_current_tenant(old_tenant)


@contextmanager
def user_context(user):
    """
    Context manager for temporary user switching
    """
    old_user = get_current_user()
    set_current_user(user)
    try:
        yield
    finally:
        set_current_user(old_user)


def get_tenant_schema(tenant):
    """
    Get schema name for tenant
    """
    if hasattr(tenant, 'schema_name'):
        return tenant.schema_name
    return 'public'