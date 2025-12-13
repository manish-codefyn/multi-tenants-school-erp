# apps/auth/views.py
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import RedirectView, UpdateView, CreateView, TemplateView
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth import login, update_session_auth_hash
from django.http import HttpResponseRedirect, JsonResponse
import pyotp
import qrcode
import base64
from io import BytesIO

from apps.core.utils.tenant import get_current_tenant
from apps.core.utils.dashboard_utils import DashboardRouter
from .forms import ProfileUpdateForm, CustomAuthenticationForm, MFASetupForm, MFAVerifyForm
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
        if request.user.is_authenticated:
            # Check if user has a role
            if not request.user.role and not request.user.is_superuser:
                messages.warning(request, "Please get admitted first then login.")
                return redirect('admission:landing')
                
            if self.redirect_authenticated_user:
                return redirect(self.get_success_url())
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Use the branding_info property from Tenant model
        if tenant:
            tenant_branding = tenant.branding_info
        else:
            tenant_branding = {
                'name': settings.TENANT_BRANDING.get('name', 'ERP System'),
                'logo': settings.TENANT_BRANDING.get('logo', '/static/images/logo.png'),
                'primary_color': settings.TENANT_BRANDING.get('primary_color', '#4e73df'),
                'secondary_color': settings.TENANT_BRANDING.get('secondary_color', '#858796'),
                'mfa_required': settings.TENANT_BRANDING.get('mfa_required', False),
            }
        
        context.update({
            'tenant': tenant,
            'tenant_branding': tenant_branding,
            'page_title': 'Login' + (f' | {tenant.name}' if tenant else ''),
            'show_password_reset': True,
            'show_register': getattr(settings, 'ALLOW_REGISTRATION', False),
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
        user = form.get_user()
        
        # Log successful login
        logger.info(f"User {user.email} logged in successfully from {self.request.META.get('REMOTE_ADDR')}")
        
        # Check if user has a role
        if not user.role:
            messages.warning(self.request, "Please get admitted first then login.")
            return redirect('admission:landing')
        
        # Check if MFA is enabled for the user
        tenant = get_current_tenant()
        user_has_mfa = getattr(user, 'mfa_enabled', False) and getattr(user, 'mfa_secret', None)
        
        if tenant and tenant.mfa_required and user_has_mfa:
            # Store user ID in session for MFA verification
            self.request.session['mfa_required'] = True
            self.request.session['mfa_user_id'] = user.id
            
            # Don't log the user in yet, wait for MFA verification
            # Instead, redirect to MFA verification page
            return redirect('mfa_verify')
        
        # Regular login without MFA
        response = super().form_valid(form)
        
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


class SignupView(CreateView):
    """User registration view"""
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')
    
    def get_form_class(self):
        from .forms import SignupForm
        return SignupForm
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        tenant = get_current_tenant()
        if tenant:
            form.instance.tenant = tenant
        return form
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Use the branding_info property from Tenant model
        if tenant:
            tenant_branding = tenant.branding_info
        else:
            tenant_branding = {
                'name': settings.TENANT_BRANDING.get('name', 'ERP System'),
                'logo': settings.TENANT_BRANDING.get('logo', '/static/images/logo.png'),
                'primary_color': settings.TENANT_BRANDING.get('primary_color', '#4e73df'),
                'secondary_color': settings.TENANT_BRANDING.get('secondary_color', '#858796'),
            }
            
        context.update({
            'tenant': tenant,
            'tenant_branding': tenant_branding,
            'page_title': 'Sign Up' + (f' | {tenant.name}' if tenant else ''),
            'allow_registration': getattr(settings, 'ALLOW_REGISTRATION', True),
        })
        return context
        
    def form_valid(self, form):
        # Set tenant
        tenant = get_current_tenant()
        if tenant:
            form.instance.tenant = tenant
        
        # # Set default role based on tenant configuration or form data
        # if not form.instance.role:
        #     form.instance.role = 'student'  # Default role
        if not form.instance.role:
            form.instance.role = None  # Default role
        

        # Set active (or require verification)
        form.instance.is_active = True
        form.instance.is_verified = False  # Require email verification ideally
        
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            "Account created successfully! Please log in.",
            extra_tags='alert-success'
        )
        
        return response
        
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            "Please correct the errors below.",
            extra_tags='alert-danger'
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Enhanced logout view with confirmation and logging"""
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        # Log logout
        if request.user.is_authenticated:
            logger.info(f"User {request.user.email} logged out")
            messages.info(request, "You have been successfully logged out.")
        
        # Clear all session data
        request.session.flush()
        
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
    
    def get_form_class(self):
        from .forms import CustomPasswordChangeForm
        return CustomPasswordChangeForm
    
    def form_valid(self, form):
        """Successful password change"""
        user = form.save()
        
        # Update password changed timestamp
        if hasattr(user, 'password_changed_at'):
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password_changed_at'])
        
        # Log the password change
        logger.info(f"User {user.email} changed password")
        
        # Keep the user logged in
        update_session_auth_hash(self.request, user)
        
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

@login_required
def dashboard_redirect(request):
    """
    Professional dashboard redirection with permission checking and logging
    """
    user = request.user
    
    # Log dashboard access attempt
    logger.info(f"Dashboard redirect for user {user.email} (role: {user.role})")
    
    # Check if user has a role
    if not user.role and not user.is_superuser:
        messages.warning(request, "Please get admitted first then login.")
        return redirect('admission:landing')
    
    # Get dashboard information
    dashboard_info = DashboardRouter.get_user_dashboard_info(user)
    
    # Check if user has permission for their primary dashboard
    if not dashboard_info.get('has_permission', True):
        messages.error(
            request,
            f"You don't have permission to access the {user.role.replace('_', ' ').title()} dashboard. "
            "Please contact your administrator.",
            extra_tags='alert-danger'
        )
        
        # Log permission denied
        logger.warning(f"Permission denied for user {user.email} to access {user.role} dashboard")
        
        # Try to redirect to an available dashboard
        available_dashboards = dashboard_info.get('available_dashboards', [])
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
    return redirect(dashboard_info.get('url', 'home'))


class DashboardSwitcherView(LoginRequiredMixin, TemplateView):
    """View to switch between available dashboards"""
    template_name = 'auth/dashboard_switcher.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        dashboard_info = DashboardRouter.get_user_dashboard_info(user)
        
        context.update({
            'page_title': 'Dashboard Switcher',
            'user_info': dashboard_info.get('user', user),
            'available_dashboards': dashboard_info.get('available_dashboards', []),
            'current_dashboard': dashboard_info.get('url', ''),
            'user_category': DashboardRouter.get_user_category(user),
        })
        
        return context


@login_required
def switch_dashboard(request, dashboard_name):
    """
    Switch to a different dashboard
    """
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
        user = self.request.user
        
        context.update({
            'page_title': self.get_page_title(),
            'quick_actions': self.get_quick_actions(),
            'recent_activities': self.get_recent_activities(),
            'notifications': self.get_notifications(),
            'user': user,
            'dashboard_type': self.dashboard_type,
            'dashboard_name': self.dashboard_name,
        })
        return context
    
    def get_page_title(self):
        """Get page title for the dashboard"""
        user_name = self.request.user.get_full_name() or self.request.user.email
        return f"{self.dashboard_name} | {user_name}"
    
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
            {'name': 'Audit Logs', 'url': reverse_lazy('admin:apps_auth_securityevent_changelist'), 'icon': 'shield'},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use get_user_model() instead of direct import
        User = get_user_model()
        
        # Try to import Tenant model safely
        try:
            from apps.tenants.models import Tenant
            # Basic Stats
            total_tenants = Tenant.objects.count()
            active_tenants = Tenant.objects.filter(status='active', is_active=True).count()
            suspended_tenants = Tenant.objects.filter(status='suspended').count()
            
            # Recent Tenants
            recent_tenants = Tenant.objects.order_by('-created_at')[:5]
            
            # Tenant Growth Chart Data (Last 12 Months)
            from django.db.models.functions import TruncMonth
            from django.utils import timezone
            import datetime
            
            last_12_months = timezone.now() - datetime.timedelta(days=365)
            tenant_growth = Tenant.objects.filter(created_at__gte=last_12_months)\
                .annotate(month=TruncMonth('created_at'))\
                .values('month')\
                .annotate(count=Count('id'))\
                .order_by('month')
                
            growth_labels = []
            growth_data = []
            
            for entry in tenant_growth:
                growth_labels.append(entry['month'].strftime('%b %Y'))
                growth_data.append(entry['count'])
                
        except ImportError:
            total_tenants = 0
            active_tenants = 0
            suspended_tenants = 0
            recent_tenants = []
            growth_labels = []
            growth_data = []
        
        # User Stats
        total_users = User.objects.count()
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        # User Role Distribution
        role_distribution = User.objects.values('role').annotate(count=Count('id')).order_by('-count')
        role_labels = []
        role_data = []
        
        for entry in role_distribution:
            role_name = entry['role'].replace('_', ' ').title() if entry['role'] else 'Unknown'
            role_labels.append(role_name)
            role_data.append(entry['count'])
            
        context.update({
            # Stats
            'total_users': total_users,
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'suspended_tenants': suspended_tenants,
            
            # Tables
            'recent_tenants': recent_tenants,
            'recent_users': recent_users,
            
            # Charts
            'tenant_growth_labels': growth_labels,
            'tenant_growth_data': growth_data,
            'user_role_labels': role_labels,
            'user_role_data': role_data,
            
            # System
            'system_stats': self.get_system_stats(),
        })
        
        return context
    
    def get_system_stats(self):
        """Get system statistics"""
        # In a real app, you might use psutil here
        import random
        return {
            'cpu_usage': random.randint(20, 45),
            'memory_usage': random.randint(40, 70),
            'disk_usage': 32,
            'active_sessions': 24, # You could query django_session if needed
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
                {'name': 'Lesson Plans', 'url': reverse_lazy('academics:lesson_plans'), 'icon': 'book-open'},
            ])
        
        if user.role in ['accountant', 'finance_staff']:
            actions.extend([
                {'name': 'Process Payments', 'url': reverse_lazy('finance:payments'), 'icon': 'credit-card'},
                {'name': 'Generate Reports', 'url': reverse_lazy('finance:reports'), 'icon': 'file-text'},
                {'name': 'Fee Management', 'url': reverse_lazy('finance:fee_management'), 'icon': 'dollar-sign'},
            ])
        
        if user.role in ['librarian']:
            actions.extend([
                {'name': 'Manage Books', 'url': reverse_lazy('library:books'), 'icon': 'book'},
                {'name': 'Issue Books', 'url': reverse_lazy('library:issue'), 'icon': 'book-open'},
                {'name': 'Catalog', 'url': reverse_lazy('library:catalog'), 'icon': 'list'},
            ])
        
        if user.role in ['admin', 'administrator']:
            actions.extend([
                {'name': 'Manage Staff', 'url': reverse_lazy('staff:management'), 'icon': 'users'},
                {'name': 'System Settings', 'url': reverse_lazy('configuration:settings'), 'icon': 'settings'},
                {'name': 'Reports', 'url': reverse_lazy('reports:dashboard'), 'icon': 'bar-chart'},
            ])
        
        return common_actions + actions
    
    def get_recent_activities(self):
        """Get recent activities for staff"""
        # This would typically come from your activity tracking system
        return [
            {'title': 'Class attendance marked', 'time': '2 hours ago', 'type': 'academic'},
            {'title': 'New assignment created', 'time': '5 hours ago', 'type': 'academic'},
            {'title': 'Meeting scheduled', 'time': '1 day ago', 'type': 'calendar'},
            {'title': 'Report generated', 'time': '2 days ago', 'type': 'report'},
        ]


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
            {'name': 'Resources', 'url': reverse_lazy('resources:index'), 'icon': 'folder'},
        ]
        
        return actions + common_actions
    
    def get_recent_activities(self):
        """Get recent activities for student/family"""
        user = self.request.user
        
        if user.role == 'student':
            return [
                {'title': 'Assignment submitted', 'time': 'Yesterday', 'type': 'academic'},
                {'title': 'Grade updated', 'time': '2 days ago', 'type': 'academic'},
                {'title': 'New announcement', 'time': '3 days ago', 'type': 'announcement'},
                {'title': 'Event reminder', 'time': '1 week ago', 'type': 'calendar'},
            ]
        else:  # parent/guardian
            return [
                {'title': 'Fee payment reminder', 'time': 'Today', 'type': 'finance'},
                {'title': 'Parent-teacher meeting', 'time': 'Tomorrow', 'type': 'calendar'},
                {'title': 'Child attendance report', 'time': '2 days ago', 'type': 'academic'},
                {'title': 'School announcement', 'time': '1 week ago', 'type': 'announcement'},
            ]


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
            'mfa_enabled': getattr(user, 'mfa_enabled', False) and getattr(user, 'mfa_secret', None),
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
        try:
            from apps.auth.models import SecurityEvent
            return SecurityEvent.objects.filter(user=user).order_by('-created_at')[:10]
        except ImportError:
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
            'mfa_enabled': getattr(user, 'mfa_enabled', False) and getattr(user, 'mfa_secret', None),
            'login_history': self.get_login_history(user),
            'api_tokens': self.get_api_tokens(user),
        })
        
        return context
    
    def get_login_history(self, user):
        """Get login history"""
        try:
            from apps.auth.models import LoginAttempt
            return LoginAttempt.objects.filter(user=user).order_by('-created_at')[:20]
        except ImportError:
            return []
    
    def get_api_tokens(self, user):
        """Get API tokens"""
        try:
            from apps.auth.models import APIToken
            return APIToken.objects.filter(user=user, is_active=True)
        except ImportError:
            return []


# ============================================
# MFA VIEWS
# ============================================

class MFAVerifyView(TemplateView):
    """MFA verification view"""
    template_name = 'auth/mfa_verify.html'
    form_class = MFAVerifyForm
    
    def dispatch(self, request, *args, **kwargs):
        # Check if MFA is required in session
        if not request.session.get('mfa_required'):
            return redirect('login')
        
        # Get user from session
        user_id = request.session.get('mfa_user_id')
        if not user_id:
            messages.error(request, "Session expired. Please log in again.")
            return redirect('login')
        
        # Get user model and check if user exists
        User = get_user_model()
        try:
            self.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found. Please log in again.")
            return redirect('login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Two-Factor Authentication',
            'user': self.user,
            'form': self.form_class(),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle MFA verification code submission"""
        form = self.form_class(request.POST)
        
        if not form.is_valid():
            messages.error(request, "Please enter a valid verification code.")
            return self.render_to_response(self.get_context_data(form=form))
        
        verification_code = form.cleaned_data['verification_code']
        
        # Verify MFA code
        if hasattr(self.user, 'verify_mfa_code'):
            is_valid = self.user.verify_mfa_code(verification_code)
        else:
            # Fallback verification
            if getattr(self.user, 'mfa_secret', None):
                totp = pyotp.TOTP(self.user.mfa_secret)
                is_valid = totp.verify(verification_code, valid_window=1)
            else:
                is_valid = False
        
        if is_valid:
            # Clear MFA session flags
            request.session.pop('mfa_required', None)
            request.session.pop('mfa_user_id', None)
            
            # Log the successful MFA verification
            logger.info(f"User {self.user.email} passed MFA verification")
            
            # Log the user in
            login(request, self.user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Set welcome message
            category = DashboardRouter.get_user_category(self.user)
            welcome_messages = {
                'system_superuser': 'Welcome to System Administration',
                'system': 'Welcome to Administration Dashboard',
                'staff': 'Welcome to Staff Portal',
                'student_family': 'Welcome to Student Portal',
            }
            
            welcome = welcome_messages.get(category, 'Welcome back!')
            messages.success(request, f"{welcome} Two-factor authentication successful!")
            
            # Redirect to dashboard
            dashboard_url = DashboardRouter.get_dashboard_url(self.user)
            return redirect(dashboard_url)
        else:
            messages.error(request, "Invalid verification code. Please try again.")
            
            # Log failed MFA attempt
            logger.warning(f"Failed MFA attempt for user {self.user.email}")
            
            return self.render_to_response(self.get_context_data(form=form))


class MFASetupView(LoginRequiredMixin, TemplateView):
    """MFA setup view"""
    template_name = 'auth/mfa_setup.html'
    form_class = MFASetupForm
    
    def dispatch(self, request, *args, **kwargs):
        # Check if MFA is already enabled
        if getattr(request.user, 'mfa_enabled', False) and getattr(request.user, 'mfa_secret', None):
            messages.info(request, "MFA is already enabled for your account.")
            return redirect('security_settings')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Generate MFA secret if not exists
        if not getattr(user, 'mfa_secret', None):
            if hasattr(user, 'generate_mfa_secret'):
                user.generate_mfa_secret()
                user.save(update_fields=['mfa_secret'])
            else:
                # Generate secret using pyotp
                secret = pyotp.random_base32()
                user.mfa_secret = secret
                user.save(update_fields=['mfa_secret'])
        
        # Generate QR code
        qr_code_url = None
        if user.mfa_secret:
            totp = pyotp.TOTP(user.mfa_secret)
            issuer_name = get_current_tenant().name if get_current_tenant() else "ERP System"
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name=issuer_name
            )
            
            # Generate QR code image
            qr = qrcode.make(provisioning_uri)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        
        context.update({
            'page_title': 'Setup Two-Factor Authentication',
            'user': user,
            'form': self.form_class(),
            'mfa_secret': user.mfa_secret,
            'mfa_secret_formatted': ' '.join([user.mfa_secret[i:i+4] for i in range(0, len(user.mfa_secret), 4)]) if user.mfa_secret else None,
            'mfa_qr_code': qr_code_url,
            'issuer_name': get_current_tenant().name if get_current_tenant() else "ERP System",
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle MFA setup verification"""
        form = self.form_class(request.POST)
        user = request.user
        
        if not form.is_valid():
            messages.error(request, "Please enter a valid verification code.")
            return self.render_to_response(self.get_context_data(form=form))
        
        verification_code = form.cleaned_data['verification_code']
        
        # Verify MFA code
        if user.mfa_secret:
            totp = pyotp.TOTP(user.mfa_secret)
            is_valid = totp.verify(verification_code, valid_window=1)
        else:
            is_valid = False
        
        if is_valid:
            # Enable MFA for user
            user.mfa_enabled = True
            user.save(update_fields=['mfa_enabled'])
            
            # Log MFA setup
            logger.info(f"User {user.email} enabled MFA")
            
            # Create backup codes (optional)
            if hasattr(user, 'generate_mfa_backup_codes'):
                backup_codes = user.generate_mfa_backup_codes()
                request.session['mfa_backup_codes'] = backup_codes
                messages.success(request, "Two-factor authentication has been enabled successfully! Please save your backup codes.")
                return redirect('mfa_backup_codes')
            else:
                messages.success(request, "Two-factor authentication has been enabled successfully!")
                return redirect('security_settings')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
            return self.render_to_response(self.get_context_data(form=form))


class MFADisableView(LoginRequiredMixin, TemplateView):
    """Disable MFA for user"""
    template_name = 'auth/mfa_disable.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if MFA is enabled
        if not getattr(request.user, 'mfa_enabled', False):
            messages.info(request, "MFA is not enabled for your account.")
            return redirect('security_settings')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Disable Two-Factor Authentication',
            'user': self.request.user,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle MFA disable"""
        user = request.user
        
        # Verify password
        password = request.POST.get('password', '')
        if not user.check_password(password):
            messages.error(request, "Invalid password. Please try again.")
            return self.render_to_response(self.get_context_data())
        
        # Disable MFA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.save(update_fields=['mfa_enabled', 'mfa_secret'])
        
        # Log MFA disable
        logger.info(f"User {user.email} disabled MFA")
        
        messages.success(request, "Two-factor authentication has been disabled for your account.")
        return redirect('security_settings')


class MFABackupCodesView(LoginRequiredMixin, TemplateView):
    """Display and regenerate MFA backup codes"""
    template_name = 'auth/mfa_backup_codes.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has MFA enabled
        if not getattr(request.user, 'mfa_enabled', False):
            messages.info(request, "MFA is not enabled for your account.")
            return redirect('security_settings')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get backup codes from session or generate new ones
        backup_codes = self.request.session.get('mfa_backup_codes', [])
        
        # If no backup codes in session and user has method to generate them
        if not backup_codes and hasattr(user, 'get_mfa_backup_codes'):
            backup_codes = user.get_mfa_backup_codes()
        
        context.update({
            'page_title': 'MFA Backup Codes',
            'user': user,
            'backup_codes': backup_codes,
            'codes_displayed': bool(backup_codes),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Regenerate backup codes"""
        user = request.user
        
        # Verify password
        password = request.POST.get('password', '')
        if not user.check_password(password):
            messages.error(request, "Invalid password. Please try again.")
            return self.render_to_response(self.get_context_data())
        
        # Generate new backup codes
        if hasattr(user, 'generate_mfa_backup_codes'):
            new_codes = user.generate_mfa_backup_codes()
            request.session['mfa_backup_codes'] = new_codes
            
            # Log backup codes regeneration
            logger.info(f"User {user.email} regenerated MFA backup codes")
            
            messages.success(request, "New backup codes have been generated. Please save them securely.")
        else:
            messages.info(request, "Backup code generation is not available.")
        
        return redirect('mfa_backup_codes')


# ============================================
# HELPER VIEWS
# ============================================

class HealthCheckView(TemplateView):
    """Health check endpoint for load balancers and monitoring"""
    template_name = 'auth/health_check.html'
    
    def get(self, request, *args, **kwargs):
        # Perform basic health checks
        checks = {
            'database': self.check_database(),
            'cache': self.check_cache(),
            'storage': self.check_storage(),
        }
        
        # Determine overall status
        all_healthy = all(checks.values())
        
        if request.GET.get('format') == 'json':
            return JsonResponse({
                'status': 'healthy' if all_healthy else 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'checks': checks,
            })
        
        context = self.get_context_data(**kwargs)
        context.update({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'checks': checks,
            'timestamp': timezone.now(),
        })
        return self.render_to_response(context)
    
    def check_database(self):
        """Check database connectivity"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def check_cache(self):
        """Check cache connectivity"""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'test', 1)
            return cache.get('health_check') == 'test'
        except Exception:
            return False
    
    def check_storage(self):
        """Check storage accessibility"""
        try:
            from django.core.files.storage import default_storage
            test_content = b'test'
            test_name = f'health_check_{timezone.now().timestamp()}.txt'
            
            # Write test file
            default_storage.save(test_name, ContentFile(test_content))
            
            # Read test file
            if default_storage.exists(test_name):
                with default_storage.open(test_name) as f:
                    content = f.read()
                
                # Delete test file
                default_storage.delete(test_name)
                return content == test_content
            
            return False
        except Exception:
            return False


class MaintenanceModeView(TemplateView):
    """Maintenance mode page"""
    template_name = 'auth/maintenance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context.update({
            'page_title': 'Maintenance Mode',
            'tenant': tenant,
            'maintenance_message': getattr(settings, 'MAINTENANCE_MESSAGE', 'The system is currently undergoing maintenance. Please check back later.'),
            'estimated_downtime': getattr(settings, 'ESTIMATED_DOWNTIME', '30 minutes'),
            'contact_email': getattr(settings, 'CONTACT_EMAIL', 'support@example.com'),
        })
        return context


