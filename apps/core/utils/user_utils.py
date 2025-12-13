# apps/core/utils/user_utils.py
"""
Utility functions for working with the custom User model
"""
from django.contrib.auth import get_user_model

def get_user_model_class():
    """Get the custom User model class"""
    return get_user_model()

def get_user_queryset():
    """Get User queryset"""
    User = get_user_model()
    return User.objects.all()

def get_user_by_id(user_id):
    """Get user by ID"""
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

def get_user_by_email(email):
    """Get user by email"""
    User = get_user_model()
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None