from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('dashboard/', views.SecurityDashboardView.as_view(), name='dashboard'),
    
    # Security Policies
    path('policies/', views.SecurityPolicyListView.as_view(), name='policy_list'),
    path('policies/create/', views.SecurityPolicyCreateView.as_view(), name='policy_create'),
    path('policies/<int:pk>/update/', views.SecurityPolicyUpdateView.as_view(), name='policy_update'),
    path('policies/<int:pk>/delete/', views.SecurityPolicyDeleteView.as_view(), name='policy_delete'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    
    # Security Incidents
    path('incidents/', views.SecurityIncidentListView.as_view(), name='incident_list'),
    path('incidents/<int:pk>/', views.SecurityIncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/create/', views.SecurityIncidentCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/update/', views.SecurityIncidentUpdateView.as_view(), name='incident_update'),
]
