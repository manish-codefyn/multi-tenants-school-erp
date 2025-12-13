# apps/auth/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/switcher/', views.DashboardSwitcherView.as_view(), name='dashboard_switcher'),
    path('dashboard/switch/<str:dashboard_name>/', views.switch_dashboard, name='switch_dashboard'),
    
    # Common Dashboards
    path('staff/dashboard/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    path('student/dashboard/', views.StudentPortalDashboardView.as_view(), name='student_portal_dashboard'),
    path('admin/dashboard/', views.SystemAdminDashboardView.as_view(), name='system_admin_dashboard'),
    
    # Password Management
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/security/', views.SecuritySettingsView.as_view(), name='security_settings'),
    
    # MFA (Optional)
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa_verify'),
    path('mfa/setup/', views.MFASetupView.as_view(), name='mfa_setup'),
]