from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from apps.users.models import User
from .models import LoginAttempt, SecurityEvent


class TenantAwareAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend with tenant awareness and security features
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """
        Authenticate user with email and password, considering tenant context
        """
        if email is None or password is None:
            return None

        email = email.lower().strip()
        
        # Get tenant from request or kwargs
        tenant = getattr(request, 'tenant', None) or kwargs.get('tenant')
        if not tenant:
            return None

        # Check if account is locked
        try:
            user = User.objects.get(email=email, tenant=tenant, is_active=True)
            
            if user.is_account_locked:
                self._log_login_attempt(
                    email, request, False, "Account locked", user
                )
                raise PermissionDenied("Account is temporarily locked due to multiple failed login attempts.")
                
        except User.DoesNotExist:
            self._log_login_attempt(email, request, False, "User not found")
            return None

        # Verify password
        if user.check_password(password):
            # Check if password is expired
            if self._is_password_expired(user):
                self._log_login_attempt(
                    email, request, False, "Password expired", user
                )
                raise PermissionDenied("Password has expired. Please reset your password.")

            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_ip = user.current_login_ip
            user.current_login_ip = self._get_client_ip(request)
            user.last_login = timezone.now()
            user.save(update_fields=[
                'failed_login_attempts', 'locked_until', 'last_login_ip',
                'current_login_ip', 'last_login'
            ])

            # Log successful login
            self._log_login_attempt(email, request, True, "", user)
            self._log_security_event(
                user, 'login_success', 'low',
                f"Successful login from {self._get_client_ip(request)}"
            )

            return user
        else:
            # Handle failed login attempt
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            max_attempts = user.tenant.configuration.max_login_attempts
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                self._log_security_event(
                    user, 'user_locked', 'high',
                    f"Account locked after {max_attempts} failed login attempts"
                )
            
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
            
            self._log_login_attempt(
                email, request, False, "Invalid password", user
            )
            self._log_security_event(
                user, 'login_failed', 'medium',
                f"Failed login attempt {user.failed_login_attempts}/{max_attempts}"
            )
            
            return None

    def _is_password_expired(self, user):
        """Check if user's password has expired"""
        password_expiry_days = user.tenant.configuration.password_expiry_days
        expiry_date = user.password_changed_at + timezone.timedelta(days=password_expiry_days)
        return timezone.now() > expiry_date

    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _log_login_attempt(self, email, request, success, failure_reason="", user=None):
        """Log login attempt for security monitoring"""
        LoginAttempt.objects.create(
            user=user,
            email=email,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=success,
            failure_reason=failure_reason,
            tenant=user.tenant if user else None
        )

    def _log_security_event(self, user, event_type, severity, description):
        """Log security event"""
        SecurityEvent.objects.create(
            user=user,
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=user.current_login_ip,
            tenant=user.tenant
        )

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None

    def get_all_permissions(self, user_obj, obj=None):
        """
        Get all permissions for the user, including role-based permissions
        from apps.auth.models.RolePermission
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        if not hasattr(user_obj, '_perm_cache'):
            # Start with standard permissions (if any mixed in)
            perms = super().get_all_permissions(user_obj, obj)
            
            # Add role-based permissions
            try:
                # Use get_model to avoid circular imports
                from django.apps import apps
                RolePermission = apps.get_model('apps_auth', 'RolePermission')
                
                # Fetch query set values to minimize DB overhead
                # We use string matching for role because user_obj.role is a string
                role_perms = RolePermission.objects.filter(
                    role=user_obj.role,
                    tenant=user_obj.tenant
                ).values_list('permission__content_type__app_label', 'permission__codename')
                
                # Format as "app_label.codename"
                for app_label, codename in role_perms:
                    perms.add(f"{app_label}.{codename}")
                    
            except Exception as e:
                # Log error
                print(f"DEBUG: Error fetching role permissions: {e}")
                pass
            
            user_obj._perm_cache = perms
            
        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has specific permission
        """
        if not user_obj.is_active:
            return False
        
        # Superusers get all permissions
        if user_obj.is_superuser:
            return True
            
        return perm in self.get_all_permissions(user_obj, obj)