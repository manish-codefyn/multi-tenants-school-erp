import os
import sys

# Add project root to path
sys.path.append('h:/works/python/Multi-Tenant/EduERP_by_AI')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    from apps.analytics.models import InstitutionalAnalytics
    from apps.analytics.forms import InstitutionalAnalyticsForm
    
    print("--- Model Fields ---")
    model_fields = [f.name for f in InstitutionalAnalytics._meta.get_fields()]
    print(model_fields)
    
    print("\n--- Form Meta Fields ---")
    print(InstitutionalAnalyticsForm.Meta.fields)
    
    if 'chart_type' in model_fields:
        print("\nERROR: chart_type FOUND in Model!")
    else:
        print("\nchart_type NOT found in Model.")
        
    if 'chart_type' in InstitutionalAnalyticsForm.Meta.fields:
        print("ERROR: chart_type FOUND in Form Meta.fields!")
    else:
        print("chart_type NOT found in Form Meta.fields.")

except Exception as e:
    print(f"\nCaught Exception: {type(e).__name__}: {e}")
    # Print traceback if it's a FieldError
    import traceback
    traceback.print_exc()
