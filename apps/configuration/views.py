from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import (
    SystemSetting, FinancialConfiguration, SecurityConfiguration,
    NotificationConfiguration, AppearanceConfiguration
)

class ConfigurationDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'configuration/dashboard.html'
    permission_required = 'configuration.view_systemsetting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_settings'] = SystemSetting.objects.filter(tenant=tenant).count()
        context['financial_config'] = FinancialConfiguration.objects.filter(tenant=tenant).first()
        context['security_config'] = SecurityConfiguration.objects.filter(tenant=tenant).first()
        context['notification_config'] = NotificationConfiguration.objects.filter(tenant=tenant).first()
        context['appearance_config'] = AppearanceConfiguration.objects.filter(tenant=tenant).first()
        
        return context

# ==================== SYSTEM SETTINGS ====================

class SystemSettingListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SystemSetting
    template_name = 'configuration/system_setting_list.html'
    context_object_name = 'settings'
    permission_required = 'configuration.view_systemsetting'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

class SystemSettingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SystemSetting
    fields = ['key', 'name', 'description', 'category', 'group', 'setting_type', 
              'value_string', 'value_text', 'value_integer', 'value_decimal', 
              'value_boolean', 'value_json', 'is_public', 'is_required', 'is_readonly']
    template_name = 'configuration/system_setting_form.html'
    success_url = reverse_lazy('configuration:setting_list')
    permission_required = 'configuration.add_systemsetting'

    def form_valid(self, form):
        messages.success(self.request, "System Setting created successfully.")
        return super().form_valid(form)

class SystemSettingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SystemSetting
    fields = ['name', 'description', 'category', 'group', 'setting_type', 
              'value_string', 'value_text', 'value_integer', 'value_decimal', 
              'value_boolean', 'value_json', 'is_public', 'is_required', 'is_readonly']
    template_name = 'configuration/system_setting_form.html'
    success_url = reverse_lazy('configuration:setting_list')
    permission_required = 'configuration.change_systemsetting'

    def form_valid(self, form):
        messages.success(self.request, "System Setting updated successfully.")
        return super().form_valid(form)

class SystemSettingDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SystemSetting
    template_name = 'configuration/confirm_delete.html'
    success_url = reverse_lazy('configuration:setting_list')
    permission_required = 'configuration.delete_systemsetting'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "System Setting deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== FINANCIAL CONFIGURATION ====================

class FinancialConfigurationView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FinancialConfiguration
    fields = ['base_currency', 'currency_symbol', 'decimal_places', 'tax_enabled', 
              'tax_rate', 'tax_number', 'invoice_prefix', 'invoice_start_number',
              'online_payment_enabled', 'auto_late_fee', 'late_fee_calculation',
              'financial_year_start', 'financial_year_end']
    template_name = 'configuration/financial_config_form.html'
    success_url = reverse_lazy('configuration:dashboard')
    permission_required = 'configuration.change_financialconfiguration'

    def get_object(self, queryset=None):
        tenant = get_current_tenant()
        obj, created = FinancialConfiguration.objects.get_or_create(tenant=tenant)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Financial Configuration updated successfully.")
        return super().form_valid(form)

# ==================== SECURITY CONFIGURATION ====================

class SecurityConfigurationView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SecurityConfiguration
    fields = ['password_min_length', 'password_require_uppercase', 'password_require_lowercase',
              'password_require_numbers', 'password_require_symbols', 'password_expiry_days',
              'session_timeout_minutes', 'max_login_attempts', 'lockout_duration_minutes',
              'require_2fa', 'enable_ip_restriction']
    template_name = 'configuration/security_config_form.html'
    success_url = reverse_lazy('configuration:dashboard')
    permission_required = 'configuration.change_securityconfiguration'

    def get_object(self, queryset=None):
        tenant = get_current_tenant()
        obj, created = SecurityConfiguration.objects.get_or_create(tenant=tenant)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Security Configuration updated successfully.")
        return super().form_valid(form)

# ==================== NOTIFICATION CONFIGURATION ====================

class NotificationConfigurationView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = NotificationConfiguration
    fields = ['email_enabled', 'email_host', 'email_port', 'email_username', 
              'email_use_tls', 'email_from_address', 'email_from_name',
              'sms_enabled', 'sms_provider', 'push_enabled', 'whatsapp_enabled']
    template_name = 'configuration/notification_config_form.html'
    success_url = reverse_lazy('configuration:dashboard')
    permission_required = 'configuration.change_notificationconfiguration'

    def get_object(self, queryset=None):
        tenant = get_current_tenant()
        obj, created = NotificationConfiguration.objects.get_or_create(tenant=tenant)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Notification Configuration updated successfully.")
        return super().form_valid(form)

# ==================== APPEARANCE CONFIGURATION ====================

class AppearanceConfigurationView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AppearanceConfiguration
    fields = ['institution_name', 'institution_logo', 'institution_favicon',
              'primary_color', 'secondary_color', 'accent_color', 'theme_mode',
              'layout_type', 'sidebar_collapsed']
    template_name = 'configuration/appearance_config_form.html'
    success_url = reverse_lazy('configuration:dashboard')
    permission_required = 'configuration.change_appearanceconfiguration'

    def get_object(self, queryset=None):
        tenant = get_current_tenant()
        obj, created = AppearanceConfiguration.objects.get_or_create(tenant=tenant)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Appearance Configuration updated successfully.")
        return super().form_valid(form)
