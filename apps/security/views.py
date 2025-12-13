from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import SecurityPolicy, AuditLog, SecurityIncident

class SecurityDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'security/dashboard.html'
    permission_required = 'security.view_securitypolicy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_policies'] = SecurityPolicy.objects.filter(tenant=tenant, is_active=True).count()
        context['total_incidents'] = SecurityIncident.objects.filter(tenant=tenant).count()
        context['open_incidents'] = SecurityIncident.objects.filter(tenant=tenant, status='OPEN').count()
        context['recent_audits'] = AuditLog.objects.filter(tenant=tenant).count()
        
        return context

# ==================== SECURITY POLICY ====================

class SecurityPolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SecurityPolicy
    template_name = 'security/policy_list.html'
    context_object_name = 'policies'
    permission_required = 'security.view_securitypolicy'

class SecurityPolicyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SecurityPolicy
    fields = ['name', 'policy_type', 'code', 'description', 'policy_document', 
              'version', 'is_mandatory', 'enforcement_level', 'compliance_standard', 
              'requires_acknowledgement', 'effective_date', 'expiry_date', 'is_active']
    template_name = 'security/policy_form.html'
    success_url = reverse_lazy('security:policy_list')
    permission_required = 'security.add_securitypolicy'

    def form_valid(self, form):
        messages.success(self.request, "Security policy created successfully.")
        return super().form_valid(form)

class SecurityPolicyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SecurityPolicy
    fields = ['name', 'policy_type', 'code', 'description', 'policy_document', 
              'version', 'is_mandatory', 'enforcement_level', 'compliance_standard', 
              'requires_acknowledgement', 'effective_date', 'expiry_date', 'is_active']
    template_name = 'security/policy_form.html'
    success_url = reverse_lazy('security:policy_list')
    permission_required = 'security.change_securitypolicy'

    def form_valid(self, form):
        messages.success(self.request, "Security policy updated successfully.")
        return super().form_valid(form)

class SecurityPolicyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SecurityPolicy
    template_name = 'security/confirm_delete.html'
    success_url = reverse_lazy('security:policy_list')
    permission_required = 'security.delete_securitypolicy'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Security policy deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== AUDIT LOG ====================

class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AuditLog
    template_name = 'security/audit_log_list.html'
    context_object_name = 'logs'
    permission_required = 'security.view_auditlog'
    paginate_by = 50

# ==================== SECURITY INCIDENT ====================

class SecurityIncidentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SecurityIncident
    template_name = 'security/incident_list.html'
    context_object_name = 'incidents'
    permission_required = 'security.view_securityincident'

class SecurityIncidentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = SecurityIncident
    template_name = 'security/incident_detail.html'
    context_object_name = 'incident'
    permission_required = 'security.view_securityincident'

class SecurityIncidentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SecurityIncident
    fields = ['title', 'incident_type', 'description', 'priority', 'impact_level', 
              'assigned_to', 'data_compromised']
    template_name = 'security/incident_form.html'
    success_url = reverse_lazy('security:incident_list')
    permission_required = 'security.add_securityincident'

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        messages.success(self.request, "Security incident created successfully.")
        return super().form_valid(form)

class SecurityIncidentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SecurityIncident
    fields = ['title', 'incident_type', 'description', 'priority', 'status', 
              'impact_level', 'assigned_to', 'root_cause', 'action_taken', 
              'prevention_measures']
    template_name = 'security/incident_form.html'
    success_url = reverse_lazy('security:incident_list')
    permission_required = 'security.change_securityincident'

    def form_valid(self, form):
        messages.success(self.request, "Security incident updated successfully.")
        return super().form_valid(form)
