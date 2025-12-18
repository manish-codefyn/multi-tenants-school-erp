# apps/core/managers.py (updated)
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import FieldError


class AuditManager(models.Manager):
    """
    Custom manager for models with audit trail functionality
    (Also aliased as AuditTrailManager)
    """
    def create(self, **kwargs):
        """
        Override create to set created_by/created_at if available
        """
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_user
            user = get_current_user()
            if user and user.is_authenticated and 'created_by' not in kwargs:
                kwargs['created_by'] = user
        except ImportError:
            pass  # Silently fail if tenant utils not available
        
        if 'created_at' not in kwargs:
            kwargs['created_at'] = timezone.now()
            
        return super().create(**kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """
        Override bulk_create to set audit fields
        """
        # Import inside method to avoid circular imports
        from django.utils import timezone
        current_time = timezone.now()
        
        try:
            from apps.core.utils.tenant import get_current_user
            user = get_current_user()
        except ImportError:
            user = None
        
        for obj in objs:
            if hasattr(obj, 'created_at') and not obj.created_at:
                obj.created_at = current_time
            if hasattr(obj, 'created_by') and not obj.created_by and user and user.is_authenticated:
                obj.created_by = user
                
        return super().bulk_create(objs, **kwargs)
    
    def update(self, **kwargs):
        """
        Override update to set updated_by/updated_at
        """
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_user
            user = get_current_user()
            if user and user.is_authenticated:
                kwargs['updated_by'] = user
        except ImportError:
            pass  # Silently fail if tenant utils not available
        
        kwargs['updated_at'] = timezone.now()
        return super().update(**kwargs)


# Alias for backward compatibility
AuditTrailManager = AuditManager


class SoftDeleteManager(AuditManager):  # Inherit from AuditManager
    """
    Custom manager for soft delete functionality
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            self.model._meta.get_field('is_active')
            return queryset.filter(is_active=True)
        except Exception:
            return queryset

    def deleted(self):
        """
        Return only deleted records
        """
        return super().get_queryset().filter(is_active=False)

    def with_deleted(self):
        """
        Return all records including deleted ones
        """
        return super().get_queryset()

    def active(self):
        """
        Explicitly return only active records (default behavior)
        """
        return self.get_queryset()

    def delete(self, user=None, reason=None):
        """
        Bulk soft delete with audit trail
        """
        # Import inside method to avoid circular imports
        from django.utils import timezone
        
        if not user:
            try:
                from apps.core.utils.tenant import get_current_user
                user = get_current_user()
            except ImportError:
                user = None
            
        return self.update(
            is_active=False,
            deleted_at=timezone.now(),
            deleted_by=user,
            deletion_reason=reason
        )


class TenantManager(AuditManager):  # Inherit from AuditManager
    """
    Manager for tenant-aware models with automatic tenant filtering
    """
    def get_queryset(self):
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_tenant
            current_tenant = get_current_tenant()
        except ImportError:
            current_tenant = None
        
        queryset = super().get_queryset()
        
        if current_tenant:
            return queryset.filter(tenant=current_tenant)
        return queryset

    def for_tenant(self, tenant):
        """
        Explicitly filter for a specific tenant
        """
        return super().get_queryset().filter(tenant=tenant)

    def cross_tenant(self):
        """
        Bypass tenant filtering (use with caution, admin only)
        """
        return super().get_queryset()


class TenantSoftDeleteManager(TenantManager, SoftDeleteManager):
    """
    Manager that combines both tenant filtering and soft delete functionality
    """
    def get_queryset(self):
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_tenant
            current_tenant = get_current_tenant()
        except ImportError:
            current_tenant = None
        
        # Use parent class method
        queryset = super(TenantManager, self).get_queryset()
        
        if current_tenant:
            queryset = queryset.filter(tenant=current_tenant)
        
        try:
            self.model._meta.get_field('is_active')
            return queryset.filter(is_active=True)
        except Exception:
            return queryset

    def deleted(self):
        """
        Return only deleted records for current tenant
        """
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_tenant
            current_tenant = get_current_tenant()
        except ImportError:
            current_tenant = None
        
        queryset = super(TenantManager, self).get_queryset()
        
        if current_tenant:
            queryset = queryset.filter(tenant=current_tenant)
        
        return queryset.filter(is_active=False)

    def with_deleted(self):
        """
        Return all records including deleted ones for current tenant
        """
        # Import inside method to avoid circular imports
        try:
            from apps.core.utils.tenant import get_current_tenant
            current_tenant = get_current_tenant()
        except ImportError:
            current_tenant = None
        
        queryset = super(TenantManager, self).get_queryset()
        
        if current_tenant:
            return queryset.filter(tenant=current_tenant)
        return queryset


class GlobalManager(models.Manager):
    """
    Manager for models that are shared across all tenants (global models)
    """
    def get_queryset(self):
        return super().get_queryset()


class GlobalSoftDeleteManager(SoftDeleteManager):
    """
    Manager for global models with soft delete functionality
    """
    pass


__all__ = [
    'AuditManager',
    'AuditTrailManager',
    'SoftDeleteManager',
    'TenantManager',
    'TenantSoftDeleteManager',
    'GlobalManager',
    'GlobalSoftDeleteManager',
]