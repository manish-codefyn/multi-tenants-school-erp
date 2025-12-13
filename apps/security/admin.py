from django.contrib import admin
from .models import (
    SecurityPolicy, PasswordPolicy, SessionPolicy, AccessControlPolicy,
    AuditLog, SecurityIncident, IncidentTimeline
)

@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'policy_type', 'enforcement_level', 'is_active', 'effective_date')
    list_filter = ('policy_type', 'enforcement_level', 'is_active')
    search_fields = ('name', 'code')

@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_length', 'password_expiry_days', 'max_login_attempts', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(SessionPolicy)
class SessionPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'session_timeout_minutes', 'max_concurrent_sessions', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(AccessControlPolicy)
class AccessControlPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'require_secure_connection', 'is_active')
    list_filter = ('is_active', 'require_secure_connection')
    search_fields = ('name',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'event_category', 'user', 'severity', 'outcome', 'created_at')
    list_filter = ('event_category', 'severity', 'outcome', 'created_at')
    search_fields = ('event_type', 'user__email', 'ip_address')
    readonly_fields = ('event_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

class IncidentTimelineInline(admin.TabularInline):
    model = IncidentTimeline
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_id', 'title', 'incident_type', 'priority', 'status', 'detected_at')
    list_filter = ('incident_type', 'priority', 'status', 'detected_at')
    search_fields = ('incident_id', 'title', 'description')
    inlines = [IncidentTimelineInline]
    date_hierarchy = 'detected_at'

@admin.register(IncidentTimeline)
class IncidentTimelineAdmin(admin.ModelAdmin):
    list_display = ('incident', 'event_type', 'created_by', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('incident__title', 'description')
