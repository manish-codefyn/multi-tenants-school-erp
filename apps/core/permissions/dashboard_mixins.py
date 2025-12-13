# apps/core/permissions/dashboard_mixins.py
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

class DashboardAccessMixin(AccessMixin):
    """Mixin for dashboard access control"""
    
    dashboard_name = None
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        
        # Superusers can access everything
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Check specific permission if required
        if self.permission_required and not user.has_perm(self.permission_required):
            raise PermissionDenied
        
        # Check dashboard-specific access
        if not self._has_dashboard_access(user):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def _has_dashboard_access(self, user):
        """Check if user has access to this dashboard"""
        from ..dashboard_utils import DashboardRouter
        
        # Get user's available dashboards
        available_dashboards = DashboardRouter.get_available_dashboards(user)
        
        # Check if current dashboard is in available list
        current_dashboard = self.get_dashboard_name()
        for dashboard in available_dashboards:
            if dashboard['name'].lower() == current_dashboard.lower():
                return True
        
        return False
    
    def get_dashboard_name(self):
        """Get current dashboard name"""
        return self.dashboard_name or self.__class__.__name__.replace('View', '').lower()
    
    def handle_no_permission(self):
        """Handle users without dashboard access"""
        from django.contrib import messages
        
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                "You don't have permission to access this dashboard."
            )
            return redirect('dashboard_switcher')
        
        return super().handle_no_permission()