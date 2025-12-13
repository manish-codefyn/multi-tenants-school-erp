from django_tenants.cache import TenantCache
from django.core.cache import cache as default_cache


def tenant_cache_key(key, key_prefix, version):
    """
    Generate cache key with tenant context
    """
    from django_tenants.utils import get_tenant
    
    try:
        tenant = get_tenant()
        if tenant:
            return f"{tenant.schema_name}:{key_prefix}:{key}:{version}"
    except Exception:
        pass
    
    return f"{key_prefix}:{key}:{version}"


class CustomTenantCache(TenantCache):
    """
    Custom tenant-aware cache implementation
    """
    
    def make_key(self, key, version=None):
        key = super().make_key(key, version)
        return tenant_cache_key(key, self._key_prefix, version or self._version)