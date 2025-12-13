from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from .models import OnlineApplication, AdmissionCycle, AdmissionProgram

class AdmissionApplicationForm(forms.ModelForm):
    class Meta:
        model = OnlineApplication
        exclude = [
            'application_number', 'status', 'submission_date', 'review_date', 
            'decision_date', 'application_fee_paid', 'payment_reference', 
            'payment_date', 'ip_address', 'user_agent', 'tenant', 'created_by', 'updated_by'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'address_line1': forms.Textarea(attrs={'rows': 2}),
            'address_line2': forms.Textarea(attrs={'rows': 2}),
            'special_requirements': forms.Textarea(attrs={'rows': 3}),
            'comments': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _("Program Selection"),
                Row(
                    Column('admission_cycle', css_class='form-group col-md-6 mb-0'),
                    Column('program', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Student Personal Information"),
                Row(
                    Column('first_name', css_class='form-group col-md-4 mb-0'),
                    Column('middle_name', css_class='form-group col-md-4 mb-0'),
                    Column('last_name', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('date_of_birth', css_class='form-group col-md-4 mb-0'),
                    Column('gender', css_class='form-group col-md-4 mb-0'),
                    Column('blood_group', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('category', css_class='form-group col-md-4 mb-0'),
                    Column('nationality', css_class='form-group col-md-4 mb-0'),
                    Column('religion', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Contact Information"),
                Row(
                    Column('email', css_class='form-group col-md-6 mb-0'),
                    Column('phone', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('alternate_phone', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Address Details"),
                Row(
                    Column('address_line1', css_class='form-group col-md-6 mb-0'),
                    Column('address_line2', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('city', css_class='form-group col-md-3 mb-0'),
                    Column('state', css_class='form-group col-md-3 mb-0'),
                    Column('pincode', css_class='form-group col-md-3 mb-0'),
                    Column('country', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Previous Academic Details"),
                Row(
                    Column('previous_school', css_class='form-group col-md-6 mb-0'),
                    Column('previous_board', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('previous_qualification', css_class='form-group col-md-4 mb-0'),
                    Column('previous_percentage', css_class='form-group col-md-4 mb-0'),
                    Column('passing_year', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Medical Information"),
                Row(
                    Column('has_medical_conditions', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('medical_conditions', css_class='form-group col-md-6 mb-0'),
                    Column('allergies', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('emergency_contact_name', css_class='form-group col-md-4 mb-0'),
                    Column('emergency_contact_relation', css_class='form-group col-md-4 mb-0'),
                    Column('emergency_contact_phone', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                _("Additional Information"),
                Row(
                    Column('house_choice', css_class='form-group col-md-4 mb-0'),
                    Column('transport_required', css_class='form-group col-md-4 mb-0'),
                    Column('hostel_required', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('special_requirements', css_class='form-group col-md-6 mb-0'),
                    Column('how_heard', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('comments', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
            ),
            Div(
                Submit('submit', _('Submit Application'), css_class='btn btn-primary btn-lg'),
                css_class='text-center mt-4'
            )
        )
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure tenant is set
        if not self.instance.tenant_id and self.tenant:
            self.instance.tenant = self.tenant
        
        return cleaned_data

class AdmissionStatusCheckForm(forms.Form):
    application_number = forms.CharField(
        label=_("Application Number"),
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. APP-2024-00001'})
    )
    date_of_birth = forms.DateField(
        label=_("Date of Birth"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('application_number', css_class='form-group col-md-6 mb-0'),
                Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Div(
                Submit('submit', _('Check Status'), css_class='btn btn-primary'),
                css_class='text-center mt-3'
            )
        )
