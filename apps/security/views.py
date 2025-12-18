from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.core.views import (
    BaseListView, BaseCreateView, BaseUpdateView, 
    BaseDeleteView, BaseTemplateView, BaseDetailView
)
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import (
    SecurityPolicy, PasswordPolicy, SessionPolicy, 
    AccessControlPolicy, SecurityIncident, AuditLog
)
from .forms import (
    SecurityPolicyForm, PasswordPolicyForm, SessionPolicyForm,
    AccessControlPolicyForm, SecurityIncidentForm, SecurityIncidentUpdateForm
)

# ==================== DASHBOARD ====================

class SecurityDashboardView(BaseTemplateView):
    template_name = 'security/dashboard.html'
    permission_required = 'security.view_securitypolicy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.tenant
        
        context['password_policy_count'] = PasswordPolicy.objects.filter(tenant=tenant).count()
        context['session_policy_count'] = SessionPolicy.objects.filter(tenant=tenant).count()
        context['access_policy_count'] = AccessControlPolicy.objects.filter(tenant=tenant).count()
        context['open_incidents_count'] = SecurityIncident.objects.filter(tenant=tenant, status='OPEN').count()
        context['recent_audits'] = AuditLog.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        
        return context

# ==================== PASSWORD POLICY ====================

class PasswordPolicyListView(BaseListView):
    model = PasswordPolicy
    template_name = 'security/password_policy/list.html'
    permission_required = 'security.view_passwordpolicy'
    search_fields = ['name']

class PasswordPolicyCreateView(BaseCreateView):
    model = PasswordPolicy
    form_class = PasswordPolicyForm
    template_name = 'security/password_policy/form.html'
    permission_required = 'security.add_passwordpolicy'
    success_url = reverse_lazy('security:password_policy_list')
    success_message = _("Password policy created successfully.")

class PasswordPolicyUpdateView(BaseUpdateView):
    model = PasswordPolicy
    form_class = PasswordPolicyForm
    template_name = 'security/password_policy/form.html'
    permission_required = 'security.change_passwordpolicy'
    success_url = reverse_lazy('security:password_policy_list')
    success_message = _("Password policy updated successfully.")

class PasswordPolicyDeleteView(BaseDeleteView):
    model = PasswordPolicy
    template_name = 'security/password_policy/confirm_delete.html'
    permission_required = 'security.delete_passwordpolicy'
    success_url = reverse_lazy('security:password_policy_list')
    success_message = _("Password policy deleted successfully.")

# ==================== SESSION POLICY ====================

class SessionPolicyListView(BaseListView):
    model = SessionPolicy
    template_name = 'security/session_policy/list.html'
    permission_required = 'security.view_sessionpolicy'
    search_fields = ['name']

class SessionPolicyCreateView(BaseCreateView):
    model = SessionPolicy
    form_class = SessionPolicyForm
    template_name = 'security/session_policy/form.html'
    permission_required = 'security.add_sessionpolicy'
    success_url = reverse_lazy('security:session_policy_list')
    success_message = _("Session policy created successfully.")

class SessionPolicyUpdateView(BaseUpdateView):
    model = SessionPolicy
    form_class = SessionPolicyForm
    template_name = 'security/session_policy/form.html'
    permission_required = 'security.change_sessionpolicy'
    success_url = reverse_lazy('security:session_policy_list')
    success_message = _("Session policy updated successfully.")

class SessionPolicyDeleteView(BaseDeleteView):
    model = SessionPolicy
    template_name = 'security/session_policy/confirm_delete.html'
    permission_required = 'security.delete_sessionpolicy'
    success_url = reverse_lazy('security:session_policy_list')
    success_message = _("Session policy deleted successfully.")

# ==================== ACCESS CONTROL POLICY ====================

class AccessControlPolicyListView(BaseListView):
    model = AccessControlPolicy
    template_name = 'security/access_control/list.html'
    permission_required = 'security.view_accesscontrolpolicy'
    search_fields = ['name']

class AccessControlPolicyCreateView(BaseCreateView):
    model = AccessControlPolicy
    form_class = AccessControlPolicyForm
    template_name = 'security/access_control/form.html'
    permission_required = 'security.add_accesscontrolpolicy'
    success_url = reverse_lazy('security:access_control_list')
    success_message = _("Access control policy created successfully.")

class AccessControlPolicyUpdateView(BaseUpdateView):
    model = AccessControlPolicy
    form_class = AccessControlPolicyForm
    template_name = 'security/access_control/form.html'
    permission_required = 'security.change_accesscontrolpolicy'
    success_url = reverse_lazy('security:access_control_list')
    success_message = _("Access control policy updated successfully.")

class AccessControlPolicyDeleteView(BaseDeleteView):
    model = AccessControlPolicy
    template_name = 'security/access_control/confirm_delete.html'
    permission_required = 'security.delete_accesscontrolpolicy'
    success_url = reverse_lazy('security:access_control_list')
    success_message = _("Access control policy deleted successfully.")

# ==================== SECURITY INCIDENTS ====================

class SecurityIncidentListView(BaseListView):
    model = SecurityIncident
    template_name = 'security/incident/list.html'
    permission_required = 'security.view_securityincident'
    search_fields = ['title', 'incident_id']
    ordering = ['-detected_at']

class SecurityIncidentCreateView(BaseCreateView):
    model = SecurityIncident
    form_class = SecurityIncidentForm
    template_name = 'security/incident/form.html'
    permission_required = 'security.add_securityincident'
    success_url = reverse_lazy('security:incident_list')
    success_message = _("Security incident reported successfully.")

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        return super().form_valid(form)

class SecurityIncidentUpdateView(BaseUpdateView):
    model = SecurityIncident
    form_class = SecurityIncidentUpdateForm
    template_name = 'security/incident/form.html'
    permission_required = 'security.change_securityincident'
    success_url = reverse_lazy('security:incident_list')
    success_message = _("Security incident updated successfully.")

class SecurityIncidentDetailView(BaseDetailView):
    model = SecurityIncident
    template_name = 'security/incident/detail.html'
    permission_required = 'security.view_securityincident'

# ==================== AUDIT LOGS ====================

class AuditLogListView(BaseListView):
    model = AuditLog
    template_name = 'security/audit_log/list.html'
    permission_required = 'security.view_auditlog'
    search_fields = ['user__username', 'description', 'ip_address']
    ordering = ['-created_at']
    paginate_by = 50
