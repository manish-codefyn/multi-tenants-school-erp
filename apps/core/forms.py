# apps/core/forms.py
from django import forms
from django.core.exceptions import ValidationError


class BaseForm(forms.ModelForm):
    """Base form with tenant handling"""
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter foreign key fields to current tenant's data
        if self.request and hasattr(self.request, 'tenant'):
            current_tenant = self.request.tenant
            for field_name, field in self.fields.items():
                if isinstance(field, forms.ModelChoiceField):
                    # Check if the related model has tenant field
                    model_class = field.queryset.model
                    if hasattr(model_class, 'tenant'):
                        # Filter to current tenant's data
                        field.queryset = field.queryset.filter(tenant=current_tenant)
        
        # Remove tenant field if it exists in form fields (not in model fields)
        if 'tenant' in self.fields:
            del self.fields['tenant']



class TenantAwareModelForm(forms.ModelForm):
    """Base form that handles tenant-specific data filtering"""
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.tenant = kwargs.pop('tenant', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Get tenant from request if not provided
        if not self.tenant and self.request:
            self.tenant = getattr(self.request, 'tenant', None)
            
        # Pre-assign tenant to instance if available
        if self.tenant:
            try:
                self.instance.tenant = self.tenant
            except Exception:
                pass

        # Filter foreign key fields to current tenant's data
        if self.tenant:
            for field_name, field in self.fields.items():
                if isinstance(field, forms.ModelChoiceField):
                    model_class = field.queryset.model
                    # Check if model has tenant field
                    if hasattr(model_class, 'tenant'):
                        field.queryset = field.queryset.filter(tenant=self.tenant)
    
    def clean(self):
        # Auto-assign tenant if not set (must do this before supervision validation)
        if self.tenant and hasattr(self.instance, 'tenant') and not self.instance.tenant_id:
            self.instance.tenant = self.tenant
            
        cleaned_data = super().clean()
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to ensure tenant is set before model validation"""
        instance = super().save(commit=False)
        
        # Ensure tenant is set before saving
        if hasattr(instance, 'tenant') and not instance.tenant_id:
            if self.tenant:
                instance.tenant = self.tenant
            elif self.request and hasattr(self.request, 'user'):
                user = self.request.user
                if hasattr(user, 'tenant'):
                    instance.tenant = user.tenant
        
        if commit:
            instance.save()
        
        return instance
