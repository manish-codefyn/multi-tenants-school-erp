#!/usr/bin/env python
# Append AuditLog model to core/models.py

audit_model_code = """

# Audit Log Model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    event_time = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs', db_index=True)
    user_email = models.EmailField(null=True, blank=True, db_index=True)
    user_role = models.CharField(max_length=100, null=True, blank=True)
    user_department = models.CharField(max_length=200, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    request_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    request_path = models.CharField(max_length=500, null=True, blank=True)
    request_query = models.JSONField(null=True, blank=True)
    action = models.CharField(max_length=50, db_index=True)
    severity = models.CharField(max_length=20, default='INFO', db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    resource_name = models.CharField(max_length=500, null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    previous_state = models.JSONField(null=True, blank=True)
    new_state = models.JSONField(null=True, blank=True)
    diff_summary = models.TextField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    duration_ms = models.FloatField(null=True, blank=True)
    memory_usage_mb = models.FloatField(null=True, blank=True)
    query_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50, default='SUCCESS')
    error_code = models.CharField(max_length=50, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)
    data_hash = models.CharField(max_length=64, editable=False, default='')
    is_tampered = models.BooleanField(default=False, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    tenant_name = models.CharField(max_length=200, null=True, blank=True)
    source = models.CharField(max_length=100, default='WEB', db_index=True)
    channel = models.CharField(max_length=50, null=True, blank=True)
    retention_days = models.IntegerField(default=365)
    is_archived = models.BooleanField(default=False, db_index=True)
    archive_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_audit_log'
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.timestamp} - {self.user_email or 'System'} - {self.action} - {self.resource_type}"
"""

# Append to file
with open(r'h:\works\python\Multi-Tenant\EduERP_by_AI\apps\core\models.py', 'a', encoding='utf-8') as f:
    f.write(audit_model_code)

print("AuditLog model appended successfully!")
