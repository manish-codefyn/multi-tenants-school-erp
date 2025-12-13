from django.contrib import admin
from .models import (
    SystemSetting, FinancialConfiguration, SecurityConfiguration,
    NotificationConfiguration
)

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'category', 'setting_type', 'is_public', 'is_encrypted')
    list_filter = ('category', 'setting_type', 'is_public', 'is_encrypted')
    search_fields = ('key', 'name', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'name', 'description', 'category', 'group')
        }),
        ('Value Configuration', {
            'fields': ('setting_type', 'value_string', 'value_text', 'value_integer', 
                      'value_decimal', 'value_boolean', 'value_json', 
                      'value_datetime', 'value_date', 'value_time')
        }),
        ('Configuration', {
            'fields': ('is_encrypted', 'is_public', 'is_required', 'is_readonly')
        }),
        ('Validation', {
            'fields': ('validation_regex', 'validation_message', 'min_value', 'max_value', 'choices')
        }),
        ('Metadata', {
            'fields': ('order', 'depends_on', 'version')
        }),
    )

@admin.register(FinancialConfiguration)
class FinancialConfigurationAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'base_currency', 'tax_enabled', 'financial_year_start', 'financial_year_end')
    list_filter = ('tax_enabled', 'base_currency')

@admin.register(SecurityConfiguration)
class SecurityConfigurationAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'password_min_length', 'session_timeout_minutes', 'require_2fa', 'data_encryption_enabled')
    list_filter = ('require_2fa', 'data_encryption_enabled')

@admin.register(NotificationConfiguration)
class NotificationConfigurationAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'email_enabled', 'sms_enabled', 'push_enabled', 'whatsapp_enabled')
    list_filter = ('email_enabled', 'sms_enabled', 'push_enabled', 'whatsapp_enabled')
