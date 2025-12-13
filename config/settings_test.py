from .settings import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}

# Remove django_tenants from INSTALLED_APPS to avoid router check
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_tenants']

# Remove tenant middleware as well to avoid runtime errors
MIDDLEWARE = [m for m in MIDDLEWARE if 'django_tenants' not in m]

# Disable routers
DATABASE_ROUTERS = []

# Speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable celery for tests
CELERY_TASK_ALWAYS_EAGER = True
