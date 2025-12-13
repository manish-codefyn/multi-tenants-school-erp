from apps.core.permissions.mixins import (
    PermissionRequiredMixin, RoleRequiredMixin, TenantAccessMixin
)
from django.views.generic import ListView, DetailView

# Example 1: Require specific permission
class FinanceReportView(PermissionRequiredMixin, ListView):
    permission_required = 'finance.view_financial_report'
    template_name = 'finance/reports.html'
    
    def get_queryset(self):
        # Only show reports for user's tenant
        return FinancialReport.objects.filter(tenant=self.request.user.tenant)

# Example 2: Require specific role
class PrincipalDashboardView(RoleRequiredMixin, TemplateView):
    roles_required = ['principal', 'headmaster', 'super_admin']
    template_name = 'dashboard/principal.html'

# Example 3: Combined role and permission
class ManageStaffView(RoleBasedViewMixin, ListView):
    roles_required = ['principal', 'headmaster', 'admin']
    permission_required = 'staff.view_staff'
    template_name = 'staff/manage.html'

# Example 4: Tenant-restricted view
class TenantDataView(TenantAccessMixin, ListView):
    model = Student
    template_name = 'students/list.html'

    {% if 'finance.view_financial_report' in user_permissions %}
    <a href="{% url 'finance-reports' %}">View Financial Reports</a>
{% endif %}

{% if user_role == 'principal' or user_role == 'headmaster' %}
    <a href="{% url 'principal-dashboard' %}">Principal Dashboard</a>
{% endif %}

{% if can_access.academics %}
    <a href="{% url 'academic-portal' %}">Academic Portal</a>
{% endif %}