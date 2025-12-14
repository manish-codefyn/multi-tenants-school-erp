from django.core.exceptions import PermissionDenied
from functools import wraps
from django.http import HttpResponseForbidden
import json


def require_https(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.is_secure():
            return HttpResponseForbidden("HTTPS is required")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required(perm, raise_exception=True):
    """
    Decorator for function-based views
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser or request.user.has_perm(perm):
                    return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            
            return HttpResponseForbidden("You don't have permission to access this page")
        return _wrapped_view
    return decorator


def role_required(roles, raise_exception=True):
    """
    Decorator to require specific role(s)
    """
    if isinstance(roles, str):
        roles = [roles]
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser or request.user.role in roles:
                    return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            
            return HttpResponseForbidden("You don't have the required role to access this page")
        return _wrapped_view
    return decorator


def min_role_level(level, raise_exception=True):
    """
    Decorator to require minimum role level
    """
    from apps.users.models import ROLE_HIERARCHY
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
                
                user_level = ROLE_HIERARCHY.get(request.user.role, 0)
                if user_level >= level:
                    return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied
            
            return HttpResponseForbidden("You don't have sufficient role level to access this page")
        return _wrapped_view
    return decorator


def api_permission_required(perm):
    """
    API-specific permission decorator that returns JSON response
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser or request.user.has_perm(perm):
                    return view_func(request, *args, **kwargs)
            
            return JsonResponse(
                {'error': 'Permission denied', 'code': 'permission_denied'},
                status=403
            )
        return _wrapped_view
    return decorator


def require_tenant_access():
    """
    Decorator to ensure user can only access their tenant's data
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user is trying to access another tenant's data
            tenant_id = kwargs.get('tenant_id') or request.GET.get('tenant')
            if tenant_id and str(tenant_id) != str(request.user.tenant_id):
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def rate_limit_by_role(requests_per_minute=60):
    """
    Rate limiting decorator based on user role
    """
    from django.core.cache import cache
    from django.http import HttpResponseTooManyRequests
    import time
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Different rate limits based on role
            role_limits = {
                'student': 30,
                'teacher': 100,
                'staff': 150,
                'admin': 300,
                'super_admin': 1000,
            }
            
            limit = role_limits.get(request.user.role, requests_per_minute)
            ip = request.META.get('REMOTE_ADDR')
            user_id = request.user.id
            
            # Create cache key
            cache_key = f"rate_limit:{user_id}:{int(time.time() // 60)}"
            
            # Get current count
            current = cache.get(cache_key, 0)
            
            if current >= limit:
                return HttpResponseTooManyRequests(
                    "Rate limit exceeded. Please try again later."
                )
            
            # Increment counter
            cache.set(cache_key, current + 1, 60)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator