from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.forms import TenantAwareModelForm
from .models import (
    SystemSetting, AcademicConfiguration, FinancialConfiguration,
    SecurityConfiguration, NotificationConfiguration, AppearanceConfiguration,
    IntegrationConfiguration, BackupConfiguration
)

class SystemSettingForm(TenantAwareModelForm):
    class Meta:
        model = SystemSetting
        fields = [
            'key', 'name', 'description', 'category', 'group',
            'setting_type', 'value_string', 'value_text', 'value_integer',
            'value_decimal', 'value_boolean', 'value_json', 'value_datetime',
            'value_date', 'value_time', 'chart_field', 'is_encrypted',
            'is_public', 'is_required', 'is_readonly', 'validation_regex',
            'validation_message', 'min_value', 'max_value', 'choices',
            'order', 'depends_on', 'version'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'value_text': forms.Textarea(attrs={'rows': 3}),
            'value_json': forms.Textarea(attrs={'rows': 5}),
            'validation_message': forms.Textarea(attrs={'rows': 2}),
            'choices': forms.Textarea(attrs={'rows': 3}),
        }

class AcademicConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = AcademicConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by']
        widgets = {
            'academic_year_start': forms.DateInput(attrs={'type': 'date'}),
            'academic_year_end': forms.DateInput(attrs={'type': 'date'}),
            'term_start_date': forms.DateInput(attrs={'type': 'date'}),
            'term_end_date': forms.DateInput(attrs={'type': 'date'}),
            'exam_types': forms.Textarea(attrs={'rows': 3}),
            'promotion_conditions': forms.Textarea(attrs={'rows': 3}),
        }

class FinancialConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = FinancialConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by']
        widgets = {
            'financial_year_start': forms.DateInput(attrs={'type': 'date'}),
            'financial_year_end': forms.DateInput(attrs={'type': 'date'}),
            'invoice_terms': forms.Textarea(attrs={'rows': 3}),
            'invoice_notes': forms.Textarea(attrs={'rows': 3}),
            'payment_methods': forms.Textarea(attrs={'rows': 2}),
        }

class SecurityConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = SecurityConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by']
        widgets = {
            'allowed_2fa_methods': forms.Textarea(attrs={'rows': 2}),
            'ip_whitelist': forms.Textarea(attrs={'rows': 3}),
            'ip_blacklist': forms.Textarea(attrs={'rows': 3}),
        }

class NotificationConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = NotificationConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by']
        widgets = {
            'email_password': forms.PasswordInput(render_value=True),
            'sms_api_key': forms.PasswordInput(render_value=True),
            'sms_api_secret': forms.PasswordInput(render_value=True),
            'whatsapp_access_token': forms.PasswordInput(render_value=True),
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time'}),
            'default_notification_channels': forms.Textarea(attrs={'rows': 2}),
            'default_email_template': forms.Textarea(attrs={'rows': 5}),
            'default_sms_template': forms.Textarea(attrs={'rows': 3}),
        }

class AppearanceConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = AppearanceConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'custom_css': forms.Textarea(attrs={'rows': 10, 'class': 'font-monospace'}),
            'custom_js': forms.Textarea(attrs={'rows': 10, 'class': 'font-monospace'}),
            'footer_text': forms.Textarea(attrs={'rows': 2}),
            'login_subtitle': forms.Textarea(attrs={'rows': 2}),
        }

class IntegrationConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = IntegrationConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by', 'last_sync', 'sync_status', 'error_message']
        widgets = {
            'webhook_secret': forms.PasswordInput(render_value=True),
            'config_data': forms.Textarea(attrs={'rows': 5}),
            'api_keys': forms.Textarea(attrs={'rows': 5}),
            'endpoints': forms.Textarea(attrs={'rows': 5}),
            'webhook_events': forms.Textarea(attrs={'rows': 3}),
        }

class BackupConfigurationForm(TenantAwareModelForm):
    class Meta:
        model = BackupConfiguration
        fields = '__all__'
        exclude = ['tenant', 'created_by', 'updated_by', 'last_backup', 'last_backup_status', 'last_backup_size', 'next_backup']
        widgets = {
            'backup_time': forms.TimeInput(attrs={'type': 'time'}),
            'excluded_tables': forms.Textarea(attrs={'rows': 3}),
            'encryption_key': forms.PasswordInput(render_value=True),
            'notification_emails': forms.Textarea(attrs={'rows': 2}),
        }
