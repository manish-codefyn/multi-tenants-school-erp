import logging
from django_tenants.utils import get_tenant_model, get_tenant_domain_model


class TenantContextFilter(logging.Filter):
    """
    Logging filter to add tenant context to log records
    """
    def filter(self, record):
        from django_tenants.utils import get_tenant
        from django.db import connection
        
        try:
            # Get current tenant from connection
            if hasattr(connection, 'tenant') and connection.tenant:
                record.tenant = connection.tenant.schema_name
            else:
                record.tenant = 'public'
        except Exception:
            record.tenant = 'unknown'
        
        return True


class TenantAwareLogger:
    """
    Tenant-aware logger for multi-tenant applications
    """
    
    @staticmethod
    def get_logger(name):
        """
        Get a logger instance with tenant context
        """
        logger = logging.getLogger(name)
        
        # Add tenant context filter if not already present
        if not any(isinstance(f, TenantContextFilter) for f in logger.filters):
            logger.addFilter(TenantContextFilter())
        
        return logger
    
    @staticmethod
    def log_tenant_event(level, message, tenant=None, extra=None):
        """
        Log an event with tenant context
        """
        logger = TenantAwareLogger.get_logger('tenants')
        
        log_data = {
            'tenant': tenant.schema_name if tenant else 'unknown',
            'message': message,
            'extra': extra or {}
        }
        
        if level == 'debug':
            logger.debug(message, extra=log_data)
        elif level == 'info':
            logger.info(message, extra=log_data)
        elif level == 'warning':
            logger.warning(message, extra=log_data)
        elif level == 'error':
            logger.error(message, extra=log_data)
        elif level == 'critical':
            logger.critical(message, extra=log_data)


def get_tenant_log_handler(tenant_schema):
    """
    Get a log handler specific to a tenant
    """
    import os
    from django.conf import settings
    
    # Create tenant-specific log directory
    log_dir = os.path.join(settings.BASE_DIR, 'logs', 'tenants', tenant_schema)
    os.makedirs(log_dir, exist_ok=True)
    
    # Create file handler for tenant
    log_file = os.path.join(log_dir, f'{tenant_schema}.log')
    handler = logging.FileHandler(log_file)
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(tenant)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    
    return handler