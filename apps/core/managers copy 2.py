from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import FieldError


class SoftDeleteManager(models.Manager):
    """
    Custom manager for soft delete functionality
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

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
        return self.update(
            is_active=False,
            deleted_at=timezone.now(),
            deleted_by=user,
            deletion_reason=reason
        )


class TenantManager(models.Manager):
    """
    Manager for tenant-aware models with automatic tenant filtering
    """
    def get_queryset(self):
        from apps.core.utils.tenant import get_current_tenant
        
        queryset = super().get_queryset()
        current_tenant = get_current_tenant()
        
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
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import FieldError


class SoftDeleteManager(models.Manager):
    """
    Custom manager for soft delete functionality
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

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
        return self.update(
            is_active=False,
            deleted_at=timezone.now(),
            deleted_by=user,
            deletion_reason=reason
        )


class TenantManager(models.Manager):
    """
    Manager for tenant-aware models with automatic tenant filtering
    """
    def get_queryset(self):
        from apps.core.utils.tenant import get_current_tenant
        
        queryset = super().get_queryset()
        current_tenant = get_current_tenant()
        
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


class AuditManager(models.Manager):
    """
    Manager for audit models with efficient querying
    """
    def recent_actions(self, days=30):
        """
        Get recent actions within specified days
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.get_queryset().filter(timestamp__gte=cutoff_date)

    def by_user(self, user):
        """
        Get actions by specific user
        """
        return self.get_queryset().filter(user=user)

    def critical_events(self):
        """
        Get only critical security events
        """
        return self.get_queryset().filter(severity__in=['HIGH', 'CRITICAL'])


class TenantSoftDeleteManager(SoftDeleteManager, TenantManager):
    """
    Manager that combines soft delete and tenant filtering.
    """
    def get_queryset(self):
        # We need to call both parent get_queryset methods logic.
        # SoftDeleteManager.get_queryset() filters is_active=True
        # TenantManager.get_queryset() filters tenant=current_tenant
        
        # Start with SoftDeleteManager's queryset (is_active=True)
        queryset = super(SoftDeleteManager, self).get_queryset()
        
        # Apply TenantManager's logic manually or via super if MRO allows, 
        # but since both inherit from models.Manager, we need to be careful.
        # Let's explicitly apply tenant filtering here to be safe and clear.
        
        from apps.core.utils.tenant import get_current_tenant
        current_tenant = get_current_tenant()
        
        if current_tenant:
            queryset = queryset.filter(tenant=current_tenant)
            
        return queryset