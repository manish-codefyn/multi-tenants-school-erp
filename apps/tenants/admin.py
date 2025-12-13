from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain

@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'status', 'plan', 'is_active', 'created_at')
    list_filter = ('status', 'plan', 'is_active')
    search_fields = ('name', 'schema_name', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Organization Info', {
            'fields': ('name', 'display_name', 'slug', 'contact_email', 'contact_phone')
        }),
        ('Technical Info', {
            'fields': ('schema_name', 'auto_create_schema')
        }),
        ('Subscription & Status', {
            'fields': ('status', 'plan', 'is_active', 'trial_ends_at', 'subscription_ends_at')
        }),
        ('Limits', {
            'fields': ('max_users', 'max_storage_mb')
        }),
        ('Security', {
            'fields': ('force_password_reset', 'mfa_required', 'password_policy')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('schema_name',)
        return self.readonly_fields

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary', 'is_verified', 'ssl_enabled')
    list_filter = ('is_primary', 'is_verified', 'ssl_enabled')
    search_fields = ('domain', 'tenant__name')
