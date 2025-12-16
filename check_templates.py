import re
import os

def check_missing_templates(views_path, templates_root):
    with open(views_path, 'r') as f:
        content = f.read()
    
    # regex to find class Name ... template_name = 'path'
    # This is a bit complex as they might be far apart with newlines.
    # But usually it's near the top.
    
    # Simpler approach: find all strings assigned to template_name
    template_refs = re.findall(r"template_name\s*=\s*['\"]([^'\"]+)['\"]", content)
    
    missing = []
    found = []
    
    for t_path in template_refs:
        # absolute path construction
        # templates_root should be .../templates
        # t_path is e.g. hr/dashboard.html
        full_path = os.path.join(templates_root, t_path)
        # normalize slashes
        full_path = full_path.replace('/', os.sep).replace('\\', os.sep)
        
        if not os.path.exists(full_path):
            missing.append(t_path)
        else:
            found.append(t_path)
            
    return sorted(list(set(missing))), sorted(list(set(found)))

views_path = r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\hr\views.py'
templates_root = r'h:\works\python\Multi-Tenant\EduERP_by_AI\templates'

missing, found = check_missing_templates(views_path, templates_root)

print(f"Found {len(found)} templates.")
print(f"Missing {len(missing)} templates.")
if missing:
    print("Missing Templates:")
    for m in missing:
        print(m)
