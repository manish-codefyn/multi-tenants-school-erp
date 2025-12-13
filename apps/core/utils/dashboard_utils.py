
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import get_user_model

class DashboardRouter:
    """
    Professional dashboard routing system with permission checking
    """
    
    # Role categories
    SYSTEM_ROLES = ['super_admin', 'admin']
    STAFF_ROLES = ['teacher', 'staff', 'principal', 'headmaster', 'accountant', 
                   'librarian', 'counselor', 'supervisor', 'vice_principal', 
                   'department_head', 'clerk', 'hr', 'it_staff', 'lab_assistant']
    STUDENT_FAMILY_ROLES = ['student', 'parent', 'guardian', 'alumni']
    
    # Dashboard URLs
    DASHBOARD_URLS = {
        # System dashboards
        'super_admin': {
            'name': 'System Admin Dashboard',
            'url_name': 'system_admin_dashboard',
            'app': 'system_admin',
            'permission_required': None,  # Super admin has all permissions
            'fallback': '/admin/'
        },
        'admin': {
            'name': 'Admin Dashboard',
            'url_name': 'admin_dashboard',
            'app': 'admin_panel',
            'permission_required': 'admin_panel.access_admin_dashboard',
            'fallback': '/admin/'
        },
        
        # Staff dashboard (common for all staff roles)
        'staff_common': {
            'name': 'Staff Dashboard',
            'url_name': 'staff_dashboard',
            'app': 'staff_portal',
            'permission_required': 'staff_portal.access_staff_dashboard',
            'fallback': 'home'
        },
        
        # Student & Family dashboard (common)
        'student_family_common': {
            'name': 'Student Portal',
            'url_name': 'student_portal_dashboard',
            'app': 'student_portal',
            'permission_required': 'student_portal.access_student_dashboard',
            'fallback': 'home'
        },
    }
    
    # Role to dashboard mapping
    ROLE_DASHBOARD_MAP = {
        # System roles
        'super_admin': 'super_admin',
        'admin': 'admin',
        
        # All staff roles go to common staff dashboard
        'teacher': 'staff_common',
        'staff': 'staff_common',
        'principal': 'staff_common',
        'headmaster': 'staff_common',
        'accountant': 'staff_common',
        'librarian': 'staff_common',
        'counselor': 'staff_common',
        'supervisor': 'staff_common',
        'vice_principal': 'staff_common',
        'department_head': 'staff_common',
        'clerk': 'staff_common',
        'hr': 'staff_common',
        'it_staff': 'staff_common',
        'lab_assistant': 'staff_common',
        
        # Student & family roles
        'student': 'student_family_common',
        'parent': 'student_family_common',
        'guardian': 'student_family_common',
        'alumni': 'student_family_common',
    }
    
    @classmethod
    def get_user_category(cls, user):
        """Determine user's category based on role"""
        if user.is_superuser:
            return 'system_superuser'
        
        role = getattr(user, 'role', 'student')
        
        if role in cls.SYSTEM_ROLES:
            return 'system'
        elif role in cls.STAFF_ROLES:
            return 'staff'
        elif role in cls.STUDENT_FAMILY_ROLES:
            return 'student_family'
        else:
            return 'unknown'

    @classmethod
    def get_dashboard_url(cls, user):
        """Get the appropriate dashboard URL for a user"""
        if not user.is_authenticated:
            return reverse('login')
            
        # Check for no role
        if not getattr(user, 'role', None) and not user.is_superuser:
            return reverse('admission:landing')
            
        dashboard_key = cls._get_dashboard_key(user)
        dashboard_config = cls.DASHBOARD_URLS.get(dashboard_key)
        
        if dashboard_config:
            try:
                return reverse(dashboard_config['url_name'])
            except Exception:
                return dashboard_config.get('fallback', '/')
        
        return '/'

    @classmethod
    def get_user_dashboard_info(cls, user):
        """Get detailed dashboard information for a user"""
        dashboard_key = cls._get_dashboard_key(user)
        dashboard_config = cls.DASHBOARD_URLS.get(dashboard_key, {})
        
        url = '/'
        try:
            if 'url_name' in dashboard_config:
                url = reverse(dashboard_config['url_name'])
        except Exception:
            url = dashboard_config.get('fallback', '/')
            
        return {
            'user': user,
            'dashboard_name': dashboard_config.get('name', 'Dashboard'),
            'url': url,
            'has_permission': True, # Simplified for now
            'available_dashboards': cls.get_available_dashboards(user)
        }

    @classmethod
    def get_available_dashboards(cls, user):
        """Get all dashboards available to a user"""
        dashboards = []
        
        # Add primary dashboard
        primary_key = cls._get_dashboard_key(user)
        if primary_key in cls.DASHBOARD_URLS:
            config = cls.DASHBOARD_URLS[primary_key]
            try:
                url = reverse(config['url_name'])
                dashboards.append({
                    'name': config['name'],
                    'url': url,
                    'active': True
                })
            except Exception:
                pass
                
        return dashboards

    @classmethod
    def _get_dashboard_key(cls, user):
        """Helper to get dashboard key from user role"""
        if user.is_superuser:
            return 'super_admin'
            
        role = getattr(user, 'role', 'student')
        return cls.ROLE_DASHBOARD_MAP.get(role, 'student_family_common')