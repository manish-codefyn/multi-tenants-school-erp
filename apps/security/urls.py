from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('', views.SecurityDashboardView.as_view(), name='dashboard'),
    
    # Password Policies
    path('password-policies/', views.PasswordPolicyListView.as_view(), name='password_policy_list'),
    path('password-policies/create/', views.PasswordPolicyCreateView.as_view(), name='password_policy_create'),
    path('password-policies/<int:pk>/update/', views.PasswordPolicyUpdateView.as_view(), name='password_policy_update'),
    path('password-policies/<int:pk>/delete/', views.PasswordPolicyDeleteView.as_view(), name='password_policy_delete'),
    
    # Session Policies
    path('session-policies/', views.SessionPolicyListView.as_view(), name='session_policy_list'),
    path('session-policies/create/', views.SessionPolicyCreateView.as_view(), name='session_policy_create'),
    path('session-policies/<int:pk>/update/', views.SessionPolicyUpdateView.as_view(), name='session_policy_update'),
    path('session-policies/<int:pk>/delete/', views.SessionPolicyDeleteView.as_view(), name='session_policy_delete'),
    
    # Access Control Policies
    path('access-policies/', views.AccessControlPolicyListView.as_view(), name='access_control_list'),
    path('access-policies/create/', views.AccessControlPolicyCreateView.as_view(), name='access_control_create'),
    path('access-policies/<int:pk>/update/', views.AccessControlPolicyUpdateView.as_view(), name='access_control_update'),
    path('access-policies/<int:pk>/delete/', views.AccessControlPolicyDeleteView.as_view(), name='access_control_delete'),
    
    # Incidents
    path('incidents/', views.SecurityIncidentListView.as_view(), name='incident_list'),
    path('incidents/create/', views.SecurityIncidentCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/', views.SecurityIncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/update/', views.SecurityIncidentUpdateView.as_view(), name='incident_update'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
]
