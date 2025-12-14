from django.core.exceptions import PermissionDenied
from django.http import Http404,HttpResponseForbidden,  JsonResponse
from django.contrib.auth.mixins import AccessMixin
from django.utils.decorators import method_decorator
from django.views import View
from functools import wraps
from apps.tenants.models import Tenant
from django.utils.decorators import method_decorator
from functools import wraps
from django.core.cache import cache
import time
import json


class RateLimitedViewMixin:
    """Mixin to add rate limiting to views"""
    rate_limit = '10/minute'
    rate_limit_key = 'user'
    
    def get_rate_limit(self):
        """Override to provide dynamic rate limits"""
        return self.rate_limit
    
    def get_rate_limit_key(self):
        """Override to customize rate limit key"""
        return self.rate_limit_key
    
    def get_cache_key(self, request):
        """Generate cache key for rate limiting"""
        key_type = self.get_rate_limit_key()
        
        if key_type == 'user' and request.user.is_authenticated:
            return f"rate_limit:user:{request.user.id}:{int(time.time() // 60)}"
        elif key_type == 'ip':
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            return f"rate_limit:ip:{ip}:{int(time.time() // 60)}"
        else:
            # Default to IP if user not authenticated
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            return f"rate_limit:ip:{ip}:{int(time.time() // 60)}"
    
    def parse_rate_limit(self, rate_string):
        """Parse rate limit string like '10/minute' or '100/hour'"""
        try:
            num, period = rate_string.split('/')
            num = int(num)
            period = period.lower().strip()
            
            # Convert period to seconds
            if period == 'second':
                return num, 1
            elif period == 'minute':
                return num, 60
            elif period == 'hour':
                return num, 3600
            elif period == 'day':
                return num, 86400
            else:
                return num, 60  # Default to minute
        except (ValueError, AttributeError):
            return 10, 60  # Default fallback
    
    def dispatch(self, request, *args, **kwargs):
        """Apply rate limiting before dispatch"""
        rate_string = self.get_rate_limit()
        max_requests, time_window = self.parse_rate_limit(rate_string)
        
        cache_key = self.get_cache_key(request)
        
        # Get current count
        current = cache.get(cache_key, 0)
        
        if current >= max_requests:
            return self.rate_limit_exceeded(request)
        
        # Increment counter
        cache.set(cache_key, current + 1, time_window)
        
        return super().dispatch(request, *args, **kwargs)
    
    def rate_limit_exceeded(self, request):
        """Handle rate limit exceeded"""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'code': 'rate_limit_exceeded'
            }, status=429)
        return HttpResponseTooManyRequests("Rate limit exceeded. Please try again later.")

