# apps/auth/views.py
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView, UpdateView
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from apps.core.utils.tenant import get_current_tenant
from apps.core.utils.dashboard_utils import DashboardRouter
from .forms import ProfileUpdateForm, CustomAuthenticationForm
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
# DO NOT import User directly, use get_user_model() when needed


# ============================================
# AUTHENTICATION VIEWS
# ============================================

class CustomLoginView(LoginView):
    """Enhanced login view with tenant branding and security features"""
    template_name = 'auth/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    redirect_field_name = 'next'
    
    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        # Log login attempt
        if request.method == 'POST':
            logger.info(f"Login attempt from {request.META.get('REMOTE_ADDR')}")
        
        # Check if user is already authenticated
        if request.user.is_authenticated and self.redirect_authenticated_user:
            return redirect(self.get_success_url())
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Get tenant branding
        tenant_branding = {
            'name': tenant.name if tenant else 'ERP System',
            'logo': self._get_tenant_logo(tenant),
            'primary_color': '#4e73df',  # Default, can be configured
            'secondary_color': '#858796',
        }
        
        # Check if MFA is required for this tenant
        if tenant and hasattr(tenant, 'configuration'):
            tenant_branding['mfa_required'] = tenant.configuration.mfa_required
        
        context.update({
            'tenant': tenant,
            'tenant_branding': tenant_branding,
            'page_title': 'Login' + (f' | {tenant.name}' if tenant else ''),
            'show_password_reset': True,
            'show_register': False,  # Set based on configuration
        })
        
        return context
    
    def get_success_url(self):
        # Check for next parameter
        redirect_to = self.request.GET.get(self.redirect_field_name, '')
        if redirect_to:
            return redirect_to
        
        # Use dashboard router for appropriate redirect
        if self.request.user.is_authenticated:
            return DashboardRouter.get_dashboard_url(self.request.user)
        
        return reverse_lazy('home')
    
    def form_valid(self, form):
        """Successful login"""
        response = super().form_valid(form)
        
        # Log successful login
        user = form.get_user()
        logger.info(f"User {user.email} logged in successfully from {self.request.META.get('REMOTE_ADDR')}")
        
        # Welcome message based on user role
        category = DashboardRouter.get_user_category(user)
        welcome_messages = {
            'system_superuser': 'Welcome to System Administration',
            'system': 'Welcome to Administration Dashboard',
            'staff': 'Welcome to Staff Portal',
            'student_family': 'Welcome to Student Portal',
        }
        
        welcome = welcome_messages.get(category, 'Welcome back!')
        messages.success(self.request, welcome)
        
        # Check if MFA is enabled for the user
        if hasattr(user, 'mfa_enabled') and user.mfa_enabled:
            # Redirect to MFA verification
            self.request.session['mfa_required'] = True
            self.request.session['user_id'] = user.id
            return redirect('mfa_verify')
        
        return response
    
    def form_invalid(self, form):
        """Failed login attempt"""
        messages.error(
            self.request,
            "Invalid email or password. Please try again.",
            extra_tags='alert-danger'
        )
        
        # Log failed attempt
        email = form.data.get('username', 'unknown')
        logger.warning(f"Failed login attempt for {email} from {self.request.META.get('REMOTE_ADDR')}")
        
        return super().form_invalid(form)
    
    def _get_tenant_logo(self, tenant):
        """Get tenant logo URL"""
        if tenant and hasattr(tenant, 'configuration') and tenant.configuration.logo:
            return tenant.configuration.logo.url
        return '/static/images/logo.png'


class CustomLogoutView(LogoutView):
    """Enhanced logout view with confirmation and logging"""
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        # Log logout
        if request.user.is_authenticated:
            logger.info(f"User {request.user.email} logged out")
            messages.info(request, "You have been successfully logged out.")
        
        return super().dispatch(request, *args, **kwargs)


# ============================================
# PASSWORD MANAGEMENT VIEWS
# ============================================

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Password change with security checks"""
    template_name = 'auth/password_change.html'
    success_url = reverse_lazy('password_change_done')
    
    @method_decorator(sensitive_post_parameters('old_password', 'new_password1', 'new_password2'))
    def dispatch(self, request, *args, **kwargs):
        # Check if password change is allowed
        if hasattr(request.user, 'is_account_locked') and request.user.is_account_locked:
            messages.error(request, "Your account is locked. Cannot change password.")
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Successful password change"""
        user = self.request.user
        
        # Update password changed timestamp
        if hasattr(user, 'password_changed_at'):
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password_changed_at'])
        
        # Log the password change
        logger.info(f"User {user.email} changed password")
        
        messages.success(
            self.request,
            "Your password has been changed successfully!",
            extra_tags='alert-success'
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Change Password',
            'active_tab': 'security',
        })
        return context


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    """Password change confirmation"""
    template_name = 'auth/password_change_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Password Changed',
            'next_steps': [
                'Your password has been updated successfully.',
                'You can now log in with your new password.',
                'Consider enabling two-factor authentication for added security.'
            ]
        })
        return context


