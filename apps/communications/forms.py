from django import forms
from django.utils.translation import gettext_lazy as _
from apps.core.forms import TenantAwareModelForm
from .models import (
    CommunicationChannel, CommunicationTemplate, 
    CommunicationCampaign, Communication, CommunicationAttachment
)

class CommunicationChannelForm(TenantAwareModelForm):
    """Form for creating and updating communication channels"""
    class Meta:
        model = CommunicationChannel
        fields = [
            'name', 'code', 'channel_type', 'description', 
            'is_active', 'priority', 'rate_limit', 'cost_per_message'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'config': forms.Textarea(attrs={'rows': 5}),
        }

class CommunicationTemplateForm(TenantAwareModelForm):
    """Form for creating and updating communication templates"""
    class Meta:
        model = CommunicationTemplate
        fields = [
            'name', 'code', 'template_type', 'channel', 
            'subject', 'body', 'language', 'description', 
            'variables', 'is_active', 'requires_approval'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'body': forms.Textarea(attrs={'rows': 10}),
            'variables': forms.Textarea(attrs={'rows': 3, 'placeholder': '["variable1", "variable2"]'}),
        }

class CommunicationCampaignForm(TenantAwareModelForm):
    """Form for creating and updating communication campaigns"""
    class Meta:
        model = CommunicationCampaign
        fields = [
            'name', 'campaign_type', 'template', 'scheduled_for', 
            'is_recurring', 'recurrence_pattern', 'target_audience', 
            'budget', 'rate_limit'
        ]
        widgets = {
            'scheduled_for': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'recurrence_pattern': forms.Textarea(attrs={'rows': 3}),
            'target_audience': forms.Textarea(attrs={'rows': 5}),
        }

class CommunicationComposeForm(TenantAwareModelForm):
    """Form for composing individual communications"""
    class Meta:
        model = Communication
        fields = [
            'title', 'subject', 'content', 'channel', 
            'template', 'recipient_type', 'recipient_id',
            'external_recipient_name', 'external_recipient_email', 
            'external_recipient_phone', 'priority', 'scheduled_for'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'scheduled_for': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.contenttypes.models import ContentType
        
        # Filter channels and templates to tenant
        self.fields['channel'].queryset = CommunicationChannel.objects.filter(
            tenant=self.tenant, is_active=True
        )
        self.fields['template'].queryset = CommunicationTemplate.objects.filter(
            tenant=self.tenant, is_active=True
        )
        self.fields['template'].required = False

        # Filter recipient types to relevant models only
        relevant_models = ['user', 'student', 'staff', 'parent']
        self.fields['recipient_type'].queryset = ContentType.objects.filter(
            model__in=relevant_models
        )
        self.fields['recipient_type'].required = False
        self.fields['recipient_id'].required = False

    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        recipient_id = cleaned_data.get('recipient_id')
        ext_name = cleaned_data.get('external_recipient_name')
        ext_email = cleaned_data.get('external_recipient_email')
        ext_phone = cleaned_data.get('external_recipient_phone')

        # Logic to check if either system recipient or external contact is present
        system_recipient = recipient_type and recipient_id
        external_contact = ext_name and (ext_email or ext_phone)

        if not (system_recipient or external_contact):
            raise forms.ValidationError(
                _("Either system recipient or external contact information is required")
            )
        
        if recipient_type and not recipient_id:
            self.add_error('recipient_id', _("Recipient ID is required when Recipient Type is selected"))
            
        return cleaned_data
