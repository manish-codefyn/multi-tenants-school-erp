from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.forms import TenantAwareModelForm
from .models import (
    SecurityPolicy, PasswordPolicy, SessionPolicy, 
    AccessControlPolicy, SecurityIncident
)

class SecurityPolicyForm(TenantAwareModelForm):
    class Meta:
        model = SecurityPolicy
        fields = [
            'name', 'policy_type', 'code', 'description', 
            'policy_document', 'version', 'is_mandatory', 
            'enforcement_level', 'compliance_standard', 
            'requires_acknowledgement', 'effective_date', 
            'expiry_date', 'is_active'
        ]
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'policy_document': forms.Textarea(attrs={'rows': 5}),
        }

class PasswordPolicyForm(TenantAwareModelForm):
    class Meta:
        model = PasswordPolicy
        fields = [
            'name', 'min_length', 'require_uppercase', 'require_lowercase',
            'require_numbers', 'require_special_chars', 'min_special_chars',
            'prevent_reuse', 'password_history_size', 'password_expiry_days',
            'warn_before_expiry', 'max_login_attempts', 'lockout_duration_minutes',
            'require_mfa', 'mfa_methods', 'apply_to_students', 'apply_to_staff',
            'apply_to_admins', 'is_active'
        ]
        widgets = {
            'mfa_methods': forms.Textarea(attrs={'rows': 3, 'placeholder': '["TOTP", "SMS"]'}),
        }
        help_texts = {
            'mfa_methods': _('Enter valid JSON list of MFA methods, e.g., ["TOTP", "SMS"]'),
        }

class SessionPolicyForm(TenantAwareModelForm):
    class Meta:
        model = SessionPolicy
        fields = [
            'name', 'session_timeout_minutes', 'extend_session_on_activity',
            'max_concurrent_sessions', 'prevent_concurrent_logins',
            'require_secure_cookies', 'http_only_cookies', 'same_site_cookies',
            'apply_to_students', 'apply_to_staff', 'apply_to_admins', 'is_active'
        ]

class AccessControlPolicyForm(TenantAwareModelForm):
    class Meta:
        model = AccessControlPolicy
        fields = [
            'name', 'description', 'ip_whitelist', 'ip_blacklist',
            'allowed_access_hours', 'allowed_countries', 'blocked_countries',
            'allowed_user_agents', 'require_secure_connection',
            'apply_to_roles', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'ip_whitelist': forms.Textarea(attrs={'rows': 3, 'placeholder': '["192.168.1.1"]'}),
            'ip_blacklist': forms.Textarea(attrs={'rows': 3, 'placeholder': '["10.0.0.1"]'}),
            'allowed_access_hours': forms.Textarea(attrs={'rows': 3, 'placeholder': '{"start": "09:00", "end": "17:00", "days": [0,1,2,3,4]}'}),
            'allowed_countries': forms.Textarea(attrs={'rows': 2, 'placeholder': '["US", "UK"]'}),
            'blocked_countries': forms.Textarea(attrs={'rows': 2, 'placeholder': '["CN", "RU"]'}),
            'allowed_user_agents': forms.Textarea(attrs={'rows': 2}),
            'apply_to_roles': forms.Textarea(attrs={'rows': 2, 'placeholder': '["admin", "teacher"]'}),
        }
        help_texts = {
            'allowed_access_hours': _('JSON format: {"start": "HH:MM", "end": "HH:MM", "days": [0-6]}'),
        }

class SecurityIncidentForm(TenantAwareModelForm):
    class Meta:
        model = SecurityIncident
        fields = [
            'title', 'incident_type', 'description', 'priority', 'status',
            'detected_at', 'impact_level', 'affected_systems',
            'data_compromised', 'assigned_to', 'notes'
        ]
        widgets = {
            'detected_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'affected_systems': forms.Textarea(attrs={'rows': 3, 'placeholder': '["Server A", "Database B"]'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class SecurityIncidentUpdateForm(TenantAwareModelForm):
    class Meta:
        model = SecurityIncident
        fields = [
            'status', 'priority', 'impact_level', 'assigned_to',
            'root_cause', 'action_taken', 'prevention_measures',
            'contained_at', 'resolved_at', 'notes'
        ]
        widgets = {
            'contained_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'resolved_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'root_cause': forms.Textarea(attrs={'rows': 3}),
            'action_taken': forms.Textarea(attrs={'rows': 3}),
            'prevention_measures': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
