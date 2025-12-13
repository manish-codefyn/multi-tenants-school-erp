from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdmissionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admission'
    verbose_name = _('Admission Management')

    def ready(self):
        import apps.admission.signals