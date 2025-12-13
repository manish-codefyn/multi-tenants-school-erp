from django.contrib import admin
from .models import RolePermission, APIToken, SecurityEvent, LoginAttempt

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'tenant_specific')
    list_filter = ('role', 'tenant_specific')
    search_fields = ('role', 'permission__codename')

@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'expires_at', 'last_used')
    search_fields = ('name', 'user__email')
    readonly_fields = ('token',)

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'severity', 'ip_address', 'created_at')
    list_filter = ('event_type', 'severity')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('created_at',)

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'success', 'ip_address', 'created_at')
    list_filter = ('success',)
    search_fields = ('email', 'ip_address')
    readonly_fields = ('created_at',)
