# apps/core/setup_config.py
"""
Configuration for system setup
"""

DEFAULT_SUPERUSER = {
    'email': 'admin@erpsystem.com',
    'password': 'admin123',
    'first_name': 'System',
    'last_name': 'Administrator',
}

DEFAULT_TENANT = {
    'name': 'Main Campus',
    'schema_name': 'public',
    'domain_url': 'localhost',
    'description': 'Main campus tenant',
}

ROLE_PERMISSIONS = {
    'student': {
        'academics': ['view_course', 'view_grade', 'view_attendance'],
        'library': ['view_book', 'borrow_book'],
    },
    'teacher': {
        'academics': ['view_course', 'change_course', 'view_grade', 'change_grade'],
        'library': ['view_book', 'reserve_book'],
    },
    'admin': {
        '*': ['all_permissions'],
    },
}

SETUP_STEPS = [
    {
        'name': 'database',
        'description': 'Apply migrations and create superuser',
        'command': 'setup_database',
        'required': True,
    },
    {
        'name': 'permissions',
        'description': 'Setup role permissions and groups',
        'command': 'setup_permissions_only',
        'required': True,
    },
    {
        'name': 'tenants',
        'description': 'Create initial tenants',
        'command': 'setup_tenants',
        'required': False,
    },
    {
        'name': 'sample_data',
        'description': 'Load sample data',
        'command': 'load_sample_data',
        'required': False,
    },
]