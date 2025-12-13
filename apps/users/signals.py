# apps/users/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import User


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle user post-save actions"""
    if created:
        # Send welcome email to new users
        if instance.email and not instance.is_superuser:
            try:
                subject = 'Welcome to Our System'
                html_message = render_to_string('emails/welcome.html', {
                    'user': instance,
                    'tenant': instance.tenant,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception:
                # Log error but don't crash
                pass


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """Handle user pre-save actions"""
    # Clean email
    if instance.email:
        instance.email = instance.email.lower()
    
    # Generate verification token for new non-superusers
    if not instance.pk and not instance.is_superuser:
        instance.generate_verification_token()