# apps/users/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import User
from .forms import (
    TenantAwareUserCreationForm, 
    TenantAwareUserChangeForm,
    TenantAwarePasswordChangeForm,
    TenantAwarePasswordChangeForm,
    UserProfileForm  # Make sure this is imported
)
from django.core.exceptions import ValidationError

class UserDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    permission_required = 'users.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_users'] = User.objects.filter(tenant=tenant).count()
        context['active_users'] = User.objects.filter(tenant=tenant, is_active=True).count()
        context['verified_users'] = User.objects.filter(tenant=tenant, is_verified=True).count()
        context['staff_users'] = User.objects.filter(tenant=tenant, is_staff=True).count()
        
        return context

# ==================== USER CRUD ====================

class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    permission_required = 'users.view_user'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        queryset = queryset.filter(tenant=tenant)
        
        # Apply search if provided
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        # Apply filters
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        is_active = self.request.GET.get('is_active')
        if is_active == 'active':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('is_active', '')
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    permission_required = 'users.view_user'

class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = TenantAwareUserCreationForm  # Use your custom form
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    permission_required = 'users.add_user'

    def get_form_kwargs(self):
        """Pass request user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User {form.instance.email} created successfully.")
        return response

class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = TenantAwareUserChangeForm  # Use your custom form
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')
    permission_required = 'users.change_user'

    def get_form_kwargs(self):
        """Pass request user to form"""
        kwargs = super().get_form_kwargs()
        kwargs['request_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User {form.instance.email} updated successfully.")
        return response

class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    permission_required = 'users.delete_user'

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(self.request, f"User {user.email} deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== PROFILE MANAGEMENT ====================

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.request.user
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm  # Use your custom profile form
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'users/change_password.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TenantAwarePasswordChangeForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = TenantAwarePasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed successfully. Please login again.")
            return redirect('login')
        else:
            return self.render_to_response({'form': form})

# ==================== ADMIN ACTIONS ====================

class ToggleUserStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Toggle user active status via AJAX"""
    permission_required = 'users.change_user'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
        user.is_active = not user.is_active
        user.save()
        
        action = "activated" if user.is_active else "deactivated"
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f"User {action} successfully."
        })

class ToggleUserVerificationView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Toggle user verification status via AJAX"""
    permission_required = 'users.change_user'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
        user.is_verified = not user.is_verified
        user.save()
        
        action = "verified" if user.is_verified else "unverified"
        return JsonResponse({
            'success': True,
            'is_verified': user.is_verified,
            'message': f"User {action} successfully."
        })

class ResetUserPasswordView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Reset user password to default"""
    permission_required = 'users.change_user'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
        import secrets
        import string
        
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        user.set_password(new_password)
        user.save()
        
        # In a real application, you would send this password securely
        # For demo purposes, we return it
        return JsonResponse({
            'success': True,
            'message': f"Password reset successfully.",
            'new_password': new_password  # Remove this in production!
        })

class ChangeUserRoleView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Change user role via AJAX"""
    permission_required = 'users.change_user'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
        new_role = request.POST.get('role')
        
        if new_role not in dict(User.ROLE_CHOICES):
            return JsonResponse({'success': False, 'message': 'Invalid role selected'}, status=400)
            
        try:
            user.role = new_role
            user.save()
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': f"Validation Error: {e}"}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error updating role: {str(e)}"}, status=500)
        
        return JsonResponse({
            'success': True,
            'message': f"Role updated to {user.get_role_display()}."
        })


class ToggleStaffView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Toggle user staff status via AJAX"""
    permission_required = 'users.change_user'

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
        action = "granted staff privileges" if not user.is_staff else "revoked staff privileges"
        
        try:
            user.is_staff = not user.is_staff
            user.save()
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': f"Validation Error: {e}"}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error: {str(e)}"}, status=500)

        return JsonResponse({
            'success': True,
            'is_staff': user.is_staff,
            'message': f"User {action}."
        })