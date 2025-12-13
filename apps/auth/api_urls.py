from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views as views

urlpatterns = [
    # Authentication endpoints
    path('api-login/', views.login_view, name='api_login'),
    path('api-logout/', views.logout_view, name='api_logout'),
    path('api-register/', views.register_view, name='api_register'),
    path('api-token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    
    # Password management
    path('api-password/reset/', views.password_reset_request, name='api_password_reset_request'),
    path('api-password/reset/confirm/', views.password_reset_confirm, name='api_password_reset_confirm'),
    path('api-password/change/', views.change_password, name='api_change_password'),
    
    # MFA endpoints
    path('api-mfa/enable/', views.enable_mfa, name='api_enable_mfa'),
    path('mfa/disable/', views.disable_mfa, name='disable_mfa'),
    
    # User management
    path('profile/', views.user_profile, name='user_profile'),
    path('verify-email/', views.verify_email, name='verify_email'),
]

# Include JWT URLs
urlpatterns += [
    path('jwt/', include([
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ])),
]