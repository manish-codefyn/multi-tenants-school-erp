from django.urls import path
from . import views

app_name = 'transportation'

urlpatterns = [
    path('dashboard/', views.TransportationDashboardView.as_view(), name='dashboard'),
    
    # Vehicles
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/create/', views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<uuid:pk>/update/', views.VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<uuid:pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle_delete'),
    
    # Routes
    path('routes/', views.RouteListView.as_view(), name='route_list'),
    path('routes/create/', views.RouteCreateView.as_view(), name='route_create'),
    path('routes/<uuid:pk>/update/', views.RouteUpdateView.as_view(), name='route_update'),
    path('routes/<uuid:pk>/delete/', views.RouteDeleteView.as_view(), name='route_delete'),
    
    # Route Stops
    path('routes/stops/', views.RouteStopListView.as_view(), name='stop_list'),
    path('routes/stops/create/', views.RouteStopCreateView.as_view(), name='stop_create'),
    path('routes/stops/<uuid:pk>/update/', views.RouteStopUpdateView.as_view(), name='stop_update'),
    path('routes/stops/<uuid:pk>/delete/', views.RouteStopDeleteView.as_view(), name='stop_delete'),
    
    # Allocations
    path('allocations/', views.TransportAllocationListView.as_view(), name='allocation_list'),
    path('allocations/create/', views.TransportAllocationCreateView.as_view(), name='allocation_create'),
    path('allocations/<uuid:pk>/update/', views.TransportAllocationUpdateView.as_view(), name='allocation_update'),
    path('allocations/<uuid:pk>/delete/', views.TransportAllocationDeleteView.as_view(), name='allocation_delete'),
    
    # Attendance
    path('attendance/', views.TransportAttendanceListView.as_view(), name='attendance_list'),
    path('attendance/create/', views.TransportAttendanceCreateView.as_view(), name='attendance_create'),
    path('attendance/<uuid:pk>/update/', views.TransportAttendanceUpdateView.as_view(), name='attendance_update'),
    path('attendance/<uuid:pk>/delete/', views.TransportAttendanceDeleteView.as_view(), name='attendance_delete'),

    # Maintenance
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<uuid:pk>/update/', views.MaintenanceUpdateView.as_view(), name='maintenance_update'),
    path('maintenance/<uuid:pk>/delete/', views.MaintenanceDeleteView.as_view(), name='maintenance_delete'),

    # Fuel
    path('fuel/', views.FuelListView.as_view(), name='fuel_list'),
    path('fuel/create/', views.FuelCreateView.as_view(), name='fuel_create'),
    path('fuel/<uuid:pk>/update/', views.FuelUpdateView.as_view(), name='fuel_update'),
    path('fuel/<uuid:pk>/delete/', views.FuelDeleteView.as_view(), name='fuel_delete'),
]
