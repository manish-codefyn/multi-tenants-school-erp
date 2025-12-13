
import os
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    OnlineApplication, AdmissionCycle, AdmissionProgram, 
    ApplicationDocument, ApplicationGuardian, MeritList
)
from apps.core.forms import BaseForm


class AdmissionApplicationForm(BaseForm):
    """Main form for online admission application"""
    
    # Add these fields for program selection if not using step-by-step wizard
    admission_cycle = forms.ModelChoiceField(
        queryset=AdmissionCycle.objects.none(),  # Will be set in __init__
        label=_("Admission Cycle"),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_admission_cycle',
            'data-action': 'change->admissions#onCycleChange'
        })
    )
    
    program = forms.ModelChoiceField(
        queryset=AdmissionProgram.objects.none(),  # Will be set in __init__
        label=_("Program"),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_program',
            'data-action': 'change->admissions#onProgramChange'
        })
    )
    
    # Add confirm email field
    confirm_email = forms.EmailField(
        label=_("Confirm Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Re-enter your email address')
        })
    )
    
    # Add password fields if creating user account
    create_account = forms.BooleanField(
        required=False,
        label=_("Create an account to track your application"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-action': 'change->admissions#togglePasswordFields'
        })
    )
    
    password = forms.CharField(
        required=False,
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a password')
        }),
        min_length=8
    )
    
    confirm_password = forms.CharField(
        required=False,
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password')
        })
    )
    
    # Custom widget for date of birth with age validation
    date_of_birth = forms.DateField(
        label=_("Date of Birth"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'max': timezone.now().date().isoformat(),
            'data-action': 'change->admissions#calculateAge'
        })
    )
    
    # Medical conditions conditional field
    medical_conditions_details = forms.CharField(
        required=False,
        label=_("Please specify medical conditions"),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': _('Describe any medical conditions in detail')
        })
    )
    
    # Terms and conditions acceptance
    accept_terms = forms.BooleanField(
        required=True,
        label=_("I accept the terms and conditions"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': 'required'
        })
    )
    
    class Meta:
        model = OnlineApplication
        fields = [
            'admission_cycle', 'program',
            'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'category', 'blood_group',
            'nationality', 'religion',
            'email',
            'phone', 'alternate_phone',
            'address_line1', 'address_line2', 
            'city', 'state', 'pincode', 'country',
            'previous_school', 'previous_qualification',
            'previous_percentage', 'previous_board', 'passing_year',
            'has_medical_conditions',
            'allergies',
            'emergency_contact_name', 'emergency_contact_relation', 'emergency_contact_phone',
            'house_choice', 'transport_required', 'hostel_required',
            'entrance_exam_name', 'entrance_exam_rank', 'entrance_exam_score',
            'special_requirements', 'how_heard', 'comments',
            # Do NOT include 'tenant' here since it's non-editable
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter first name'),
                'pattern': '[A-Za-z\s]+',
                'title': _('Only letters and spaces allowed')
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter middle name (optional)'),
                'pattern': '[A-Za-z\s]+'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter last name'),
                'pattern': '[A-Za-z\s]+'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Indian')
            }),
            'religion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Hindu, Muslim, Christian, etc.')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter valid email address')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+91 9876543210'),
                'pattern': r'^\+?1?\d{9,15}$'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+91 9876543210 (optional)'),
                'pattern': r'^\+?1?\d{9,15}$'
            }),
            'address_line1': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Flat/House No., Building, Street')
            }),
            'address_line2': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Area, Locality (optional)')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City/Town')
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State')
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('6-digit PIN code'),
                'pattern': r'\d{6}',
                'title': _('6-digit PIN code required')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Country'),
                'value': 'India'
            }),
            'previous_school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Name of previous school')
            }),
            'previous_qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Class 10, Grade 5, etc.')
            }),
            'previous_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Percentage or CGPA'),
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'previous_board': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., CBSE, ICSE, State Board')
            }),
           'passing_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('YYYY'),
                'min': '1900',
                'max': str(timezone.now().year),
                'step': '1'
            }),

            'has_medical_conditions': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-action': 'change->admissions#toggleMedicalDetails'
            }),
            'allergies': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('List any allergies (if any)')
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Full name of emergency contact')
            }),
            'emergency_contact_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Relation to student')
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Emergency contact phone number'),
                'pattern': r'^\+?1?\d{9,15}$'
            }),
            'house_choice': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('House preference (if any)')
            }),
            'transport_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'hostel_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'entrance_exam_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Entrance Test 2024 (if applicable)')
            }),
            'entrance_exam_rank': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Rank (if applicable)'),
                'min': '1'
            }),
            'entrance_exam_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Score (if applicable)'),
                'step': '0.01'
            }),
            'special_requirements': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Any special requirements or accommodations needed')
            }),
            'how_heard': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', _('How did you hear about us?')),
                ('FRIEND', _('Friend/Relative')),
                ('NEWSPAPER', _('Newspaper')),
                ('SOCIAL_MEDIA', _('Social Media')),
                ('WEBSITE', _('School Website')),
                ('HOARDING', _('Hoardings/Banners')),
                ('OTHER', _('Other'))
            ]),
            'comments': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Any additional comments or information')
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial queryset for programs based on active cycles
        if self.tenant:
            active_cycles = AdmissionCycle.objects.filter(
                is_active=True, 
                status='ACTIVE',
                tenant=self.tenant
            )
            self.fields['admission_cycle'].queryset = active_cycles
            
            # If only one active cycle, set it as initial and readonly
            if active_cycles.count() == 1:
                self.fields['admission_cycle'].initial = active_cycles.first()
           
          
                
                # Set programs for this cycle
                self.fields['program'].queryset = AdmissionProgram.objects.filter(
                    admission_cycle=active_cycles.first(),
                    is_active=True,
                    tenant=self.tenant
                )
            else:
                # Set empty program queryset initially
                self.fields['program'].queryset = AdmissionProgram.objects.filter(
                    is_active=True,
                    tenant=self.tenant
                )
        else:
            # If no tenant, use empty querysets
            self.fields['admission_cycle'].queryset = AdmissionCycle.objects.none()
            self.fields['program'].queryset = AdmissionProgram.objects.none()
        
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if field_name in ['accept_terms', 'has_medical_conditions', 
                             'transport_required', 'hostel_required', 'create_account']:
                continue  # Skip for checkbox fields
                
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.CheckboxInput,)):
                    field.widget.attrs['class'] = 'form-check-input'
                elif isinstance(field.widget, (forms.Select,)):
                    field.widget.attrs['class'] = 'form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
            
            # Add required attribute for required fields
            if field.required and field_name not in ['accept_terms', 'create_account']:
                field.widget.attrs['required'] = 'required'
            
            # Add aria-label for accessibility
            if field.label:
                field.widget.attrs['aria-label'] = str(field.label)
        
        # If user is logged in, pre-fill some information
        if self.user and self.user.is_authenticated:
            if not self.instance.pk:
                self.fields['email'].initial = self.user.email
                
                # Try to get user profile information
                if hasattr(self.user, 'profile'):
                    profile = self.user.profile
                    self.fields['first_name'].initial = profile.first_name or self.user.first_name
                    self.fields['last_name'].initial = profile.last_name or self.user.last_name
                    self.fields['phone'].initial = profile.phone if hasattr(profile, 'phone') else ''
        
        # Hide medical conditions details initially
        if not self.initial.get('has_medical_conditions'):
            self.fields['medical_conditions_details'].widget.attrs['style'] = 'display: none;'
        
        # Hide password fields initially
        # self.fields['password'].widget.attrs['style'] = 'display: none;'
        # self.fields['confirm_password'].widget.attrs['style'] = 'display: none;'
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Check tenant
        if not self.tenant:
            # Try to get tenant from admission cycle
            admission_cycle = cleaned_data.get('admission_cycle')
            if admission_cycle and hasattr(admission_cycle, 'tenant'):
                self.tenant = admission_cycle.tenant
            else:
                # Add non-field error
                raise ValidationError(_('Tenant context is required. Please select an admission cycle.'))
        
        # Ensure instance has tenant set for validation
        if self.tenant and not self.instance.tenant_id:
            self.instance.tenant = self.tenant

        # Email confirmation
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', _('Email addresses do not match.'))
        
        # Password validation if creating account
        create_account = cleaned_data.get('create_account')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if create_account:
            if not password:
                self.add_error('password', _('Password is required when creating an account.'))
            if not confirm_password:
                self.add_error('confirm_password', _('Please confirm your password.'))
            if password and confirm_password and password != confirm_password:
                self.add_error('confirm_password', _('Passwords do not match.'))
            if password and len(password) < 8:
                self.add_error('password', _('Password must be at least 8 characters long.'))
        
        # Date of birth validation
        date_of_birth = cleaned_data.get('date_of_birth')
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            
            if age < 3:
                self.add_error('date_of_birth', _('Applicant must be at least 3 years old.'))
            if age > 25:
                self.add_error('date_of_birth', _('Applicant age seems incorrect. Please verify.'))
        
        # Admission cycle and program validation
        admission_cycle = cleaned_data.get('admission_cycle')
        program = cleaned_data.get('program')
        
        if admission_cycle and program:
            # Check if program belongs to cycle
            if program.admission_cycle != admission_cycle:
                self.add_error('program', _('Selected program is not available in this admission cycle.'))
            
            # Check if cycle is open
            if not admission_cycle.is_open:
                self.add_error('admission_cycle', _('This admission cycle is not currently accepting applications.'))
            
            # Check age eligibility for program
            if date_of_birth and program:
                if not program.check_age_eligibility(date_of_birth):
                    self.add_error('date_of_birth', 
                        _('Age does not meet the eligibility criteria for %(program)s.') % {'program': program.class_grade}
                    )
            
            # Check academic eligibility
            previous_percentage = cleaned_data.get('previous_percentage')
            if previous_percentage and program.min_percentage:
                if previous_percentage < program.min_percentage:
                    self.add_error('previous_percentage',
                        _('Percentage does not meet minimum requirement of %(min_percent)s%% for %(program)s.') % {
                            'min_percent': program.min_percentage,
                            'program': program.class_grade
                        }
                    )
        
        # Medical conditions validation
        has_medical_conditions = cleaned_data.get('has_medical_conditions')
        medical_conditions_details = cleaned_data.get('medical_conditions_details')
        
        if has_medical_conditions and not medical_conditions_details:
            self.add_error('medical_conditions_details', 
                _('Please specify medical conditions when "Has Medical Conditions" is checked.')
            )
        
        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        admission_cycle = self.cleaned_data.get('admission_cycle')
        
        if email and admission_cycle and self.tenant:
            # Check for existing application in this cycle
            qs = OnlineApplication.objects.filter(
                email=email,
                admission_cycle=admission_cycle,
                tenant=self.tenant
            )
            
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    _('An application with this email already exists in the selected admission cycle.')
                )
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Remove any non-digit characters except +
        if phone:
            import re
            phone = re.sub(r'[^\d+]', '', phone)
            
            # Ensure Indian numbers start with +91 or 91
            if phone.startswith('0'):
                phone = phone[1:]
            
            if not phone.startswith('+91') and not phone.startswith('91'):
                phone = '+91' + phone.lstrip('+')
        
        return phone
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set tenant if not already set
        if not instance.tenant_id and self.tenant:
            instance.tenant = self.tenant
        
        # Set medical conditions from details field
        has_medical_conditions = self.cleaned_data.get('has_medical_conditions')
        medical_conditions_details = self.cleaned_data.get('medical_conditions_details')
        
        if has_medical_conditions and medical_conditions_details:
            instance.medical_conditions = medical_conditions_details
        
        # Set created by if user is logged in
        if self.user and self.user.is_authenticated:
            instance.created_by = self.user
        
        # Set default status to DRAFT
        if not instance.status:
            instance.status = 'DRAFT'
        
        # Generate application number on first save
        if not instance.application_number:
            # Save first to get ID
            if commit:
                instance.save()
                # Generate application number
                instance.application_number = instance.generate_application_number()
                instance.save()
        elif commit:
            instance.save()
        
        # Create user account if requested
        if self.cleaned_data.get('create_account') and commit:
            self._create_student_user(instance)
        
        return instance

    def _create_student_user(self, application):
        """Create a user account for the applicant"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        email = application.email
        password = self.cleaned_data.get('password')
        
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=application.first_name,
                last_name=application.last_name,
                role='student',
                tenant=self.tenant,
                is_active=True,
                is_verified=False
            )
            # Link application to user
            application.created_by = user
            application.save()

class ApplicationStep1Form(forms.ModelForm):
    """Step 1: Personal Information"""
    class Meta:
        model = OnlineApplication
        fields = [
            'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'category', 'blood_group',
            'nationality', 'religion'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ApplicationStep2Form(forms.ModelForm):
    """Step 2: Contact Information"""
    confirm_email = forms.EmailField(label=_("Confirm Email"))
    
    class Meta:
        model = OnlineApplication
        fields = [
            'email', 'phone', 'alternate_phone',
            'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'country'
        ]


from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import OnlineApplication


class ApplicationStep3Form(forms.ModelForm):
    """
    Step 3: Academic Information
    """

    class Meta:
        model = OnlineApplication
        fields = [
            'previous_school',
            'previous_qualification',
            'previous_percentage',
            'previous_board',
            'passing_year',
        ]

        widgets = {
            'previous_school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Name of Previous School'),
            }),

            'previous_qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Previous Qualification'),
            }),

            'previous_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Percentage (%)'),
                'min': '0',
                'max': '100',
                'step': '0.01',
            }),

            'previous_board': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Education Board (CBSE / ICSE / State Board)'),
            }),

            # YEAR FIELD (frontend)
         'passing_year': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': _('YYYY'),
                'max': str(timezone.now().year),
                'step': '1',
            }),
        }

        labels = {
            'previous_school': _('Previous School'),
            'previous_qualification': _('Qualification'),
            'previous_percentage': _('Percentage'),
            'previous_board': _('Board'),
            'passing_year': _('Year of Passing'),
        }

        help_texts = {
            'previous_percentage': _('Enter percentage obtained (e.g. 85.50)'),
            'passing_year': _('Enter year of passing (YYYY)'),
        }


class AdmissionStatusCheckForm(forms.Form):
    """Form for checking application status"""
    application_number = forms.CharField(
        label=_("Application Number"),
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'APP-2024-00001',
            'aria-label': 'Application Number',
            'autocomplete': 'off'
        })
    )
    
    date_of_birth = forms.DateField(
        label=_("Date of Birth"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'aria-label': 'Date of Birth',
            'max': timezone.now().date().isoformat()
        })
    )
    
    captcha = forms.CharField(
        required=False,
        label=_("Security Code"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter the code shown'),
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
    
    def clean(self):
        cleaned_data = super().clean()
        application_number = cleaned_data.get('application_number')
        date_of_birth = cleaned_data.get('date_of_birth')
        
        if application_number and date_of_birth:
            try:
                filters = {
                    'application_number': application_number,
                    'date_of_birth': date_of_birth
                }
                
                if self.tenant:
                    filters['tenant'] = self.tenant
                
                application = OnlineApplication.objects.get(**filters)
                cleaned_data['application'] = application
                
                # Check if application is submitted
                if application.status == 'DRAFT':
                    self.add_error(None, 
                        _('This application has not been submitted yet. Please submit your application first.')
                    )
                
            except OnlineApplication.DoesNotExist:
                self.add_error(None, 
                    _('No application found with the provided details. Please check your application number and date of birth.')
                )
        
        return cleaned_data


class ApplicationSearchForm(forms.Form):
    """Admin search form for applications"""
    SEARCH_CHOICES = [
        ('', _('Search by...')),
        ('application_number', _('Application Number')),
        ('email', _('Email Address')),
        ('phone', _('Phone Number')),
        ('name', _('Name')),
        ('aadhaar', _('Aadhaar Number')),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter search term...'),
            'aria-label': 'Search query'
        })
    )
    
    admission_cycle = forms.ModelChoiceField(
        queryset=AdmissionCycle.objects.all(),
        required=False,
        empty_label=_("All Admission Cycles"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    program = forms.ModelChoiceField(
        queryset=AdmissionProgram.objects.all(),
        required=False,
        empty_label=_("All Programs"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + list(OnlineApplication.APPLICATION_STATUS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ChoiceField(
        choices=[('', _('All Categories'))] + list(OnlineApplication.CATEGORY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        label=_("From Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        label=_("To Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['admission_cycle'].queryset = AdmissionCycle.objects.filter(tenant=self.tenant)
            self.fields['program'].queryset = AdmissionProgram.objects.filter(tenant=self.tenant)
        
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ApplicationDocumentForm(BaseForm):
    """Form for uploading application documents"""
    class Meta:
        model = ApplicationDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-control',
                'data-action': 'change->documents#onDocumentTypeChange'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
                'data-max-size': '5242880'  # 5MB
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Optional description or notes about this document')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        if self.application:
            # Filter out already uploaded document types
            existing_docs = self.application.documents.values_list('document_type', flat=True)
            available_choices = [
                choice for choice in self.fields['document_type'].choices 
                if choice[0] not in existing_docs
            ]
            self.fields['document_type'].choices = [('', _('Select document type'))] + available_choices
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # File size validation (5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('File size must be less than 5MB.'))
            
            # File type validation
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError(
                    _('Unsupported file format. Please upload PDF, JPG, PNG, or DOC files.')
                )
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.application:
            instance.application = self.application
        if commit:
            instance.save()
        return instance


class GuardianForm(BaseForm):
    """Form for guardian information"""
    is_primary = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Primary Guardian"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ApplicationGuardian
        exclude = ['application', 'tenant', 'created_by', 'updated_by']
        widgets = {
            'relation': forms.Select(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Full name of guardian')
            }),
            'occupation': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Guardian email address')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Guardian phone number'),
                'pattern': r'^\+?1?\d{9,15}$'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Alternate phone (optional)'),
                'pattern': r'^\+?1?\d{9,15}$'
            }),
            'address_line1': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Guardian address line 1')
            }),
            'address_line2': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': _('Guardian address line 2 (optional)')
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'\d{6}'
            }),
            'annual_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': _('Annual income (optional)')
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Highest qualification (optional)')
            }),
            'is_emergency_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name not in ['is_primary', 'is_emergency_contact']:
                field.widget.attrs.setdefault('class', 'form-control')
    
    def clean(self):
        cleaned_data = super().clean()
        is_primary = cleaned_data.get('is_primary')
        
        if self.application and is_primary:
            # Check if another primary guardian exists
            existing_primary = ApplicationGuardian.objects.filter(
                application=self.application,
                is_primary=True
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_primary.exists():
                self.add_error('is_primary', 
                    _('This application already has a primary guardian.')
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.application:
            instance.application = self.application
        
        # Ensure only one guardian is primary
        if instance.is_primary and self.application:
            ApplicationGuardian.objects.filter(
                application=self.application, 
                is_primary=True
            ).update(is_primary=False)
        
        if commit:
            instance.save()
        
        return instance


class ApplicationStatusUpdateForm(forms.Form):
    """Form for updating application status (admin use)"""
    status = forms.ChoiceField(
        choices=OnlineApplication.APPLICATION_STATUS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': _('Add notes about this status change...')
        })
    )
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Send notification email to applicant"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class MeritListGenerationForm(forms.Form):
    """Form for generating merit lists"""
    program = forms.ModelChoiceField(
        queryset=AdmissionProgram.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ChoiceField(
        choices=OnlineApplication.CATEGORY_CHOICES,
        initial='GENERAL',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    criteria = forms.ChoiceField(
        choices=[
            ('academic', _('Academic Performance (Previous Percentage)')),
            ('entrance', _('Entrance Exam Score')),
            ('combined', _('Combined Score (Academic + Entrance + Interview)')),
            ('custom', _('Custom Scoring')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    academic_weight = forms.IntegerField(
        initial=50,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px; display: inline;'
        })
    )
    
    entrance_weight = forms.IntegerField(
        initial=30,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px; display: inline;'
        })
    )
    
    interview_weight = forms.IntegerField(
        initial=20,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 100px; display: inline;'
        })
    )
    
    cutoff_score = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    auto_select = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Automatically select candidates based on available seats"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ApplicationFilterForm(forms.Form):
    """Filter form for applications in admin panel"""
    STATUS_CHOICES = [('', 'All Statuses')] + list(OnlineApplication.APPLICATION_STATUS)
    CATEGORY_CHOICES = [('', 'All Categories')] + list(OnlineApplication.CATEGORY_CHOICES)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    program = forms.ModelChoiceField(
        queryset=AdmissionProgram.objects.all(),
        required=False,
        empty_label="All Programs",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    admission_cycle = forms.ModelChoiceField(
        queryset=AdmissionCycle.objects.all(),
        required=False,
        empty_label="All Cycles",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    submitted_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'From Date'
        })
    )
    
    submitted_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm',
            'placeholder': 'To Date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['program'].queryset = AdmissionProgram.objects.filter(tenant=self.tenant)
            self.fields['admission_cycle'].queryset = AdmissionCycle.objects.filter(tenant=self.tenant)


class BulkApplicationActionForm(forms.Form):
    """Form for bulk actions on applications"""
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('change_status', 'Change Status'),
        ('export_csv', 'Export to CSV'),
        ('send_email', 'Send Email'),
        ('generate_admit_card', 'Generate Admit Cards'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_status = forms.ChoiceField(
        choices=[('', 'Select Status')] + list(OnlineApplication.APPLICATION_STATUS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    applications = forms.CharField(
        widget=forms.HiddenInput()
    )  # Will hold JSON list of application IDs


# Multi-step form wizard for application
from formtools.wizard.views import SessionWizardView

class AdmissionApplicationWizard(SessionWizardView):
    """Multi-step wizard for admission application"""
    template_name = 'admissions/application_wizard.html'
    form_list = [
        ('personal', ApplicationStep1Form),
        ('contact', ApplicationStep2Form),
        ('academic', ApplicationStep3Form),
        # Add more steps as needed
    ]
    
    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs(step)
        if 'tenant' in self.request.session:
            kwargs['tenant'] = self.request.session['tenant']
        return kwargs
    
    def done(self, form_list, **kwargs):
        # Combine all form data and create application
        form_data = {}
        for form in form_list:
            form_data.update(form.cleaned_data)
        
        # Create application instance
        application = OnlineApplication(**form_data)
        application.tenant = self.request.session.get('tenant')
        application.save()
        
        return redirect('admissions:application_complete', pk=application.pk)