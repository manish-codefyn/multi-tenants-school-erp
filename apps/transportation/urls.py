from django.urls import path
from . import views

app_name = 'transportation'

urlpatterns = [
    path('dashboard/', views.TransportationDashboardView.as_view(), name='dashboard'),
    
    # Vehicles
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/create/', views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<int:pk>/update/', views.VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle_delete'),
    
    # Routes
    path('routes/', views.RouteListView.as_view(), name='route_list'),
    path('routes/create/', views.RouteCreateView.as_view(), name='route_create'),
    path('routes/<int:pk>/update/', views.RouteUpdateView.as_view(), name='route_update'),
    path('routes/<int:pk>/delete/', views.RouteDeleteView.as_view(), name='route_delete'),
    
    # Allocations
    path('allocations/', views.TransportAllocationListView.as_view(), name='allocation_list'),
    path('allocations/create/', views.TransportAllocationCreateView.as_view(), name='allocation_create'),
    path('allocations/<int:pk>/update/', views.TransportAllocationUpdateView.as_view(), name='allocation_update'),
    path('allocations/<int:pk>/delete/', views.TransportAllocationDeleteView.as_view(), name='allocation_delete'),
]
