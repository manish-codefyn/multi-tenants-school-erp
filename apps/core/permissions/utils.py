from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

def create_custom_permission(name, codename, content_type, description=""):
    """
    Create a custom permission
    """
    permission, created = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={
            'name': name,
            'description': description
        }
    )
    return permission


def assign_role_permissions(user, tenant=None):
    """
    Assign all permissions based on user's role
    """
    from apps.auth.models import RolePermission
    from django.contrib.auth.models import Permission
    
    # Get permissions for the role
    perm_codenames = RolePermission.get_permissions_for_role(user.role, tenant)
    
    # Get permission objects
    permissions = Permission.objects.filter(codename__in=perm_codenames)
    
    # Assign to user
    user.user_permissions.set(permissions)
    user.save()


def check_user_permission(user, permission_codename, obj=None):
    """
    Check if user has permission, considering role and object-level permissions
    """
    if user.is_superuser:
        return True
    
    # Check direct permission
    if user.has_perm(permission_codename):
        return True
    
    # Check role permission
    from apps.auth.models import RolePermission
    role_perms = RolePermission.get_permissions_for_role(user.role, user.tenant)
    
    if permission_codename in role_perms:
        return True
    
    # Check object-level permission if object is provided
    if obj and hasattr(obj, 'has_permission'):
        return obj.has_permission(user, permission_codename)
    
    return False


def get_user_permissions_summary(user):
    """
    Get a summary of user's permissions
    """
    from apps.auth.models import RolePermission
    
    summary = {
        'role': user.role,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'direct_permissions': list(user.get_all_permissions()),
        'role_permissions': RolePermission.get_permissions_for_role(user.role, user.tenant),
        'modules': RolePermission.get_permissions_with_modules(user.role, user.tenant),
    }
    
    return summary


def can_user_access_module(user, module_name):
    """
    Check if user can access a specific module
    """
    if user.is_superuser:
        return True
    
    summary = get_user_permissions_summary(user)
    
    # Check if user has any permission in the module
    if module_name in summary['modules']:
        return True
    
    # Check wildcard permissions
    if '*' in summary['modules'] or 'all' in summary['modules']:
        return True
    
    return False


def filter_queryset_by_permission(user, queryset, permission_codename):
    """
    Filter queryset based on user's permissions
    """
    if user.is_superuser:
        return queryset
    
    # Get model from queryset
    model = queryset.model
    
    # Check if user has permission for all objects
    if user.has_perm(f"{model._meta.app_label}.view_{model._meta.model_name}"):
        return queryset
    
    # Apply filters based on user's role
    if user.role == 'teacher':
        # Teachers can only see their own classes
        if hasattr(model, 'teacher'):
            return queryset.filter(teacher=user)
        elif hasattr(model, 'created_by'):
            return queryset.filter(created_by=user)
    
    elif user.role == 'student':
        # Students can only see their own data
        if hasattr(model, 'student'):
            return queryset.filter(student=user)
    
    elif user.role == 'parent':
        # Parents can only see their children's data
        if hasattr(model, 'parent'):
            return queryset.filter(parent=user)
    
    # Default: return empty queryset
    return queryset.none()