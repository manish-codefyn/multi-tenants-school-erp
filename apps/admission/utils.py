# apps/admission/utils.py or in your models.py

import uuid
import os
from django.utils import timezone
from django.utils.text import slugify
import hashlib

def application_document_upload_path(instance, filename):
    """
    Generate upload path for application documents with shorter, safe filenames.
    This prevents the SuspiciousFileOperation error on Windows.
    """
    # Get the application and tenant
    application = instance.application
    tenant = application.tenant if hasattr(application, 'tenant') else None
    
    # Create shorter identifiers
    app_short_id = str(application.id)[:8]  # First 8 chars of UUID
    doc_type_slug = slugify(instance.document_type.replace('_', ' '))[:20]
    timestamp = str(int(timezone.now().timestamp()))[-6:]  # Last 6 digits of timestamp
    
    # Create a short unique identifier
    unique_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:6]
    
    # Get file extension safely
    ext = os.path.splitext(filename)[1].lower()
    
    # Clean original filename (limit to 50 chars)
    original_name = os.path.splitext(filename)[0]
    cleaned_name = slugify(original_name)[:50]
    
    # Construct new filename (maximum 100 chars total)
    new_filename = f"{app_short_id}_{doc_type_slug}_{timestamp}_{unique_id}{ext}"
    
    # Construct path with forward slashes only (Windows compatibility)
    if tenant:
        # Include tenant ID in path
        tenant_short = str(tenant.id)[:8]
        return f"admission_documents/tenant_{tenant_short}/app_{app_short_id}/{new_filename}"
    else:
        return f"admission_documents/app_{app_short_id}/{new_filename}"


# Alternative: Even shorter version
def simple_document_upload_path(instance, filename):
    """
    Minimal upload path to avoid path length issues
    """
    # Generate a short UUID (6 chars)
    short_uuid = str(uuid.uuid4()).split('-')[0]  # First segment only
    
    # Get file extension
    ext = os.path.splitext(filename)[1].lower()
    
    # Use application ID (first 6 chars) and short UUID
    app_id = str(instance.application.id)[:6]
    
    # Return very short path
    return f"docs/{app_id}/{short_uuid}{ext}"