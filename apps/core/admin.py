
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AuditLog

class ReadOnlyAdmin(admin.ModelAdmin):
    """Prevent accidental edits"""
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdmin):
    list_display = (
        'timestamp',
        'action',
        'severity',
        'status',
        'user_email',
        'resource_type',
        'resource_id',
        'tenant_name',
    )

    list_filter = (
        'action',
        'severity',
        'status',
        'tenant_name',
        'timestamp',
    )

    search_fields = (
        'user_email',
        'user_display_name',
        'resource_type',
        'resource_id',
        'tenant_name',
        'request_id',
        'session_id',
    )

    ordering = ('-timestamp',)

    readonly_fields = [field.name for field in AuditLog._meta.fields]

    fieldsets = (
        (_("Basic Info"), {
            "fields": (
                'timestamp',
                'action',
                'severity',
                'status',
            )
        }),
        (_("User"), {
            "fields": (
                'user_email',
                'user_display_name',
                'user_ip',
                'user_agent',
            )
        }),
        (_("Resource"), {
            "fields": (
                'resource_type',
                'resource_id',
                'resource_name',
            )
        }),
        (_("Tenant"), {
            "fields": (
                'tenant_id',
                'tenant_name',
            )
        }),
        (_("Request"), {
            "classes": ('collapse',),
            "fields": (
                'request_method',
                'request_path',
                'request_id',
                'session_id',
                'duration_ms',
            )
        }),
        (_("Error (if any)"), {
            "classes": ('collapse',),
            "fields": (
                'error_message',
                'stack_trace',
            )
        }),
        (_("Extra Data"), {
            "classes": ('collapse',),
            "fields": (
                'changes',
                'previous_state',
                'new_state',
                'extra_data',
            )
        }),
    )
