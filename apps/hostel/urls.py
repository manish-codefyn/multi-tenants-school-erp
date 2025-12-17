from django.urls import path, include
from . import views

app_name = 'hostel'

urlpatterns = [
    path('dashboard/', views.HostelDashboardView.as_view(), name='dashboard'),
    
    # Hostels
    path('hostels/', include([
        path('', views.HostelListView.as_view(), name='hostel_list'),
        path('import/', views.HostelImportView.as_view(), name='hostel_import'),
        path('create/', views.HostelCreateView.as_view(), name='hostel_create'),
        path('<uuid:pk>/', include([
            path('', views.HostelDetailView.as_view(), name='hostel_detail'),
            path('update/', views.HostelUpdateView.as_view(), name='hostel_update'),
            path('delete/', views.HostelDeleteView.as_view(), name='hostel_delete'),
        ])),
    ])),

    # Rooms
    path('rooms/', include([
        path('', views.RoomListView.as_view(), name='room_list'),
        path('import/', views.RoomImportView.as_view(), name='room_import'),
        path('create/', views.RoomCreateView.as_view(), name='room_create'),
        path('<uuid:pk>/', include([
            path('update/', views.RoomUpdateView.as_view(), name='room_update'),
            path('delete/', views.RoomDeleteView.as_view(), name='room_delete'),
        ])),
    ])),
    
    # Allocations
    path('allocations/', include([
        path('', views.HostelAllocationListView.as_view(), name='allocation_list'),
        path('import/', views.HostelAllocationImportView.as_view(), name='allocation_import'),
        path('create/', views.HostelAllocationCreateView.as_view(), name='allocation_create'),
        path('<uuid:pk>/', include([
            path('update/', views.HostelAllocationUpdateView.as_view(), name='allocation_update'),
            path('delete/', views.HostelAllocationDeleteView.as_view(), name='allocation_delete'),
        ])),
    ])),
    
    # Leave Applications
    path('leaves/', include([
        path('', views.LeaveApplicationListView.as_view(), name='leave_list'),
        path('create/', views.LeaveApplicationCreateView.as_view(), name='leave_create'),
        path('<uuid:pk>/', include([
            path('update/', views.LeaveApplicationUpdateView.as_view(), name='leave_update'),
            path('delete/', views.LeaveApplicationDeleteView.as_view(), name='leave_delete'),
        ])),
    ])),

    # Amenity Management
    path('amenities/', include([
        path('', views.AmenityListView.as_view(), name='amenity_list'),
        path('create/', views.AmenityCreateView.as_view(), name='amenity_create'),
        path('<uuid:pk>/', include([
            path('update/', views.AmenityUpdateView.as_view(), name='amenity_update'),
            path('delete/', views.AmenityDeleteView.as_view(), name='amenity_delete'),
        ])),
    ])),

    # Facility Management
    path('facilities/', include([
        path('', views.FacilityListView.as_view(), name='facility_list'),
        path('create/', views.FacilityCreateView.as_view(), name='facility_create'),
        path('<uuid:pk>/', include([
            path('update/', views.FacilityUpdateView.as_view(), name='facility_update'),
            path('delete/', views.FacilityDeleteView.as_view(), name='facility_delete'),
        ])),
    ])),

    # Mess Management (Replaces old mess_menu)
    path('mess/', include([
        path('dashboard/', views.MessDashboardView.as_view(), name='mess_dashboard'),
        
        # Categories
        path('categories/', include([
            path('', views.MessMenuCategoryListView.as_view(), name='mess_category_list'),
            path('create/', views.MessMenuCategoryCreateView.as_view(), name='mess_category_create'),
             path('<uuid:pk>/', include([
                path('update/', views.MessMenuCategoryUpdateView.as_view(), name='mess_category_update'),
                path('delete/', views.MessMenuCategoryDeleteView.as_view(), name='mess_category_delete'),
            ])),
        ])),
        
        # Items
        path('items/', include([
            path('', views.MessMenuItemListView.as_view(), name='mess_item_list'),
            path('import/', views.MessMenuItemImportView.as_view(), name='mess_item_import'),
            path('create/', views.MessMenuItemCreateView.as_view(), name='mess_item_create'),
             path('<uuid:pk>/', include([
                path('update/', views.MessMenuItemUpdateView.as_view(), name='mess_item_update'),
                path('delete/', views.MessMenuItemDeleteView.as_view(), name='mess_item_delete'),
            ])),
        ])),

        # Daily Menus
        path('daily/', include([
            path('', views.DailyMessMenuListView.as_view(), name='mess_daily_list'),
            path('create/', views.DailyMessMenuCreateView.as_view(), name='mess_daily_create'),
             path('<uuid:pk>/', include([
                path('update/', views.DailyMessMenuUpdateView.as_view(), name='mess_daily_update'),
                path('delete/', views.DailyMessMenuDeleteView.as_view(), name='mess_daily_delete'),
            ])),
        ])),

        # Subscriptions
        path('subscriptions/', include([
            path('', views.HostelMessSubscriptionListView.as_view(), name='mess_subscription_list'),
            path('create/', views.HostelMessSubscriptionCreateView.as_view(), name='mess_subscription_create'),
             path('<uuid:pk>/', include([
                path('update/', views.HostelMessSubscriptionUpdateView.as_view(), name='mess_subscription_update'),
                path('delete/', views.HostelMessSubscriptionDeleteView.as_view(), name='mess_subscription_delete'),
            ])),
        ])),
    ])),
    
    # Attendance
    path('attendance/', include([
        path('', views.HostelAttendanceListView.as_view(), name='attendance_list'),
        path('create/', views.HostelAttendanceCreateView.as_view(), name='attendance_create'),
        path('<uuid:pk>/', include([
            path('update/', views.HostelAttendanceUpdateView.as_view(), name='attendance_update'),
            path('delete/', views.HostelAttendanceDeleteView.as_view(), name='attendance_delete'),
        ])),
    ])),
]
