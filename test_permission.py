import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_permission():
    with connection.cursor() as cursor:
        try:
            print("Attempting to create schema 'test_schema_permission'...")
            cursor.execute("CREATE SCHEMA test_schema_permission")
            print("Schema created successfully.")
            cursor.execute("DROP SCHEMA test_schema_permission")
            print("Schema dropped successfully.")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == '__main__':
    test_permission()
