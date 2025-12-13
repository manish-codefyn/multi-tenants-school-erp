
from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path('dashboard/', views.TenantDashboardView.as_view(), name='dashboard'),
    
    # Tenants
    path('dsd/', views.TenantListView.as_view(), name='home'),
    path('tenant_list/', views.TenantListView.as_view(), name='tenant_list'),
    path('<uuid:pk>/', views.TenantDetailView.as_view(), name='tenant_detail'),
    path('create/', views.TenantCreateView.as_view(), name='tenant_create'),
    path('<uuid:pk>/update/', views.TenantUpdateView.as_view(), name='tenant_update'),
    path('<uuid:pk>/delete/', views.TenantDeleteView.as_view(), name='tenant_delete'),
    
    # Domains
    path('domains/', views.DomainListView.as_view(), name='domain_list'),
    path('domains/create/', views.DomainCreateView.as_view(), name='domain_create'),
    path('domains/<uuid:pk>/update/', views.DomainUpdateView.as_view(), name='domain_update'),
    path('domains/<uuid:pk>/delete/', views.DomainDeleteView.as_view(), name='domain_delete'),
]