class PermissionRequiredMixin(AccessMixin):
    """
    Mixin to require specific permissions for view access
    """
    permission_required = None
    permission_required_any = None
    raise_exception = True
    
    def get_permission_required(self):
        """
        Override this method to customize permission checking
        """
        return self.permission_required
    
    def has_permission(self):
        """
        Check if user has required permission
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
        
        # Check single permission
        if self.permission_required:
            if isinstance(self.permission_required, str):
                return user.has_perm(self.permission_required)
            elif isinstance(self.permission_required, (list, tuple)):
                return all(user.has_perm(perm) for perm in self.permission_required)
        
        # Check any of multiple permissions
        if self.permission_required_any:
            return any(user.has_perm(perm) for perm in self.permission_required_any)
        
        return True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            if self.raise_exception:
                raise PermissionDenied
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(AccessMixin):
    """
    Mixin to require specific role(s) for view access
    """
    roles_required = None
    roles_required_any = None
    min_role_level = None
    
    def get_roles_required(self):
        return self.roles_required
    
    def has_role_permission(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
        
        # Check specific role(s)
        if self.roles_required:
            if isinstance(self.roles_required, str):
                return user.role == self.roles_required
            elif isinstance(self.roles_required, (list, tuple)):
                return user.role in self.roles_required
        
        # Check any of multiple roles
        if self.roles_required_any:
            return user.role in self.roles_required_any
        
        # Check minimum role level
        if self.min_role_level:
            from apps.users.models import ROLE_HIERARCHY
            user_level = ROLE_HIERARCHY.get(user.role, 0)
            return user_level >= self.min_role_level
        
        return True
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_role_permission():
            if self.raise_exception:
                raise PermissionDenied
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class TenantAccessMixin(AccessMixin):
    """
    Mixin to ensure user can only access their tenant's data
    """
    tenant_field = 'tenant'
    allow_superuser = True
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser and self.allow_superuser:
            return queryset
        
        # Filter by user's tenant
        return queryset.filter(**{self.tenant_field: user.tenant})
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user
        
        if user.is_superuser and self.allow_superuser:
            return obj
        
        # Check if object belongs to user's tenant
        if getattr(obj, self.tenant_field) != user.tenant:
            raise Http404("Object not found or you don't have permission to view it")
        
        return obj


class ObjectPermissionMixin(AccessMixin):
    """
    Mixin for object-level permissions
    """
    object_permission_required = None
    
    def has_object_permission(self, obj):
        user = self.request.user
        
        if user.is_superuser:
            return True
        
        if self.object_permission_required:
            return user.has_perm(self.object_permission_required, obj)
        
        # Default: check if user owns the object
        return getattr(obj, 'user', None) == user or getattr(obj, 'created_by', None) == user
    
    def dispatch(self, request, *args, **kwargs):
        # For detail views, check object permissions
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if not self.has_object_permission(obj):
                raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


class RoleBasedViewMixin(PermissionRequiredMixin, RoleRequiredMixin):
    """
    Combined mixin for both role and permission checking
    """
    def has_permission(self):
        # Check role first
        if not self.has_role_permission():
            return False
        
        # Then check specific permissions
        return super().has_permission()

class TenantRequiredMixin(AccessMixin):
    """
    Mixin to control tenant-based access for views.
    
    Features:
    - Only allow users to access their tenant's resources.
    - Superusers bypass checks.
    - Supports multi-tenant users (if you use a many-to-many relation).
    - Auto-detect tenant from object, queryset, or URL kwargs.
    """

    tenant_field = "tenant"            # Field on model representing tenant
    tenant_kwarg = "tenant_id"         # Optional URL kwarg for tenant ID
    allow_superuser = True
    raise_exception = True

    # -----------------------------------------------------------
    # 1. Get currently allowed tenants for logged-in user
    # -----------------------------------------------------------
    def get_user_tenants(self):
        user = self.request.user

        # Superuser: full access
        if user.is_superuser and self.allow_superuser:
            return Tenant.objects.all()

        # If user.tenant is a single tenant
        if hasattr(user, "tenant") and user.tenant:
            return Tenant.objects.filter(id=user.tenant.id)

        # If system uses many-to-many: user.tenants (preferred)
        if hasattr(user, "tenants"):
            return user.tenants.all()

        # No tenant found → block
        return Tenant.objects.none()

    # -----------------------------------------------------------
    # 2. Detect tenant from URL kwargs or object
    # -----------------------------------------------------------
    def get_requested_tenant(self, obj=None):
        # From URL kwargs
        if self.tenant_kwarg and self.tenant_kwarg in self.kwargs:
            from apps.tenants.models import Tenant
            try:
                return Tenant.objects.get(id=self.kwargs[self.tenant_kwarg])
            except Tenant.DoesNotExist:
                return None

        # From object (DetailView, UpdateView, DeleteView)
        if obj and hasattr(obj, self.tenant_field):
            return getattr(obj, self.tenant_field)

        return None

    # -----------------------------------------------------------
    # 3. Validate access
    # -----------------------------------------------------------
    def has_tenant_access(self, obj=None):
        user_tenants = self.get_user_tenants()
        requested_tenant = self.get_requested_tenant(obj)

        # If there is no tenant to validate → allow
        if not requested_tenant:
            return True

        return requested_tenant in user_tenants

    # -----------------------------------------------------------
    # 4. For queryset-based views (ListView)
    # -----------------------------------------------------------
    def get_queryset(self):
        qs = super().get_queryset()
        user_tenants = self.get_user_tenants()
        return qs.filter(**{f"{self.tenant_field}__in": user_tenants})

    # -----------------------------------------------------------
    # 5. For object-based views (DetailView/UpdateView/DeleteView)
    # -----------------------------------------------------------
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not self.has_tenant_access(obj):
            raise Http404("You do not have access to this tenant's data.")

        return obj

    # -----------------------------------------------------------
    # 6. Dispatch-level protection
    # -----------------------------------------------------------
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not self.has_tenant_access():
            if self.raise_exception:
                raise PermissionDenied("Tenant access denied.")
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
