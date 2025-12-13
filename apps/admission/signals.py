from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import OnlineApplication, AdmissionStatistics


@receiver(post_save, sender=OnlineApplication)
def update_admission_statistics(sender, instance, created, **kwargs):
    """
    Update admission statistics when application is created or updated
    """
    if instance.program and instance.admission_cycle:
        stats, created = AdmissionStatistics.objects.get_or_create(
            admission_cycle=instance.admission_cycle,
            program=instance.program,
            tenant=instance.tenant
        )
        stats.update_statistics()


@receiver(pre_save, sender=OnlineApplication)
def application_status_change_handler(sender, instance, **kwargs):
    """
    Handle application status changes and trigger appropriate actions
    """
    if instance.pk:
        try:
            original = OnlineApplication.objects.get(pk=instance.pk)
            if original.status != instance.status:
                # Status changed - trigger notifications, etc.
                pass
        except OnlineApplication.DoesNotExist:
            pass