from django.views.generic import TemplateView, ListView, DetailView
from apps.tenants.models import Tenant

class HomeView(TemplateView):
    template_name = 'public/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_tenants'] = Tenant.objects.filter(
            status=Tenant.STATUS_ACTIVE,
            is_active=True
        ).exclude(schema_name='public')[:6]
        return context

class TenantListView(ListView):
    model = Tenant
    template_name = 'public/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 12

    def get_queryset(self):
        return Tenant.objects.filter(
            status=Tenant.STATUS_ACTIVE,
            is_active=True
        ).exclude(schema_name='public').order_by('name')

class TenantDetailView(DetailView):
    model = Tenant
    template_name = 'public/tenant_detail.html'
    context_object_name = 'tenant'
    slug_field = 'schema_name'
    slug_url_kwarg = 'schema_name'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.object, 'configuration'):
            context['tenant_config'] = self.object.configuration
        return context
