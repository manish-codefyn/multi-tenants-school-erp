from django.contrib.auth.mixins import UserPassesTestMixin


class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin to require that the current user belongs to at least one of the given groups.

    Usage:
        class MyView(RoleRequiredMixin, TemplateView):
            required_roles = ['student']
    """

    required_roles = None  # list or tuple or string

    def test_func(self):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        # Allow superusers
        if getattr(user, 'is_superuser', False):
            return True
        roles = self.required_roles or []
        if isinstance(roles, str):
            roles = [roles]
        user_groups = {g.name for g in user.groups.all()}
        return bool(user_groups.intersection(set(roles)))


class TenantRequiredMixin:
    """Placeholder mixin for tenant checks. Implement as needed for your tenancy model."""

    def dispatch(self, request, *args, **kwargs):
        # Example: ensure request.tenant exists
        # if not getattr(request, 'tenant', None):
        #     return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)
