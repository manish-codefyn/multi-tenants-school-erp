# apps/core/middleware.py
from django.utils import timezone

class DashboardAccessMiddleware:
    """Middleware to track dashboard access"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track dashboard access
        if request.user.is_authenticated:
            self._track_dashboard_access(request)
        
        return response
    
    def _track_dashboard_access(self, request):
        """Track user's dashboard access"""
        from apps.auth.models import SecurityEvent
        
        # Check if this is a dashboard URL
        path = request.path
        dashboard_paths = ['/dashboard/', '/portal/', '/admin/', '/staff/']
        
        if any(path.startswith(p) for p in dashboard_paths):
            try:
                SecurityEvent.objects.create(
                    user=request.user,
                    event_type='dashboard_access',
                    severity='low',
                    description=f'Accessed {path}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'path': path,
                        'method': request.method,
                        'role': request.user.role,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
            except Exception:
                # Silently fail for tracking errors
                pass