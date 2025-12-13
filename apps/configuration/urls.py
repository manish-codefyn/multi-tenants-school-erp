from django.urls import path
from . import views

app_name = 'configuration'

urlpatterns = [
    path('dashboard/', views.ConfigurationDashboardView.as_view(), name='dashboard'),
    
    # System Settings
    path('settings/', views.SystemSettingListView.as_view(), name='setting_list'),
    path('settings/create/', views.SystemSettingCreateView.as_view(), name='setting_create'),
    path('settings/<int:pk>/update/', views.SystemSettingUpdateView.as_view(), name='setting_update'),
    path('settings/<int:pk>/delete/', views.SystemSettingDeleteView.as_view(), name='setting_delete'),
    
    # Configuration Modules
    path('financial/', views.FinancialConfigurationView.as_view(), name='financial_config'),
    path('security/', views.SecurityConfigurationView.as_view(), name='security_config'),
    path('notification/', views.NotificationConfigurationView.as_view(), name='notification_config'),
    path('appearance/', views.AppearanceConfigurationView.as_view(), name='appearance_config'),
]
