from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    path('dashboard/', views.HostelDashboardView.as_view(), name='dashboard'),
    
    # Hostels
    path('', views.HostelListView.as_view(), name='hostel_list'),
    path('<int:pk>/', views.HostelDetailView.as_view(), name='hostel_detail'),
    path('create/', views.HostelCreateView.as_view(), name='hostel_create'),
    path('<int:pk>/update/', views.HostelUpdateView.as_view(), name='hostel_update'),
    path('<int:pk>/delete/', views.HostelDeleteView.as_view(), name='hostel_delete'),
    
    # Rooms
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),
    
    # Allocations
    path('allocations/', views.HostelAllocationListView.as_view(), name='allocation_list'),
    path('allocations/create/', views.HostelAllocationCreateView.as_view(), name='allocation_create'),
    path('allocations/<int:pk>/update/', views.HostelAllocationUpdateView.as_view(), name='allocation_update'),
    path('allocations/<int:pk>/delete/', views.HostelAllocationDeleteView.as_view(), name='allocation_delete'),
    
    # Leave Applications
    path('leaves/', views.LeaveApplicationListView.as_view(), name='leave_list'),
    path('leaves/create/', views.LeaveApplicationCreateView.as_view(), name='leave_create'),
    path('leaves/<int:pk>/update/', views.LeaveApplicationUpdateView.as_view(), name='leave_update'),
]
