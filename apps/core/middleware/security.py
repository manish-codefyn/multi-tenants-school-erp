
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import re


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Security headers middleware to add various security-related headers to responses.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Default security headers configuration
        self.security_headers = getattr(settings, 'SECURITY_HEADERS', {
            'X_FRAME_OPTIONS': 'DENY',
            'X_CONTENT_TYPE_OPTIONS': 'nosniff',
            'X_XSS_PROTECTION': '1; mode=block',
            'REFERRER_POLICY': 'strict-origin-when-cross-origin',
            'PERMISSIONS_POLICY': {
                'camera': '()',
                'microphone': '()',
                'geolocation': '()',
                'payment': '()',
            },
            'STRICT_TRANSPORT_SECURITY': {
                'max_age': 31536000,  # 1 year
                'include_subdomains': True,
                'preload': False,
            },
            'CONTENT_SECURITY_POLICY': {
                'default-src': ["'self'"],
                'script-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
                'style-src': ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"],
                'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
                'img-src': ["'self'", "data:", "https:"],
                'connect-src': ["'self'"],
                'frame-src': ["'self'"],
                'object-src': ["'none'"],
                'base-uri': ["'self'"],
                'form-action': ["'self'"],
            }
        })

    def process_response(self, request, response):
        """
        Add security headers to the response
        """
        # Don't add headers to admin pages if configured
        if hasattr(settings, 'SECURITY_HEADERS_EXCLUDE_ADMIN') and settings.SECURITY_HEADERS_EXCLUDE_ADMIN:
            if request.path.startswith('/admin/'):
                return response

        # Add each security header
        self.add_frame_options(response)
        self.add_content_type_options(response)
        self.add_xss_protection(response)
        self.add_referrer_policy(response)
        self.add_permissions_policy(response)
        self.add_strict_transport_security(response)
        self.add_content_security_policy(response)
        self.add_feature_policy(response)
        
        # Additional custom headers
        self.add_custom_headers(response)
        
        return response

    def add_frame_options(self, response):
        """Add X-Frame-Options header"""
        x_frame_options = self.security_headers.get('X_FRAME_OPTIONS', 'DENY')
        if x_frame_options:
            response['X-Frame-Options'] = x_frame_options

    def add_content_type_options(self, response):
        """Add X-Content-Type-Options header"""
        x_content_type_options = self.security_headers.get('X_CONTENT_TYPE_OPTIONS', 'nosniff')
        if x_content_type_options:
            response['X-Content-Type-Options'] = x_content_type_options

    def add_xss_protection(self, response):
        """Add X-XSS-Protection header"""
        x_xss_protection = self.security_headers.get('X_XSS_PROTECTION', '1; mode=block')
        if x_xss_protection:
            response['X-XSS-Protection'] = x_xss_protection

    def add_referrer_policy(self, response):
        """Add Referrer-Policy header"""
        referrer_policy = self.security_headers.get('REFERRER_POLICY', 'strict-origin-when-cross-origin')
        if referrer_policy:
            response['Referrer-Policy'] = referrer_policy

    def add_permissions_policy(self, response):
        """Add Permissions-Policy header (replaces Feature-Policy)"""
        permissions_policy = self.security_headers.get('PERMISSIONS_POLICY', {})
        if permissions_policy:
            policy_directives = []
            for feature, value in permissions_policy.items():
                policy_directives.append(f"{feature}={value}")
            response['Permissions-Policy'] = ', '.join(policy_directives)

    def add_feature_policy(self, response):
        """Add Feature-Policy header (legacy, for older browsers)"""
        feature_policy = self.security_headers.get('FEATURE_POLICY', {})
        if feature_policy:
            policy_directives = []
            for feature, value in feature_policy.items():
                policy_directives.append(f"{feature} {value}")
            response['Feature-Policy'] = '; '.join(policy_directives)

    def add_strict_transport_security(self, response):
        """Add Strict-Transport-Security header"""
        hsts_config = self.security_headers.get('STRICT_TRANSPORT_SECURITY', {})
        if hsts_config and request.is_secure():
            max_age = hsts_config.get('max_age', 31536000)
            include_subdomains = hsts_config.get('include_subdomains', True)
            preload = hsts_config.get('preload', False)
            
            hsts_value = f"max-age={max_age}"
            if include_subdomains:
                hsts_value += "; includeSubDomains"
            if preload:
                hsts_value += "; preload"
                
            response['Strict-Transport-Security'] = hsts_value

    def add_content_security_policy(self, response):
        """Add Content-Security-Policy header"""
        csp_config = self.security_headers.get('CONTENT_SECURITY_POLICY', {})
        if csp_config:
            csp_directives = []
            for directive, sources in csp_config.items():
                if sources:
                    sources_str = ' '.join(str(source) for source in sources)
                    csp_directives.append(f"{directive} {sources_str}")
            
            csp_value = '; '.join(csp_directives)
            response['Content-Security-Policy'] = csp_value

    def add_custom_headers(self, response):
        """Add any custom security headers"""
        custom_headers = self.security_headers.get('CUSTOM_HEADERS', {})
        for header, value in custom_headers.items():
            response[header] = value

    def should_add_headers(self, request, response):
        """
        Determine whether to add security headers to this response
        """
        # Skip for certain content types
        content_type = response.get('Content-Type', '')
        if any(ct in content_type for ct in ['image/', 'font/', 'audio/', 'video/']):
            return False

        # Skip for certain paths (API endpoints, static files, etc.)
        excluded_paths = getattr(settings, 'SECURITY_HEADERS_EXCLUDED_PATHS', [])
        for path in excluded_paths:
            if re.match(path, request.path):
                return False

        return True