class CustomPasswordResetView(PasswordResetView):
    """Password reset request"""
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/emails/password_reset_email.html'
    subject_template_name = 'auth/emails/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        context.update({
            'page_title': 'Reset Password',
            'tenant_name': tenant.name if tenant else 'System',
        })
        return context
    
    def form_valid(self, form):
        """Successful password reset request"""
        response = super().form_valid(form)
        
        # Don't reveal whether email exists for security
        messages.info(
            self.request,
            "If an account exists with the email you entered, you will receive a password reset link.",
            extra_tags='alert-info'
        )
        
        return response


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Password reset email sent confirmation"""
    template_name = 'auth/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Reset Email Sent',
            'instructions': [
                'We\'ve emailed you instructions for setting your password.',
                'You should receive them shortly.',
                'If you don\'t receive an email, please check your spam folder.',
                'Make sure you entered the email address you registered with.'
            ]
        })
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirmation"""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    @method_decorator(sensitive_post_parameters('new_password1', 'new_password2'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Successful password reset"""
        user = form.save()
        
        # Log the password reset
        logger.info(f"Password reset for user {user.email}")
        
        # Clear failed login attempts
        if hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
        
        messages.success(
            self.request,
            "Your password has been reset successfully! You can now log in with your new password.",
            extra_tags='alert-success'
        )
        
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Password reset completion"""
    template_name = 'auth/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Password Reset Complete',
            'next_action': 'You can now log in with your new password.',
        })
        return context


# ============================================
# DASHBOARD & PROFILE VIEWS
# ============================================

def dashboard_redirect(request):
    """
    Professional dashboard redirection with permission checking and logging
    """
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to access your dashboard.")
        return redirect('login')
    
    user = request.user
    
    # Log dashboard access attempt
    logger.info(f"Dashboard redirect for user {user.email} (role: {user.role})")
    
    # Get dashboard information
    dashboard_info = DashboardRouter.get_user_dashboard_info(user)
    
    # Check if user has permission for their primary dashboard
    if not dashboard_info['has_permission']:
        messages.error(
            request,
            f"You don't have permission to access the {user.role.replace('_', ' ').title()} dashboard. "
            "Please contact your administrator.",
            extra_tags='alert-danger'
        )
        
        # Log permission denied
        logger.warning(f"Permission denied for user {user.email} to access {user.role} dashboard")
        
        # Try to redirect to an available dashboard
        available_dashboards = dashboard_info['available_dashboards']
        if available_dashboards:
            # Redirect to first available dashboard
            return redirect(available_dashboards[0]['url'])
        
        # No dashboards available, go home
        return redirect('home')
    
    # Set welcome message if first time
    if not request.session.get('dashboard_welcomed'):
        category = DashboardRouter.get_user_category(user)
        welcome_messages = {
            'system_superuser': 'Welcome to System Administration Dashboard',
            'system': 'Welcome to Administration Dashboard',
            'staff': 'Welcome to Staff Portal',
            'student_family': 'Welcome to Student Portal',
        }
        
        welcome = welcome_messages.get(category, 'Welcome to your dashboard')
        messages.success(request, welcome, extra_tags='alert-success')
        request.session['dashboard_welcomed'] = True
    
    # Redirect to appropriate dashboard
    return redirect(dashboard_info['url'])


class DashboardSwitcherView(LoginRequiredMixin, TemplateView):
    """View to switch between available dashboards"""
    template_name = 'auth/dashboard_switcher.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        dashboard_info = DashboardRouter.get_user_dashboard_info(user)
        
        context.update({
            'page_title': 'Dashboard Switcher',
            'user_info': dashboard_info['user'],
            'available_dashboards': dashboard_info['available_dashboards'],
            'current_dashboard': dashboard_info['url'],
            'user_category': DashboardRouter.get_user_category(user),
        })
        
        return context


