# apps/students/permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Permission
from django.db.models import Q


class StudentPermission(permissions.BasePermission):
    """
    Custom permission for Student operations
    """
    def has_permission(self, request, view):
        user = request.user
        
        # Superusers have all permissions
        if user.is_superuser:
            return True
            
        # Check if user belongs to current tenant
        if not hasattr(request, 'tenant') or request.tenant != user.tenant:
            return False
            
        # Map view actions to permissions
        if view.action == 'list':
            return user.has_perm('students.view_student') or user.has_perm('students.view_own_student')
        elif view.action == 'retrieve':
            return user.has_perm('students.view_student') or user.has_perm('students.view_own_student')
        elif view.action == 'create':
            return user.has_perm('students.add_student')
        elif view.action == 'update' or view.action == 'partial_update':
            return user.has_perm('students.change_student') or user.has_perm('students.change_own_student')
        elif view.action == 'destroy':
            return user.has_perm('students.delete_student')
        elif view.action == 'dashboard':
            return user.has_perm('students.view_student_dashboard')
        elif view.action == 'export':
            return user.has_perm('students.export_student_data')
        elif view.action == 'bulk_update':
            return user.has_perm('students.bulk_update_students')
            
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superusers have all permissions
        if user.is_superuser:
            return True
            
        # Check if object belongs to user's tenant
        if hasattr(obj, 'tenant') and obj.tenant != request.tenant:
            return False
            
        # Check own student permissions
        if user.has_perm('students.view_own_student') and obj.user == user:
            return view.action in ['retrieve', 'update', 'partial_update']
            
        # Check general permissions
        if view.action == 'retrieve':
            return user.has_perm('students.view_student')
        elif view.action == 'update' or view.action == 'partial_update':
            return user.has_perm('students.change_student')
        elif view.action == 'destroy':
            return user.has_perm('students.delete_student')
            
        return False


class GuardianPermission(permissions.BasePermission):
    """Permissions for Guardian operations"""
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
            
        if not hasattr(request, 'tenant') or request.tenant != user.tenant:
            return False
            
        if view.action in ['list', 'retrieve']:
            return user.has_perm('students.view_student')
        elif view.action == 'create':
            return user.has_perm('students.add_student')
        elif view.action in ['update', 'partial_update', 'destroy']:
            return user.has_perm('students.change_student')
            
        return True


class StudentDocumentPermission(permissions.BasePermission):
    """Permissions for Student Document operations"""
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
            
        if not hasattr(request, 'tenant') or request.tenant != user.tenant:
            return False
            
        if view.action in ['list', 'retrieve']:
            return user.has_perm('students.view_student')
        elif view.action == 'create':
            return user.has_perm('students.add_student')
        elif view.action in ['update', 'partial_update']:
            return user.has_perm('students.change_student')
        elif view.action == 'verify':
            return user.has_perm('students.verify_document')
        elif view.action == 'download':
            return user.has_perm('students.view_student')
            
        return True


def get_student_permissions():
    """Return all permissions for Student model"""
    return [
        ('add_student', 'Can add student'),
        ('change_student', 'Can change student'),
        ('delete_student', 'Can delete student'),
        ('view_student', 'Can view student'),
        ('view_own_student', 'Can view own student profile'),
        ('change_own_student', 'Can change own student profile'),
        ('view_student_dashboard', 'Can view student dashboard'),
        ('export_student_data', 'Can export student data'),
        ('bulk_update_students', 'Can bulk update students'),
        ('verify_document', 'Can verify student documents'),
    ]