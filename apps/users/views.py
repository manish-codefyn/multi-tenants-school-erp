import logging
logger = logging.getLogger(__name__)
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from apps.core.services.audit_service import AuditService
from apps.core.views import (BaseTemplateView, BaseListView, BaseCreateView, 
BaseUpdateView, BaseDeleteView,BaseDetailView,BaseFormView,BaseView)
from .models import User
from .forms import (
    TenantAwareUserCreationForm, 
    TenantAwareUserChangeForm,
    TenantAwarePasswordChangeForm,
    UserProfileForm
)
from django.core.exceptions import ValidationError
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant 


class UserDashboardView(BaseTemplateView):
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

class UserListView(BaseListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    permission_required = 'users.view_user'
    paginate_by = 20
    search_fields = ['email', 'first_name', 'last_name', 'phone_number', 'student_id', 'employee_id']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        
        # Apply role filter
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        # Apply status filter
        is_active = self.request.GET.get('is_active')
        if is_active == 'active':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply verification filter
        is_verified = self.request.GET.get('is_verified')
        if is_verified == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif is_verified == 'unverified':
            queryset = queryset.filter(is_verified=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('q', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('is_active', '')
        context['verification_filter'] = self.request.GET.get('is_verified', '')
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserDetailView(BaseDetailView):
    model = User
    template_name = 'users/user_detail.html'
    context_object_name = 'user_obj'
    permission_required = 'users.view_user'

class UserCreateView(BaseCreateView):
    model = User
    form_class = TenantAwareUserCreationForm
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
        
        # Optionally send verification email
        if not form.instance.is_verified and not form.instance.is_superuser:
            try:
                form.instance.send_verification_email()
                messages.info(self.request, f"Verification email sent to {form.instance.email}.")
            except Exception as e:
                logger.warning(f"Failed to send verification email: {e}")
        
        return response

class UserUpdateView(BaseUpdateView):
    model = User
    form_class = TenantAwareUserChangeForm
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

class UserDeleteView(BaseDeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')
    permission_required = 'users.delete_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.object
        return context
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(self.request, f"User {user.email} deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== PROFILE MANAGEMENT ====================

class ProfileView(BaseTemplateView):
    template_name = 'users/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.request.user
        return context

class ProfileUpdateView(BaseUpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Don't require tenant for profile updates
        if 'tenant' in kwargs:
            del kwargs['tenant']
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

class ChangePasswordView(BaseFormView):
    template_name = 'users/change_password.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TenantAwarePasswordChangeForm(user=self.request.user)
        return context
    
    def post(self, request, *args, **kwargs):
        form = TenantAwarePasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            
            # Update user's password changed timestamp
            request.user.password_changed_at = timezone.now()
            request.user.save(update_fields=['password_changed_at'])
            
            # Log the user out and redirect to login
            from django.contrib.auth import logout
            logout(request)
            
            messages.success(request, "Password changed successfully. Please login with your new password.")
            return redirect('login')
        else:
            return self.render_to_response({'form': form})

# ==================== ADMIN ACTIONS ====================

class ToggleUserStatusView(BaseView):
    """Toggle user active status via AJAX"""
    permission_required = 'users.change_user'
    audit_action = 'UPDATE'
    
    @method_decorator(csrf_protect)
    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
            
        try:
            with transaction.atomic():
                user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
                user.is_active = not user.is_active
                user.save(update_fields=['is_active', 'updated_at'])
                
                action = "activated" if user.is_active else "deactivated"
                
                # Audit the action
                if self.audit_enabled:
                    self.audit_service.create_audit_entry(
                        action='USER_STATUS_TOGGLE',
                        resource_type='User',
                        user=request.user,
                        request=request,
                        instance=user,
                        severity='INFO',
                        extra_data={
                            'new_status': user.is_active,
                            'old_status': not user.is_active
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'is_active': user.is_active,
                    'message': f"User {action} successfully."
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            }, status=500)

class ToggleUserVerificationView(BaseView):
    """Toggle user verification status via AJAX"""
    permission_required = 'users.change_user'
    audit_action = 'UPDATE'
    
    @method_decorator(csrf_protect)
    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
            
        try:
            with transaction.atomic():
                user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
                user.is_verified = not user.is_verified
                user.save(update_fields=['is_verified', 'updated_at'])
                
                action = "verified" if user.is_verified else "unverified"
                
                # Audit the action
                if self.audit_enabled:
                    AuditService.create_audit_entry(
                        action='USER_VERIFICATION_TOGGLE',
                        resource_type='User',
                        user=request.user,
                        request=request,
                        instance=user,
                        severity='INFO',
                        extra_data={
                            'new_verified': user.is_verified,
                            'old_verified': not user.is_verified
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'is_verified': user.is_verified,
                    'message': f"User {action} successfully."
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            }, status=500)

class ResetUserPasswordView(BaseView):
    """Reset user password to default"""
    permission_required = 'users.change_user'
    
    @method_decorator(csrf_protect)
    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
            
        try:
            with transaction.atomic():
                user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
                import secrets
                import string
                
                # Generate a secure random password
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
                
                user.set_password(new_password)
                user.password_changed_at = timezone.now()
                user.save(update_fields=['password', 'password_changed_at', 'updated_at'])
                
                # TODO: In production, send password via email instead
                # For now, we'll return it but you should remove this
                
                return JsonResponse({
                    'success': True,
                    'message': f"Password reset successfully.",
                    'new_password': new_password  # Remove this in production and use email!
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            }, status=500)

class ChangeUserRoleView(BaseView):
    """Change user role via AJAX"""
    permission_required = 'users.change_user'
    audit_action = 'UPDATE'
    
    @method_decorator(csrf_protect)
    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
            
        try:
            with transaction.atomic():
                user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
                new_role = request.POST.get('role')
                
                if new_role not in dict(User.ROLE_CHOICES):
                    return JsonResponse({'success': False, 'message': 'Invalid role selected'}, status=400)
                
                # Check if current user can assign this role
                current_user = request.user
                if not current_user.is_superuser:
                    current_user_role_level = User.ROLE_HIERARCHY.get(current_user.role, 0)
                    new_role_level = User.ROLE_HIERARCHY.get(new_role, 0)
                    
                    # Users can only assign roles at or below their own level
                    if new_role_level > current_user_role_level:
                        return JsonResponse({
                            'success': False, 
                            'message': 'You cannot assign a role higher than your own.'
                        }, status=403)
                
                old_role = user.role
                user.role = new_role
                user.save(update_fields=['role', 'updated_at'])
                
                # Audit the role change
                if self.audit_enabled:
                    AuditService.create_audit_entry(
                        action='USER_ROLE_CHANGE',
                        resource_type='User',
                        user=request.user,
                        request=request,
                        instance=user,
                        severity='INFO',
                        extra_data={
                            'old_role': old_role,
                            'new_role': new_role
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': f"Role updated to {user.get_role_display()}.",
                    'role_display': user.get_role_display(),
                    'role': user.role
                })
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': f"Validation Error: {e}"}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Error updating role: {str(e)}"}, status=500)

class ToggleStaffView(BaseView):
    """Toggle user staff status via AJAX"""
    permission_required = 'users.change_user'
    audit_action = 'UPDATE'
    
    @method_decorator(csrf_protect)
    def post(self, request, pk):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
            
        try:
            with transaction.atomic():
                user = get_object_or_404(User, pk=pk, tenant=get_current_tenant())
                
                # Prevent self-demotion if needed
                if user == request.user and user.is_staff:
                    return JsonResponse({
                        'success': False, 
                        'message': 'You cannot remove your own staff privileges'
                    }, status=400)
                
                old_status = user.is_staff
                user.is_staff = not user.is_staff
                user.save(update_fields=['is_staff', 'updated_at'])
                
                action = "granted staff privileges" if user.is_staff else "revoked staff privileges"
                
                # Audit the action
                if self.audit_enabled:
                    AuditService.create_audit_entry(
                        action='USER_STAFF_TOGGLE',
                        resource_type='User',
                        user=request.user,
                        request=request,
                        instance=user,
                        severity='INFO',
                        extra_data={
                            'old_staff': old_status,
                            'new_staff': user.is_staff
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'is_staff': user.is_staff,
                    'message': f"User {action}."
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            }, status=500)

# ==================== BULK USER OPERATIONS ====================

class BulkUserActionView(BaseView):
    """Handle bulk user operations"""
    permission_required = 'users.change_user'
    
    @method_decorator(csrf_protect)
    def post(self, request):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
        
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids[]')
        
        if not action or not user_ids:
            return JsonResponse({
                'success': False, 
                'message': 'Action and user selection required'
            }, status=400)
        
        try:
            with transaction.atomic():
                tenant = get_current_tenant()
                users = User.objects.filter(id__in=user_ids, tenant=tenant)
                
                if action == 'activate':
                    users.update(is_active=True)
                    message = f"{users.count()} users activated successfully."
                elif action == 'deactivate':
                    users.update(is_active=False)
                    message = f"{users.count()} users deactivated successfully."
                elif action == 'verify':
                    users.update(is_verified=True)
                    message = f"{users.count()} users verified successfully."
                elif action == 'send_welcome':
                    # Send welcome emails
                    count = 0
                    for user in users:
                        try:
                            user.send_verification_email()
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to send email to {user.email}: {e}")
                    message = f"Welcome emails sent to {count} users."
                else:
                    return JsonResponse({
                        'success': False, 
                        'message': 'Invalid action'
                    }, status=400)
                
                # Audit bulk action
                if self.audit_enabled:
                    self.audit_service.create_audit_entry(
                        action=f'BULK_USER_{action.upper()}',
                        resource_type='User',
                        user=request.user,
                        request=request,
                        severity='INFO',
                        extra_data={
                            'action': action,
                            'user_count': users.count(),
                            'user_ids': user_ids
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'count': users.count()
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Error: {str(e)}"
            }, status=500)