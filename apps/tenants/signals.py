from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Tenant, Domain

@receiver(post_save, sender=Tenant)
def create_tenant_configuration(sender, instance, created, **kwargs):
    """Create default configuration for new tenants"""
    if created:
        from .models import TenantConfiguration
        TenantConfiguration.objects.get_or_create(tenant=instance)

@receiver(pre_save, sender=Domain)
def validate_primary_domain(sender, instance, **kwargs):
    """Ensure domain validation before saving"""
    if instance.is_primary and not instance.is_verified:
        raise ValidationError("Primary domain must be verified")