# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='dashboard'),
    path('role/', views.UserListView.as_view(), name='user_list'),
    path('create/', views.UserCreateView.as_view(), name='user_create'),
    path('<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<uuid:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('<uuid:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('<uuid:pk>/toggle-status/', views.ToggleUserStatusView.as_view(), name='user_toggle_status'),
    path('<uuid:pk>/toggle-verification/', views.ToggleUserVerificationView.as_view(), name='user_toggle_verification'),
    path('<uuid:pk>/toggle-staff/', views.ToggleStaffView.as_view(), name='user_toggle_staff'),  # Added this line
    path('<uuid:pk>/change-role/', views.ChangeUserRoleView.as_view(), name='user_change_role'),
    path('<uuid:pk>/reset-password/', views.ResetUserPasswordView.as_view(), name='user_reset_password'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]