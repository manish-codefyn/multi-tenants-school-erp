from django.urls import path, include
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'transportation'

urlpatterns = [
    # ==================== DASHBOARD & HOME ====================
    path('', login_required(views.TransportationDashboardView.as_view()), name='dashboard'),
    path('dashboard/', login_required(views.TransportationDashboardView.as_view()), name='dashboard_alt'),

    # ==================== VEHICLE MANAGEMENT ====================
    path('vehicles/', include([
        path('', login_required(views.VehicleListView.as_view()), name='vehicle_list'),
        path('create/', login_required(views.VehicleCreateView.as_view()), name='vehicle_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.VehicleUpdateView.as_view()), name='vehicle_update'),
            path('delete/', login_required(views.VehicleDeleteView.as_view()), name='vehicle_delete'),
        ])),
    ])),

    # ==================== ROUTE MANAGEMENT ====================
    path('routes/', include([
        path('', login_required(views.RouteListView.as_view()), name='route_list'),
        path('create/', login_required(views.RouteCreateView.as_view()), name='route_create'),

        # Route Stops
        path('stops/', include([
            path('', login_required(views.RouteStopListView.as_view()), name='stop_list'),
            path('create/', login_required(views.RouteStopCreateView.as_view()), name='stop_create'),
            path('<uuid:pk>/', include([
                path('edit/', login_required(views.RouteStopUpdateView.as_view()), name='stop_update'),
                path('delete/', login_required(views.RouteStopDeleteView.as_view()), name='stop_delete'),
            ])),
        ])),

        path('<uuid:pk>/', include([
            path('edit/', login_required(views.RouteUpdateView.as_view()), name='route_update'),
            path('delete/', login_required(views.RouteDeleteView.as_view()), name='route_delete'),
        ])),
    ])),

    # ==================== TRANSPORT ALLOCATIONS ====================
    path('allocations/', include([
        path('', login_required(views.TransportAllocationListView.as_view()), name='allocation_list'),
        path('create/', login_required(views.TransportAllocationCreateView.as_view()), name='allocation_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.TransportAllocationUpdateView.as_view()), name='allocation_update'),
            path('delete/', login_required(views.TransportAllocationDeleteView.as_view()), name='allocation_delete'),
        ])),
    ])),

    # ==================== ATTENDANCE MANAGEMENT ====================
    path('attendance/', include([
        path('', login_required(views.TransportAttendanceListView.as_view()), name='attendance_list'),
        path('mark/', login_required(views.TransportAttendanceCreateView.as_view()), name='attendance_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.TransportAttendanceUpdateView.as_view()), name='attendance_update'),
            path('delete/', login_required(views.TransportAttendanceDeleteView.as_view()), name='attendance_delete'),
        ])),
    ])),

    # ==================== MAINTENANCE MANAGEMENT ====================
    path('maintenance/', include([
        path('', login_required(views.MaintenanceListView.as_view()), name='maintenance_list'),
        path('create/', login_required(views.MaintenanceCreateView.as_view()), name='maintenance_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.MaintenanceUpdateView.as_view()), name='maintenance_update'),
            path('delete/', login_required(views.MaintenanceDeleteView.as_view()), name='maintenance_delete'),
        ])),
    ])),

    # ==================== FUEL MANAGEMENT ====================
    path('fuel/', include([
        path('', login_required(views.FuelListView.as_view()), name='fuel_list'),
        path('create/', login_required(views.FuelCreateView.as_view()), name='fuel_create'),
        path('<uuid:pk>/', include([
            path('edit/', login_required(views.FuelUpdateView.as_view()), name='fuel_update'),
            path('delete/', login_required(views.FuelDeleteView.as_view()), name='fuel_delete'),
        ])),
    ])),
]
