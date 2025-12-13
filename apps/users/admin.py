# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model"""
    
    # Fields to display in list view
    list_display = (
        'email', 
        'first_name', 
        'last_name', 
        'tenant', 
        'role',
        'is_active',
        'is_verified',
        'is_staff',
        'last_login',
    )
    
    # Fields for filtering
    list_filter = (
        'is_active',
        'is_verified',
        'is_staff',
        'is_superuser',
        'role',
        'tenant',
        'created_at',
    )
    
    # Fields for searching
    search_fields = (
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'student_id',
        'employee_id',
    )
    
    # Ordering
    ordering = ('-created_at', 'email')
    
    # Readonly fields
    readonly_fields = (
        'last_login',
        'date_joined',
        'created_at',
        'updated_at',
        'password_changed_at',
        'locked_until',
        'failed_login_attempts',
    )
    
    # Custom field display
    fieldsets = (
        (_('Personal Info'), {
            'fields': (
                'email',
                'password',
                'first_name',
                'last_name',
                'phone_number',
                'date_of_birth',
                'avatar',
            )
        }),
        (_('Tenant & Role'), {
            'fields': (
                'tenant',
                'role',
                'student_id',
                'employee_id',
            )
        }),
        (_('Security'), {
            'fields': (
                'mfa_enabled',
                'last_login_ip',
                'current_login_ip',
                'failed_login_attempts',
                'locked_until',
                'password_changed_at',
                'is_verified',
                # 'verification_token',
            )
        }),
        (_('Preferences'), {
            'fields': (
                'timezone',
                'language',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important Dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    # Add form fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'tenant',
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )
    
    # Custom list view actions
    actions = [
        'activate_users',
        'deactivate_users',
        'verify_users',
        'enable_mfa',
        'disable_mfa',
        'reset_login_attempts',
        'unlock_accounts',
    ]
    
    def get_queryset(self, request):
        """Customize queryset based on user permissions"""
        qs = super().get_queryset(request)
        
        # Superusers can see all users
        if request.user.is_superuser:
            return qs
        
        # Staff users can only see users from their tenant
        if request.user.is_staff and request.user.tenant:
            return qs.filter(tenant=request.user.tenant)
        
        return qs
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on permissions"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        
        # Prevent non-superusers from making themselves superusers
        if not request.user.is_superuser:
            readonly_fields.extend(['is_superuser', 'is_staff'])
            
        # For existing objects, make some fields readonly
        if obj:
            readonly_fields.append('tenant')
            
        return tuple(set(readonly_fields))
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on user permissions"""
        form = super().get_form(request, obj, **kwargs)
        
        # Auto-detect tenant from context
        from apps.core.utils.tenant import get_current_tenant
        current_tenant = get_current_tenant()

        # If we are in a specific tenant context (not public), force that tenant
        if current_tenant and current_tenant.schema_name != 'public':
             if 'tenant' in form.base_fields:
                form.base_fields['tenant'].initial = current_tenant
                form.base_fields['tenant'].queryset = form.base_fields['tenant'].queryset.filter(id=current_tenant.id)
        
        # Limit tenant choices for non-superusers (fallback if no context or public)
        elif not request.user.is_superuser and 'tenant' in form.base_fields:
            if request.user.tenant:
                form.base_fields['tenant'].queryset = form.base_fields['tenant'].queryset.filter(
                    id=request.user.tenant.id
                )
                form.base_fields['tenant'].initial = request.user.tenant
        
        return form
    
    # Custom display methods
    def get_tenant_display(self, obj):
        """Display tenant with link"""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return "-"
    
    get_tenant_display.short_description = _('Tenant')
    
    # Custom columns
    def get_role_display_with_color(self, obj):
        """Display role with color coding"""
        role_colors = {
            User.ROLE_SUPER_ADMIN: 'red',
            User.ROLE_ADMIN: 'orange',
            User.ROLE_STAFF: 'blue',
            User.ROLE_TEACHER: 'green',
            User.ROLE_STUDENT: 'gray',
        }
        
        color = role_colors.get(obj.role, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    
    get_role_display_with_color.short_description = _('Role')
    
    # Custom actions
    @admin.action(description=_('Activate selected users'))
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f'Successfully activated {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Deactivate selected users'))
    def deactivate_users(self, request, queryset):
        # Prevent deactivating yourself
        filtered_queryset = queryset.exclude(id=request.user.id)
        count = filtered_queryset.update(is_active=False)
        self.message_user(
            request,
            _(f'Successfully deactivated {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Verify selected users'))
    def verify_users(self, request, queryset):
        count = queryset.update(is_verified=True, verification_token='')
        self.message_user(
            request,
            _(f'Successfully verified {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Enable MFA for selected users'))
    def enable_mfa(self, request, queryset):
        count = queryset.update(mfa_enabled=True)
        self.message_user(
            request,
            _(f'Successfully enabled MFA for {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Disable MFA for selected users'))
    def disable_mfa(self, request, queryset):
        count = queryset.update(mfa_enabled=False)
        self.message_user(
            request,
            _(f'Successfully disabled MFA for {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Reset login attempts for selected users'))
    def reset_login_attempts(self, request, queryset):
        count = queryset.update(
            failed_login_attempts=0,
            locked_until=None
        )
        self.message_user(
            request,
            _(f'Successfully reset login attempts for {count} user(s).'),
            messages.SUCCESS
        )
    
    @admin.action(description=_('Unlock selected accounts'))
    def unlock_accounts(self, request, queryset):
        count = queryset.update(
            failed_login_attempts=0,
            locked_until=None
        )
        self.message_user(
            request,
            _(f'Successfully unlocked {count} account(s).'),
            messages.SUCCESS
        )
    
    # Override save method
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom changelist view
    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist"""
        extra_context = extra_context or {}
        
        # Add stats
        total_users = self.get_queryset(request).count()
        active_users = self.get_queryset(request).filter(is_active=True).count()
        verified_users = self.get_queryset(request).filter(is_verified=True).count()
        
        extra_context.update({
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
        })
        
        return super().changelist_view(request, extra_context=extra_context)