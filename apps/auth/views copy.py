from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import RedirectView, TemplateView, UpdateView
from django.contrib import messages
from apps.core.utils.tenant import get_current_tenant
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        # Access logo through TenantConfiguration relationship
        if tenant and hasattr(tenant, 'configuration') and tenant.configuration.logo:
            context['tenant_logo'] = tenant.configuration.logo.url
        else:
            context['tenant_logo'] = '/static/images/logo.png'
            
        return context

    def get_success_url(self):
        return reverse_lazy('dashboard')

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


def dashboard_redirect(request):
    """
    Redirect user to the appropriate dashboard based on their role.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # Super users - Django admin
    if user.is_superuser:
        return redirect('/admin/')
    
    # Super admins - Custom admin dashboard with full access
    elif user.role == 'super_admin':
        return redirect('admin_panel:super_dashboard')
    
    # Regular admins - Custom admin dashboard with limited access
    elif user.role == 'admin':
        return redirect('admin_panel:dashboard')
    
    elif user.role == 'student':
        return redirect('students:dashboard')
    
    elif user.role == 'teacher':
        return redirect('academics:teacher-dashboard') 
    
    elif user.role == 'staff':
        return redirect('hr:staff-dashboard')
    
    else:
        # Default fallback with warning
        messages.warning(request, 'Your role is not properly configured.')
        return redirect('home')

        
# Additional dashboard views for different user roles
class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/student_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/teacher_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'teacher':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class StaffDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/staff_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'staff':
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or (not request.user.is_superuser and request.user.role not in ['super_admin', 'admin']):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'auth/password_change.html'
    success_url = reverse_lazy('password_change_done')
    
    def form_valid(self, form):
        messages.success(self.request, "Your password was successfully updated!")
        return super().form_valid(form)


class CustomPasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = 'auth/password_change_done.html'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'auth/profile.html'
    fields = ['first_name', 'last_name', 'phone_number', 'avatar', 'language', 'timezone']
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'profile'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)