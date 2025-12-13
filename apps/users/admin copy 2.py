# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.db import transaction
import csv
import io
from datetime import datetime

from .models import User
from .forms import (
    TenantAwareUserCreationForm,
    TenantAwareUserChangeForm,
    TenantAwarePasswordChangeForm,
    UserProfileForm,
    BulkUserImportForm,
    UserFilterForm,
    MFAEnableForm,
    MFADisableForm
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model"""
    
    # Use custom forms
    add_form = TenantAwareUserCreationForm
    form = TenantAwareUserChangeForm
    change_password_form = TenantAwarePasswordChangeForm
    
    # Fields to display in list view
    list_display = (
        'get_avatar_display',
        'email', 
        'get_full_name_display',
        'get_tenant_display', 
        'get_role_display_with_color',
        'get_status_display',
        'get_mfa_status',
        'last_login',
    )
    
    list_display_links = ('get_avatar_display', 'email', 'get_full_name_display')
    
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
        'verification_token',
        'mfa_secret',
        'last_login_ip',
        'current_login_ip',
    )
    
    # Custom field display with sections
    fieldsets = (
        (_('Personal Information'), {
            'fields': (
                'avatar',
                'email',
                'password',
                'first_name',
                'last_name',
                'phone_number',
                'date_of_birth',
            ),
            'classes': ('wide',),
        }),
        (_('Organization & Role'), {
            'fields': (
                'tenant',
                'role',
                'student_id',
                'employee_id',
            ),
            'classes': ('wide',),
        }),
        (_('Security'), {
            'fields': (
                'mfa_enabled',
                'mfa_secret',
                'is_verified',
                'verification_token',
                'failed_login_attempts',
                'locked_until',
                'last_login_ip',
                'current_login_ip',
                'password_changed_at',
            ),
            'classes': ('collapse',),
        }),
        (_('Preferences'), {
            'fields': (
                'timezone',
                'language',
            ),
            'classes': ('wide',),
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
            'classes': ('wide',),
        }),
        (_('System Information'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Add form fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'confirm_password',
                'first_name',
                'last_name',
                'tenant',
                'role',
                'is_active',
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
        'export_users_csv',
        'send_welcome_emails',
    ]
    
    # Add custom admin views
    change_list_template = 'admin/users/change_list.html'
    change_form_template = 'admin/users/change_form.html'
    
    def get_changelist(self, request, **kwargs):
        """Add filter form to changelist"""
        from django.contrib.admin.views.main import ChangeList
        class FilteredChangeList(ChangeList):
            def get_filters_params(self, params=None):
                filters = super().get_filters_params(params)
                # Add custom filter form
                self.filter_form = UserFilterForm(data=self.params)
                if self.filter_form.is_valid():
                    filters.update(self.filter_form.cleaned_data)
                return filters
            
            def get_queryset(self, request):
                qs = super().get_queryset(request)
                if hasattr(self, 'filter_form') and self.filter_form.is_valid():
                    qs = self.filter_form.filter_queryset(qs)
                return qs
        
        return FilteredChangeList
    
    def get_urls(self):
        """Add custom URLs"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_users_view), name='users_user_import'),
            path('<path:object_id>/enable-mfa/', self.admin_site.admin_view(self.enable_mfa_view), name='users_user_enable_mfa'),
            path('<path:object_id>/disable-mfa/', self.admin_site.admin_view(self.disable_mfa_view), name='users_user_disable_mfa'),
            path('<path:object_id>/send-verification/', self.admin_site.admin_view(self.send_verification_view), name='users_user_send_verification'),
            path('<path:object_id>/reset-password/', self.admin_site.admin_view(self.reset_password_view), name='users_user_reset_password'),
        ]
        return custom_urls + urls
    
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
            readonly_fields.extend(['is_superuser', 'is_staff', 'groups', 'user_permissions'])
            
        # For existing objects, make some fields readonly
        if obj:
            readonly_fields.extend(['tenant', 'email'])
            
        # Add audit fields
        readonly_fields.extend(['created_by', 'updated_by'])
            
        return tuple(set(readonly_fields))
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on user permissions"""
        form = super().get_form(request, obj, **kwargs)
        
        # Pass request user to form for tenant/role filtering
        form.request_user = request.user
        
        # Limit tenant choices for non-superusers
        if not request.user.is_superuser and 'tenant' in form.base_fields:
            if request.user.tenant:
                form.base_fields['tenant'].queryset = form.base_fields['tenant'].queryset.filter(
                    id=request.user.tenant.id
                )
                form.base_fields['tenant'].initial = request.user.tenant
        
        # For add form, pass request user
        if obj is None and hasattr(form, '__init__'):
            original_init = form.__init__
            
            def new_init(*args, **kwargs):
                kwargs['request_user'] = request.user
                return original_init(*args, **kwargs)
            
            form.__init__ = new_init
        
        return form
    
    # Custom display methods
    def get_avatar_display(self, obj):
        """Display avatar thumbnail"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;">',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 30px; height: 30px; border-radius: 50%; background-color: #ccc; '
            'display: flex; align-items: center; justify-content: center; color: #666; font-weight: bold;">'
            '{}</div>',
            obj.first_name[0] + obj.last_name[0] if obj.first_name and obj.last_name else '?'
        )
    
    get_avatar_display.short_description = ''
    
    def get_full_name_display(self, obj):
        """Display full name with link"""
        url = reverse('admin:users_user_change', args=[obj.id])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.get_full_name() or obj.email
        )
    
    get_full_name_display.short_description = _('Name')
    
    def get_tenant_display(self, obj):
        """Display tenant with link"""
        if obj.tenant:
            url = reverse('admin:tenants_tenant_change', args=[obj.tenant.id])
            return format_html('<a href="{}">{}</a>', url, obj.tenant.name)
        return format_html('<span style="color: #999;">{}</span>', _('System'))
    
    get_tenant_display.short_description = _('Organization')
    
    def get_role_display_with_color(self, obj):
        """Display role with color coding"""
        role_colors = {
            User.ROLE_SUPER_ADMIN: '#dc3545',  # red
            User.ROLE_ADMIN: '#fd7e14',        # orange
            User.ROLE_STAFF: '#0d6efd',        # blue
            User.ROLE_TEACHER: '#198754',      # green
            User.ROLE_STUDENT: '#6c757d',      # gray
        }
        
        color = role_colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 2px 6px; '
            'border-radius: 12px; background-color: {}20;">{}</span>',
            color, color, obj.get_role_display()
        )
    
    get_role_display_with_color.short_description = _('Role')
    
    def get_status_display(self, obj):
        """Display status with icons"""
        status_html = []
        
        if obj.is_active:
            status_html.append(
                '<span style="color: #198754;" title="Active">●</span>'
            )
        else:
            status_html.append(
                '<span style="color: #dc3545;" title="Inactive">●</span>'
            )
        
        if obj.is_verified:
            status_html.append(
                '<span style="color: #0d6efd; margin-left: 5px;" title="Verified">✓</span>'
            )
        
        if obj.is_account_locked:
            status_html.append(
                '<span style="color: #ffc107; margin-left: 5px;" title="Locked">🔒</span>'
            )
        
        return format_html(''.join(status_html))
    
    get_status_display.short_description = _('Status')
    
    def get_mfa_status(self, obj):
        """Display MFA status"""
        if obj.mfa_enabled:
            return format_html(
                '<span style="color: #198754;" title="MFA Enabled">✓ 2FA</span>'
            )
        return format_html(
            '<span style="color: #6c757d;" title="MFA Disabled">—</span>'
        )
    
    get_mfa_status.short_description = _('MFA')
    
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
        count = 0
        for user in queryset:
            if not user.mfa_secret:
                user.generate_mfa_secret()
            user.mfa_enabled = True
            user.save()
            count += 1
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
    
    @admin.action(description=_('Export selected users to CSV'))
    def export_users_csv(self, request, queryset):
        """Export users to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export_{}.csv"'.format(
            datetime.now().strftime('%Y%m%d_%H%M%S')
        )
        
        writer = csv.writer(response)
        writer.writerow([
            'Email', 'First Name', 'Last Name', 'Role', 'Organization',
            'Phone', 'Status', 'Verified', 'MFA Enabled', 'Last Login'
        ])
        
        for user in queryset:
            writer.writerow([
                user.email,
                user.first_name or '',
                user.last_name or '',
                user.get_role_display(),
                user.tenant.name if user.tenant else '',
                user.phone_number or '',
                'Active' if user.is_active else 'Inactive',
                'Yes' if user.is_verified else 'No',
                'Yes' if user.mfa_enabled else 'No',
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else ''
            ])
        
        return response
    
    @admin.action(description=_('Send welcome emails to selected users'))
    def send_welcome_emails(self, request, queryset):
        """Send welcome emails to users"""
        count = 0
        for user in queryset:
            if user.email and user.is_active and not user.is_superuser:
                try:
                    user.send_verification_email()
                    count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        _(f'Failed to send email to {user.email}: {str(e)}'),
                        messages.ERROR
                    )
        
        self.message_user(
            request,
            _(f'Successfully sent welcome emails to {count} user(s).'),
            messages.SUCCESS if count > 0 else messages.WARNING
        )
    
    # Custom admin views
    def import_users_view(self, request):
        """View for bulk importing users"""
        context = {
            **self.admin_site.each_context(request),
            'title': _('Import Users'),
            'opts': self.model._meta,
        }
        
        if request.method == 'POST':
            form = BulkUserImportForm(request.POST, request.FILES, request_user=request.user)
            if form.is_valid():
                try:
                    csv_file = form.cleaned_data['csv_file']
                    tenant = form.cleaned_data['tenant']
                    default_password = form.cleaned_data['default_password']
                    send_welcome_email = form.cleaned_data['send_welcome_email']
                    
                    # Read CSV file
                    decoded_file = csv_file.read().decode('utf-8')
                    io_string = io.StringIO(decoded_file)
                    reader = csv.DictReader(io_string)
                    
                    imported_count = 0
                    errors = []
                    
                    with transaction.atomic():
                        for row_num, row in enumerate(reader, start=2):  # Start from 2 for line numbers
                            try:
                                # Create user
                                user = User.objects.create_user(
                                    email=row.get('email', '').strip().lower(),
                                    first_name=row.get('first_name', '').strip(),
                                    last_name=row.get('last_name', '').strip(),
                                    tenant=tenant,
                                    role=row.get('role', User.ROLE_STUDENT),
                                    phone_number=row.get('phone_number', '').strip(),
                                    is_active=True,
                                )
                                
                                # Set password
                                if default_password:
                                    user.set_password(default_password)
                                else:
                                    # Generate random password
                                    import secrets
                                    import string
                                    alphabet = string.ascii_letters + string.digits
                                    password = ''.join(secrets.choice(alphabet) for i in range(12))
                                    user.set_password(password)
                                    # Store password for email if needed
                                    row['_generated_password'] = password
                                
                                user.save()
                                imported_count += 1
                                
                                # Send welcome email if requested
                                if send_welcome_email:
                                    try:
                                        user.send_verification_email()
                                    except Exception as e:
                                        errors.append(f"Row {row_num}: Failed to send email to {user.email}")
                                
                            except Exception as e:
                                errors.append(f"Row {row_num}: {str(e)}")
                    
                    if imported_count > 0:
                        self.message_user(
                            request,
                            _(f'Successfully imported {imported_count} user(s).'),
                            messages.SUCCESS
                        )
                    
                    if errors:
                        for error in errors:
                            self.message_user(request, error, messages.WARNING)
                    
                    return HttpResponseRedirect(reverse('admin:users_user_changelist'))
                    
                except Exception as e:
                    self.message_user(
                        request,
                        _(f'Error processing CSV file: {str(e)}'),
                        messages.ERROR
                    )
        else:
            form = BulkUserImportForm(request_user=request.user)
        
        context['form'] = form
        return TemplateResponse(request, 'admin/users/import_form.html', context)
    
    def enable_mfa_view(self, request, object_id):
        """View for enabling MFA for a user"""
        user = self.get_object(request, object_id)
        
        if not user:
            self.message_user(request, _('User not found.'), messages.ERROR)
            return HttpResponseRedirect(reverse('admin:users_user_changelist'))
        
        context = {
            **self.admin_site.each_context(request),
            'title': _('Enable MFA'),
            'opts': self.model._meta,
            'user': user,
            'provisioning_uri': user.get_mfa_provisioning_uri() if not user.mfa_enabled else None,
        }
        
        if request.method == 'POST':
            form = MFAEnableForm(request.POST, user=user)
            if form.is_valid():
                user.mfa_enabled = True
                user.save()
                self.message_user(request, _('MFA enabled successfully.'), messages.SUCCESS)
                return HttpResponseRedirect(reverse('admin:users_user_change', args=[object_id]))
        else:
            form = MFAEnableForm(user=user)
        
        context['form'] = form
        return TemplateResponse(request, 'admin/users/enable_mfa.html', context)
    
    def disable_mfa_view(self, request, object_id):
        """View for disabling MFA for a user"""
        user = self.get_object(request, object_id)
        
        if not user:
            self.message_user(request, _('User not found.'), messages.ERROR)
            return HttpResponseRedirect(reverse('admin:users_user_changelist'))
        
        context = {
            **self.admin_site.each_context(request),
            'title': _('Disable MFA'),
            'opts': self.model._meta,
            'user': user,
        }
        
        if request.method == 'POST':
            form = MFADisableForm(request.POST, user=user)
            if form.is_valid():
                user.mfa_enabled = False
                user.save()
                self.message_user(request, _('MFA disabled successfully.'), messages.SUCCESS)
                return HttpResponseRedirect(reverse('admin:users_user_change', args=[object_id]))
        else:
            form = MFADisableForm(user=user)
        
        context['form'] = form
        return TemplateResponse(request, 'admin/users/disable_mfa.html', context)
    
    def send_verification_view(self, request, object_id):
        """View for sending verification email"""
        user = self.get_object(request, object_id)
        
        if not user:
            self.message_user(request, _('User not found.'), messages.ERROR)
            return HttpResponseRedirect(reverse('admin:users_user_changelist'))
        
        try:
            user.send_verification_email()
            self.message_user(request, _('Verification email sent successfully.'), messages.SUCCESS)
        except Exception as e:
            self.message_user(request, _(f'Failed to send verification email: {str(e)}'), messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:users_user_change', args=[object_id]))
    
    def reset_password_view(self, request, object_id):
        """View for resetting user password"""
        from django.contrib.auth.forms import AdminPasswordChangeForm
        
        user = self.get_object(request, object_id)
        
        if not user:
            self.message_user(request, _('User not found.'), messages.ERROR)
            return HttpResponseRedirect(reverse('admin:users_user_changelist'))
        
        context = {
            **self.admin_site.each_context(request),
            'title': _('Reset Password'),
            'opts': self.model._meta,
            'user': user,
        }
        
        if request.method == 'POST':
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                self.message_user(request, _('Password reset successfully.'), messages.SUCCESS)
                return HttpResponseRedirect(reverse('admin:users_user_change', args=[object_id]))
        else:
            form = AdminPasswordChangeForm(user)
        
        context['form'] = form
        return TemplateResponse(request, 'admin/users/reset_password.html', context)
    
    # Override save method
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Set tenant for non-superusers created by non-superusers
        if not obj.is_superuser and not request.user.is_superuser and not obj.tenant:
            obj.tenant = request.user.tenant
        
        super().save_model(request, obj, form, change)
        
        # Send verification email for new non-superuser accounts
        if not change and not obj.is_superuser and obj.email:
            try:
                obj.send_verification_email()
            except Exception as e:
                # Log but don't fail
                pass
    
    # Custom changelist view
    def changelist_view(self, request, extra_context=None):
        """Add custom context to changelist"""
        extra_context = extra_context or {}
        
        # Add stats
        qs = self.get_queryset(request)
        total_users = qs.count()
        active_users = qs.filter(is_active=True).count()
        verified_users = qs.filter(is_verified=True).count()
        mfa_users = qs.filter(mfa_enabled=True).count()
        
        # Add filter form
        filter_form = UserFilterForm(request.GET or None)
        
        extra_context.update({
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'mfa_users': mfa_users,
            'filter_form': filter_form,
            'show_import': request.user.is_superuser or request.user.is_staff,
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    
    # Custom change form view
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Add custom context to change form"""
        extra_context = extra_context or {}
        
        if object_id:
            user = self.get_object(request, object_id)
            if user:
                extra_context.update({
                    'show_mfa_actions': not user.mfa_enabled,
                    'show_verification_action': not user.is_verified and not user.is_superuser,
                })
        
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    # Add custom buttons to change form
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add custom buttons to change form"""
        extra_context = extra_context or {}
        user = self.get_object(request, object_id)
        
        if user:
            extra_context.update({
                'custom_buttons': [
                    {
                        'name': 'enable_mfa',
                        'url': reverse('admin:users_user_enable_mfa', args=[object_id]),
                        'label': _('Enable MFA'),
                        'class': 'button',
                        'condition': not user.mfa_enabled,
                    },
                    {
                        'name': 'disable_mfa',
                        'url': reverse('admin:users_user_disable_mfa', args=[object_id]),
                        'label': _('Disable MFA'),
                        'class': 'button',
                        'condition': user.mfa_enabled,
                    },
                    {
                        'name': 'send_verification',
                        'url': reverse('admin:users_user_send_verification', args=[object_id]),
                        'label': _('Send Verification Email'),
                        'class': 'button',
                        'condition': not user.is_verified and not user.is_superuser,
                    },
                    {
                        'name': 'reset_password',
                        'url': reverse('admin:users_user_reset_password', args=[object_id]),
                        'label': _('Reset Password'),
                        'class': 'button',
                        'condition': True,
                    },
                ]
            })
        
        return super().change_view(request, object_id, form_url, extra_context)