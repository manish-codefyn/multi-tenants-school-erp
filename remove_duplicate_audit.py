#!/usr/bin/env python
# Script to remove duplicate AuditLog class from utils/audit.py

with open(r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\core\utils\audit.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 45-191 (Python is 0-indexed, so 44-190)
# Line 45 is index 44, line 191 is index 190
new_lines = lines[:44] + ["\\n# AuditLog model moved to apps.core.models\\nfrom apps.core.models import AuditLog\\n\n"] + lines[191:]

with open(r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\core\utils\audit.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully removed duplicate AuditLog class and added import!")