def switch_dashboard(request, dashboard_name):
    """
    Switch to a different dashboard
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # Get all available dashboards
    available_dashboards = DashboardRouter.get_available_dashboards(user)
    
    # Find the requested dashboard
    target_dashboard = None
    for dashboard in available_dashboards:
        if dashboard['name'].lower().replace(' ', '_') == dashboard_name.lower():
            target_dashboard = dashboard
            break
    
    if target_dashboard:
        # Log dashboard switch
        logger.info(f"User {user.email} switched to {target_dashboard['name']}")
        
        messages.success(
            request,
            f"Switched to {target_dashboard['name']}",
            extra_tags='alert-success'
        )
        return redirect(target_dashboard['url'])
    else:
        messages.error(
            request,
            "Dashboard not found or access denied.",
            extra_tags='alert-danger'
        )
        return redirect('dashboard_switcher')


# ============================================
# COMMON DASHBOARD VIEWS
# ============================================

class BaseDashboardView(LoginRequiredMixin, TemplateView):
    """Base class for all dashboard views"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': self.get_page_title(),
            'quick_actions': self.get_quick_actions(),
            'recent_activities': self.get_recent_activities(),
            'notifications': self.get_notifications(),
        })
        return context
    
    def get_page_title(self):
        """Get page title for the dashboard"""
        return f"{self.dashboard_name} | {self.request.user.get_full_name()}"
    
    def get_quick_actions(self):
        """Get quick actions for the dashboard"""
        return []
    
    def get_recent_activities(self):
        """Get recent activities for the dashboard"""
        return []

    def get_notifications(self):
        """Get notifications for the user"""
        return []


