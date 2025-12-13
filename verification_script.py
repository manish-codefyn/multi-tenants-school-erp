
import os
import django
from django.urls import reverse
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verify_urls():
    print("Verifying Admin URLs...")
    
    urls_to_check = [
        'admin:apps_auth_securityevent_changelist',
        'admin:users_user_changelist',
        'admin:app_list',
    ]
    
    for url_name in urls_to_check:
        try:
            if url_name == 'admin:app_list':
                url = reverse(url_name, args=('configuration',))
            else:
                url = reverse(url_name)
            print(f"[OK] {url_name} -> {url}")
        except Exception as e:
            print(f"[FAIL] {url_name} -> {e}")

if __name__ == '__main__':
    verify_urls()
