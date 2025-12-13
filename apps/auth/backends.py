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