class SystemAdminDashboardView(BaseDashboardView):
    """Dashboard for system administrators and super_admins"""
    template_name = 'dashboards/system_admin.html'
    dashboard_name = 'System Administration'
    dashboard_type = 'system'
    
    def get_quick_actions(self):
        return [
            {'name': 'Manage Users', 'url': reverse_lazy('admin:users_user_changelist'), 'icon': 'users'},
            {'name': 'System Settings', 'url': reverse_lazy('admin:app_list', args=('configuration',)), 'icon': 'settings'},
            {'name': 'View Reports', 'url': reverse_lazy('analytics:dashboard'), 'icon': 'bar-chart'},
            # {'name': 'Database Backup', 'url': reverse_lazy('admin:backup'), 'icon': 'database'},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use get_user_model() instead of direct import
        User = get_user_model()
        from apps.tenants.models import Tenant
        
        context.update({
            'total_users': User.objects.count(),
            'total_tenants': Tenant.objects.count(),
            'active_tenants': Tenant.objects.filter(is_active=True).count(),
            'system_stats': self.get_system_stats(),
        })
        
        return context
    
    def get_system_stats(self):
        """Get system statistics"""
        # Implement system statistics
        return {
            'cpu_usage': 45,
            'memory_usage': 68,
            'disk_usage': 32,
            'active_sessions': 24,
        }


class StaffDashboardView(BaseDashboardView):
    """Common dashboard for all staff roles (teachers, principals, accountants, etc.)"""
    template_name = 'dashboards/staff.html'
    dashboard_name = 'Staff Portal'
    dashboard_type = 'staff'
    
    def get_quick_actions(self):
        user = self.request.user
        actions = []
        
        # Common staff actions
        common_actions = [
            {'name': 'My Schedule', 'url': reverse_lazy('academics:schedule'), 'icon': 'calendar'},
            {'name': 'Attendance', 'url': reverse_lazy('academics:attendance'), 'icon': 'check-circle'},
            {'name': 'Messages', 'url': reverse_lazy('communications:messages'), 'icon': 'message-square'},
        ]
        
        # Role-specific actions
        if user.role in ['teacher', 'principal', 'headmaster']:
            actions.extend([
                {'name': 'Grade Students', 'url': reverse_lazy('academics:grading'), 'icon': 'edit-3'},
                {'name': 'Assignments', 'url': reverse_lazy('academics:assignments'), 'icon': 'file-text'},
            ])
        
        if user.role in ['accountant', 'finance_staff']:
            actions.extend([
                {'name': 'Process Payments', 'url': reverse_lazy('finance:payments'), 'icon': 'credit-card'},
                {'name': 'Generate Reports', 'url': reverse_lazy('finance:reports'), 'icon': 'file-text'},
            ])
        
        if user.role in ['librarian']:
            actions.extend([
                {'name': 'Manage Books', 'url': reverse_lazy('library:books'), 'icon': 'book'},
                {'name': 'Issue Books', 'url': reverse_lazy('library:issue'), 'icon': 'book-open'},
            ])
        
        return common_actions + actions


class StudentPortalDashboardView(BaseDashboardView):
    """Common dashboard for students, parents, and guardians"""
    template_name = 'dashboards/student_portal.html'
    dashboard_name = 'Student Portal'
    dashboard_type = 'student_family'
    
    def get_quick_actions(self):
        user = self.request.user
        actions = []
        
        # Student actions
        if user.role == 'student':
            actions = [
                {'name': 'My Courses', 'url': reverse_lazy('academics:my_courses'), 'icon': 'book'},
                {'name': 'Grades', 'url': reverse_lazy('academics:my_grades'), 'icon': 'award'},
                {'name': 'Attendance', 'url': reverse_lazy('academics:my_attendance'), 'icon': 'check-circle'},
                {'name': 'Assignments', 'url': reverse_lazy('academics:my_assignments'), 'icon': 'file-text'},
            ]
        
        # Parent/Guardian actions
        elif user.role in ['parent', 'guardian']:
            actions = [
                {'name': 'Child Progress', 'url': reverse_lazy('students:child_progress'), 'icon': 'trending-up'},
                {'name': 'Attendance', 'url': reverse_lazy('students:child_attendance'), 'icon': 'calendar'},
                {'name': 'Fee Status', 'url': reverse_lazy('finance:fee_status'), 'icon': 'credit-card'},
                {'name': 'Communications', 'url': reverse_lazy('communications:parent_messages'), 'icon': 'message-square'},
            ]
        
        # Common actions
        common_actions = [
            {'name': 'Timetable', 'url': reverse_lazy('academics:timetable'), 'icon': 'clock'},
            {'name': 'Events', 'url': reverse_lazy('events:calendar'), 'icon': 'calendar'},
            {'name': 'Library', 'url': reverse_lazy('library:catalog'), 'icon': 'book-open'},
        ]
        
        return actions + common_actions


# ============================================
# PROFILE VIEWS
# ============================================

class ProfileView(LoginRequiredMixin, UpdateView):
    """User profile management"""
    form_class = ProfileUpdateForm
    template_name = 'auth/profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_form_class(self):
        """Get the form class for the custom user model"""
        return ProfileUpdateForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'page_title': 'My Profile',
            'active_tab': 'profile',
            'user': user,
            'mfa_enabled': getattr(user, 'mfa_enabled', False),
            'last_login': user.last_login,
            'account_created': user.date_joined,
            'security_events': self.get_security_events(user),
        })
        
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        """Successful profile update"""
        user = form.save()
        
        # Log profile update
        logger.info(f"User {user.email} updated profile")
        
        messages.success(
            self.request,
            "Your profile has been updated successfully!",
            extra_tags='alert-success'
        )
        
        return super().form_valid(form)
    
    def get_security_events(self, user):
        """Get recent security events for the user"""
        from apps.auth.models import SecurityEvent
        
        try:
            return SecurityEvent.objects.filter(user=user).order_by('-created_at')[:10]
        except Exception:
            return []


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    """Security settings management"""
    template_name = 'auth/security_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'page_title': 'Security Settings',
            'active_tab': 'security',
            'user': user,
            'mfa_enabled': getattr(user, 'mfa_enabled', False),
            'mfa_secret': getattr(user, 'mfa_secret', None),
            'login_history': self.get_login_history(user),
            'api_tokens': self.get_api_tokens(user),
        })
        
        return context
    
    def get_login_history(self, user):
        """Get login history"""
        from apps.auth.models import LoginAttempt
        
        try:
            return LoginAttempt.objects.filter(user=user).order_by('-created_at')[:20]
        except Exception:
            return []
    
    def get_api_tokens(self, user):
        """Get API tokens"""
        from apps.auth.models import APIToken
        
        try:
            return APIToken.objects.filter(user=user, is_active=True)
        except Exception:
            return []


# ============================================
# MFA VIEWS (Optional)
# ============================================

class MFAVerifyView(LoginRequiredMixin, TemplateView):
    """MFA verification view"""
    template_name = 'auth/mfa_verify.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if MFA is required in session
        if not request.session.get('mfa_required'):
            return redirect('dashboard_redirect')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.request.session.get('user_id')
        
        if user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                context.update({
                    'page_title': 'Two-Factor Authentication',
                    'user': user,
                    'mfa_qr_code': user.get_mfa_provisioning_uri() if getattr(user, 'mfa_secret', None) else None,
                })
            except User.DoesNotExist:
                pass
        
        return context


class MFASetupView(LoginRequiredMixin, TemplateView):
    """MFA setup view"""
    template_name = 'auth/mfa_setup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not getattr(user, 'mfa_secret', None):
            if hasattr(user, 'generate_mfa_secret'):
                user.generate_mfa_secret()
        
        context.update({
            'page_title': 'Setup Two-Factor Authentication',
            'user': user,
            'mfa_secret': getattr(user, 'mfa_secret', None),
            'mfa_qr_code': user.get_mfa_provisioning_uri() if hasattr(user, 'get_mfa_provisioning_uri') else None,
        })
        
        return context