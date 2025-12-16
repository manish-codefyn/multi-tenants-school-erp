import os

dirs = [
    r'templates/hr/addresses',
    r'templates/hr/documents',
    r'templates/hr/history',
    r'templates/hr/leave',
    r'templates/hr/payroll',
    r'templates/hr/performance',
    r'templates/hr/recruitment',
    r'templates/hr/reports',
    r'templates/hr/staff',
    r'templates/hr/training'
]

root = r'h:\works\python\Multi-Tenant\EduERP_by_AI'

for d in dirs:
    path = os.path.join(root, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created {path}")
