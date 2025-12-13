import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Tenant

def list_tenants():
    print("Listing Tenants:")
    for tenant in Tenant.objects.all():
        print(f"Name: {tenant.name}, Schema: {tenant.schema_name}")

if __name__ == "__main__":
    list_tenants()
