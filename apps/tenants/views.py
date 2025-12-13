from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from .models import Tenant, Domain, TenantConfiguration

class TenantDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'tenants/dashboard.html'
    permission_required = 'tenants.view_tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_tenants'] = Tenant.objects.count()
        context['active_tenants'] = Tenant.objects.filter(status='active', is_active=True).count()
        context['trial_tenants'] = Tenant.objects.filter(status='trial').count()
        context['suspended_tenants'] = Tenant.objects.filter(status='suspended').count()
        
        return context

# ==================== TENANT ====================

class TenantListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tenant
    template_name = 'tenants/tenant_list.html'
    context_object_name = 'tenants'
    permission_required = 'tenants.view_tenant'

class TenantDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Tenant
    template_name = 'tenants/tenant_detail.html'
    context_object_name = 'tenant'
    permission_required = 'tenants.view_tenant'

class TenantCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Tenant
    fields = ['name', 'display_name', 'schema_name', 'status', 'plan', 'max_users', 
              'max_storage_mb', 'contact_email', 'contact_phone', 'is_active']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:tenant_list')
    permission_required = 'tenants.add_tenant'

    def form_valid(self, form):
        messages.success(self.request, "Tenant created successfully.")
        return super().form_valid(form)

class TenantUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Tenant
    fields = ['name', 'display_name', 'status', 'plan', 'max_users', 
              'max_storage_mb', 'contact_email', 'contact_phone', 'is_active']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:tenant_list')
    permission_required = 'tenants.change_tenant'

    def form_valid(self, form):
        messages.success(self.request, "Tenant updated successfully.")
        return super().form_valid(form)

class TenantDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Tenant
    template_name = 'tenants/confirm_delete.html'
    success_url = reverse_lazy('tenants:tenant_list')
    permission_required = 'tenants.delete_tenant'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Tenant deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== DOMAIN ====================

class DomainListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Domain
    template_name = 'tenants/domain_list.html'
    context_object_name = 'domains'
    permission_required = 'tenants.view_domain'

class DomainCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Domain
    fields = ['tenant', 'domain', 'is_primary', 'ssl_enabled']
    template_name = 'tenants/domain_form.html'
    success_url = reverse_lazy('tenants:domain_list')
    permission_required = 'tenants.add_domain'

    def form_valid(self, form):
        messages.success(self.request, "Domain created successfully.")
        return super().form_valid(form)

class DomainUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Domain
    fields = ['tenant', 'domain', 'is_primary', 'ssl_enabled', 'is_verified']
    template_name = 'tenants/domain_form.html'
    success_url = reverse_lazy('tenants:domain_list')
    permission_required = 'tenants.change_domain'

    def form_valid(self, form):
        messages.success(self.request, "Domain updated successfully.")
        return super().form_valid(form)

class DomainDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Domain
    template_name = 'tenants/confirm_delete.html'
    success_url = reverse_lazy('tenants:domain_list')
    permission_required = 'tenants.delete_domain'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Domain deleted successfully.")
        return super().delete(request, *args, **kwargs)
