import re
import os

def get_views_from_urls(urls_path):
    with open(urls_path, 'r') as f:
        content = f.read()
    
    # improved regex to handle views.ViewName.as_view()
    views = re.findall(r'views\.([a-zA-Z0-9_]+)\.as_view', content)
    return set(views)

def get_classes_from_views(views_path):
    with open(views_path, 'r') as f:
        content = f.read()
    
    classes = re.findall(r'class\s+([a-zA-Z0-9_]+)', content)
    return set(classes)

urls_path = r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\hr\urls.py'
views_path = r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\hr\views.py'

required_views = get_views_from_urls(urls_path)
existing_views = get_classes_from_views(views_path)

missing_views = required_views - existing_views

print("Missing Views:")
for view in sorted(missing_views):
    print(view)
