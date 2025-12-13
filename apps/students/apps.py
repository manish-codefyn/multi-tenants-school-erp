
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.students'
    verbose_name = _('Students Management')
    
    def ready(self):
        import apps.students.signals