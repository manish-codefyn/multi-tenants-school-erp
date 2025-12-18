from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.core.views import (
    BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseTemplateView
)
from apps.core.utils.tenant import get_current_tenant
from .models import (
    SystemSetting, AcademicConfiguration, FinancialConfiguration,
    SecurityConfiguration, NotificationConfiguration, AppearanceConfiguration,
    IntegrationConfiguration, BackupConfiguration
)
from .forms import (
    SystemSettingForm, AcademicConfigurationForm, FinancialConfigurationForm,
    SecurityConfigurationForm, NotificationConfigurationForm, AppearanceConfigurationForm,
    IntegrationConfigurationForm, BackupConfigurationForm
)

# ==================== DASHBOARD ====================

class ConfigurationDashboardView(BaseTemplateView):
    template_name = 'configuration/dashboard.html'
    permission_required = 'configuration.view_systemsetting'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Add summary data
        context['system_settings_count'] = SystemSetting.objects.filter(tenant=tenant).count()
        context['active_integrations'] = IntegrationConfiguration.objects.filter(tenant=tenant, is_enabled=True).count()
        
        # Check if configurations exist
        context['has_academic'] = AcademicConfiguration.objects.filter(tenant=tenant).exists()
        context['has_financial'] = FinancialConfiguration.objects.filter(tenant=tenant).exists()
        context['has_security'] = SecurityConfiguration.objects.filter(tenant=tenant).exists()
        context['has_notification'] = NotificationConfiguration.objects.filter(tenant=tenant).exists()
        context['has_appearance'] = AppearanceConfiguration.objects.filter(tenant=tenant).exists()
        context['has_backup'] = BackupConfiguration.objects.filter(tenant=tenant).exists()
        
        return context

# ==================== SYSTEM SETTINGS ====================

class SystemSettingListView(BaseListView):
    model = SystemSetting
    template_name = 'configuration/system_setting/list.html'
    context_object_name = 'settings'
    permission_required = 'configuration.view_systemsetting'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

class SystemSettingCreateView(BaseCreateView):
    model = SystemSetting
    form_class = SystemSettingForm
    template_name = 'configuration/system_setting/form.html'
    permission_required = 'configuration.add_systemsetting'
    success_url = reverse_lazy('configuration:setting_list')

class SystemSettingUpdateView(BaseUpdateView):
    model = SystemSetting
    form_class = SystemSettingForm
    template_name = 'configuration/system_setting/form.html'
    permission_required = 'configuration.change_systemsetting'
    success_url = reverse_lazy('configuration:setting_list')

class SystemSettingDeleteView(BaseDeleteView):
    model = SystemSetting
    template_name = 'configuration/system_setting/confirm_delete.html'
    permission_required = 'configuration.delete_systemsetting'
    success_url = reverse_lazy('configuration:setting_list')

# ==================== ACADEMIC CONFIGURATION ====================

class AcademicConfigurationView(BaseUpdateView):
    model = AcademicConfiguration
    form_class = AcademicConfigurationForm
    template_name = 'configuration/academic/form.html'
    permission_required = 'configuration.change_academicconfiguration'
    success_url = reverse_lazy('configuration:academic_config')
    
    def get_object(self, queryset=None):
        return AcademicConfiguration.get_for_tenant(get_current_tenant())

# ==================== FINANCIAL CONFIGURATION ====================

class FinancialConfigurationView(BaseUpdateView):
    model = FinancialConfiguration
    form_class = FinancialConfigurationForm
    template_name = 'configuration/financial/form.html'
    permission_required = 'configuration.change_financialconfiguration'
    success_url = reverse_lazy('configuration:financial_config')
    
    def get_object(self, queryset=None):
        return FinancialConfiguration.get_for_tenant(get_current_tenant())

# ==================== SECURITY CONFIGURATION ====================

class SecurityConfigurationView(BaseUpdateView):
    model = SecurityConfiguration
    form_class = SecurityConfigurationForm
    template_name = 'configuration/security/form.html'
    permission_required = 'configuration.change_securityconfiguration'
    success_url = reverse_lazy('configuration:security_config')
    
    def get_object(self, queryset=None):
        return SecurityConfiguration.get_for_tenant(get_current_tenant())

# ==================== NOTIFICATION CONFIGURATION ====================

class NotificationConfigurationView(BaseUpdateView):
    model = NotificationConfiguration
    form_class = NotificationConfigurationForm
    template_name = 'configuration/notification/form.html'
    permission_required = 'configuration.change_notificationconfiguration'
    success_url = reverse_lazy('configuration:notification_config')
    
    def get_object(self, queryset=None):
        return NotificationConfiguration.get_for_tenant(get_current_tenant())

# ==================== APPEARANCE CONFIGURATION ====================

class AppearanceConfigurationView(BaseUpdateView):
    model = AppearanceConfiguration
    form_class = AppearanceConfigurationForm
    template_name = 'configuration/appearance/form.html'
    permission_required = 'configuration.change_appearanceconfiguration'
    success_url = reverse_lazy('configuration:appearance_config')
    
    def get_object(self, queryset=None):
        return AppearanceConfiguration.get_for_tenant(get_current_tenant())

# ==================== INTEGRATION CONFIGURATION ====================

class IntegrationListView(BaseListView):
    model = IntegrationConfiguration
    template_name = 'configuration/integration/list.html'
    context_object_name = 'integrations'
    permission_required = 'configuration.view_integrationconfiguration'

class IntegrationCreateView(BaseCreateView):
    model = IntegrationConfiguration
    form_class = IntegrationConfigurationForm
    template_name = 'configuration/integration/form.html'
    permission_required = 'configuration.add_integrationconfiguration'
    success_url = reverse_lazy('configuration:integration_list')

class IntegrationUpdateView(BaseUpdateView):
    model = IntegrationConfiguration
    form_class = IntegrationConfigurationForm
    template_name = 'configuration/integration/form.html'
    permission_required = 'configuration.change_integrationconfiguration'
    success_url = reverse_lazy('configuration:integration_list')

class IntegrationDeleteView(BaseDeleteView):
    model = IntegrationConfiguration
    template_name = 'configuration/integration/confirm_delete.html'
    permission_required = 'configuration.delete_integrationconfiguration'
    success_url = reverse_lazy('configuration:integration_list')

# ==================== BACKUP CONFIGURATION ====================

class BackupConfigurationView(BaseUpdateView):
    model = BackupConfiguration
    form_class = BackupConfigurationForm
    template_name = 'configuration/backup/form.html'
    permission_required = 'configuration.change_backupconfiguration'
    success_url = reverse_lazy('configuration:backup_config')
    
    def get_object(self, queryset=None):
        return BackupConfiguration.get_for_tenant(get_current_tenant())
