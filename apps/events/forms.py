from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Event, EventCategory, EventRegistration, EventDocument
from apps.core.forms import TenantAwareModelForm
from apps.core.utils.form_helpers import DateInput, TimeInput, PhoneInput, SelectWithSearch

class EventCategoryForm(TenantAwareModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'code', 'description', 'color', 'icon', 'is_active', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px;'}),
        }

class EventForm(TenantAwareModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'short_description', 'event_type', 'category',
            'start_date', 'end_date', 'start_time', 'end_time', 'is_all_day',
            'venue', 'address', 'google_maps_link', 'is_online', 'online_link',
            'event_scope', 'target_classes', 'target_sections', 'academic_year',
            'status', 'priority', 'is_published', 'is_featured', 'featured_image',
            'max_attendees', 'requires_registration', 'registration_deadline',
            'is_free', 'fee_amount', 'fee_currency', 'organizer_name',
            'organizer_email', 'organizer_phone', 'tags', 'external_link'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'start_date': DateInput(),
            'end_date': DateInput(),
            'start_time': TimeInput(),
            'end_time': TimeInput(),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'category': SelectWithSearch(),
            'target_classes': forms.CheckboxSelectMultiple(),
            'target_sections': forms.CheckboxSelectMultiple(),
            'organizer_phone': PhoneInput(),
            'academic_year': SelectWithSearch(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # academic_year is required
        self.fields['academic_year'].required = True

class EventRegistrationForm(TenantAwareModelForm):
    class Meta:
        model = EventRegistration
        fields = [
            'event', 'student', 'user', 'external_name', 'external_email',
            'external_phone', 'external_organization', 'registration_type',
            'status', 'special_requirements', 'dietary_restrictions',
            'emergency_contact', 'emergency_phone', 'internal_notes'
        ]
        widgets = {
            'event': SelectWithSearch(),
            'student': SelectWithSearch(),
            'user': SelectWithSearch(),
            'external_phone': PhoneInput(),
            'emergency_phone': PhoneInput(),
            'special_requirements': forms.Textarea(attrs={'rows': 2}),
            'dietary_restrictions': forms.Textarea(attrs={'rows': 2}),
            'internal_notes': forms.Textarea(attrs={'rows': 2}),
        }

class EventDocumentForm(TenantAwareModelForm):
    class Meta:
        model = EventDocument
        fields = ['event', 'name', 'document_type', 'file', 'description', 'is_public']
        widgets = {
            'event': SelectWithSearch(),
            'description': forms.Textarea(attrs={'rows': 2}),
        }
