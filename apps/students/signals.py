# apps/students/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Student, StudentIdentification, StudentMedicalInfo


@receiver(post_save, sender=Student)
def create_student_related_models(sender, instance, created, **kwargs):
    """Create related models when student is created"""
    if created:
        # Create identification record
        StudentIdentification.objects.create(student=instance, tenant=instance.tenant)
        
        # Create medical info record
        StudentMedicalInfo.objects.create(student=instance, tenant=instance.tenant)


@receiver(pre_save, sender=Student)
def update_status_changed_date(sender, instance, **kwargs):
    """Update status changed date when status changes"""
    if instance.pk:
        try:
            original = Student.objects.get(pk=instance.pk)
            if original.status != instance.status:
                instance.status_changed_date = timezone.now()
        except Student.DoesNotExist:
            pass