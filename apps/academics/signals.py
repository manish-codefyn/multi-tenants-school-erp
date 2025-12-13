
# Signals for additional business logic
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

@receiver(pre_save, sender=Enrollment)
def validate_enrollment_capacity(sender, instance, **kwargs):
    """Ensure course capacity is not exceeded"""
    if instance.status == 'active' and instance.pk is None:
        active_enrollments = Enrollment.objects.filter(
            course=instance.course,
            status='active'
        ).count()
        if active_enrollments >= instance.course.max_students:
            raise ValidationError(
                _("Course has reached maximum capacity. Cannot enroll more students.")
            )


@receiver(post_save, sender=Enrollment)
def update_course_status(sender, instance, created, **kwargs):
    """Update course enrollment status if needed"""
    if instance.status == 'active':
        active_enrollments = Enrollment.objects.filter(
            course=instance.course,
            status='active'
        ).count()
        
        # Close enrollment if course is full
        if active_enrollments >= instance.course.max_students:
            instance.course.enrollment_open = False
            instance.course.save()