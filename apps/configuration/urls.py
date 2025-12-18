from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'configuration'

urlpatterns = [
    # Dashboard
    path('', login_required(views.ConfigurationDashboardView.as_view()), name='dashboard'),
    
    # System Settings
    path('settings/', include([
        path('', login_required(views.SystemSettingListView.as_view()), name='setting_list'),
        path('create/', login_required(views.SystemSettingCreateView.as_view()), name='setting_create'),
        path('<int:pk>/edit/', login_required(views.SystemSettingUpdateView.as_view()), name='setting_update'),
        path('<int:pk>/delete/', login_required(views.SystemSettingDeleteView.as_view()), name='setting_delete'),
    ])),
    
    # Academic Configuration
    path('academic/', login_required(views.AcademicConfigurationView.as_view()), name='academic_config'),

    # Financial Configuration
    path('financial/', login_required(views.FinancialConfigurationView.as_view()), name='financial_config'),

    # Security Configuration
    path('security/', login_required(views.SecurityConfigurationView.as_view()), name='security_config'),

    # Notification Configuration
    path('notification/', login_required(views.NotificationConfigurationView.as_view()), name='notification_config'),

    # Appearance Configuration
    path('appearance/', login_required(views.AppearanceConfigurationView.as_view()), name='appearance_config'),

    # Integration Configuration
    path('integration/', include([
        path('', login_required(views.IntegrationListView.as_view()), name='integration_list'),
        path('create/', login_required(views.IntegrationCreateView.as_view()), name='integration_create'),
        path('<int:pk>/edit/', login_required(views.IntegrationUpdateView.as_view()), name='integration_update'),
        path('<int:pk>/delete/', login_required(views.IntegrationDeleteView.as_view()), name='integration_delete'),
    ])),

    # Backup Configuration
    path('backup/', login_required(views.BackupConfigurationView.as_view()), name='backup_config'),
]
