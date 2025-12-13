from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('institutions/', views.TenantListView.as_view(), name='tenant_list'),
    path('institutions/<slug:schema_name>/', views.TenantDetailView.as_view(), name='tenant_detail'),
]
