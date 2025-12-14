
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
import re
import logging

from apps.core.forms import TenantAwareModelForm
from .models import Student, Guardian, StudentDocument, StudentAddress

logger = logging.getLogger(__name__)


# ============================================================================
# BASE FORM CLASSES
# ============================================================================

class SecureStudentForm(TenantAwareModelForm):
    """
    Base form for all student-related forms with enhanced security
    and tenant integration
    """
    
    def __init__(self, *args, **kwargs):
        # Extract additional parameters
        self.user = kwargs.pop('user', None)
        self.instance_data = kwargs.pop('instance_data', None)
        
        super().__init__(*args, **kwargs)
        
        # Add security class to all input fields
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
    
    def clean(self):
        """Enhanced cleaning with tenant validation"""
        cleaned_data = super().clean()
        
        # Ensure tenant is set
        if not self.tenant:
            raise ValidationError(_("Tenant context is required"))
        
        # Add audit trail data
        if hasattr(self, 'instance') and self.instance.pk:
            cleaned_data['_audit_action'] = 'UPDATE'
            cleaned_data['_audit_user'] = self.user
        else:
            cleaned_data['_audit_action'] = 'CREATE'
            cleaned_data['_audit_user'] = self.user
        
        return cleaned_data
    
    def save(self, commit=True):
        """Enhanced save with audit trail"""
        instance = super().save(commit=False)
        
        # Set created_by/updated_by
        if not instance.pk and self.user:  # New instance
            instance.created_by = self.user
        elif self.user:  # Existing instance
            instance.updated_by = self.user
        
        if commit:
            try:
                # Calculate data signature before saving
                if hasattr(instance, 'calculate_signature'):
                    instance.data_signature = instance.calculate_signature()
                
                instance.save()
                
                # Save many-to-many relationships if any
                self.save_m2m()
                
            except Exception as e:
                logger.error(f"Error saving form for {self.__class__.__name__}: {str(e)}")
                raise
        
        return instance


# ============================================================================
# STUDENT FORMS
# ============================================================================

class StudentForm(SecureStudentForm):
    """
    Professional student form with comprehensive validation,
    tenant-aware dropdowns, and enhanced security
    """
    
    # Additional custom fields
    # confirm_email = forms.EmailField(
    #     required=False,
    #     label=_('Confirm Email'),
    #     widget=forms.EmailInput(attrs={
    #         'placeholder': _('Re-enter email for verification'),
    #         'class': 'form-control'
    #     }),
    #     help_text=_('Re-enter email address to confirm')
    # )
    
    accept_terms = forms.BooleanField(
        required=True,
        label=_('I accept the terms and conditions'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': _('You must accept the terms and conditions')}
    )
    
    class Meta:
        model = Student
        exclude = [
            'tenant', 'created_by', 'updated_by', 'deleted_by', 'user','passing_year',
            'data_signature', 'encryption_version', 'request_count',
            'last_request_at', 'rate_limit_key', 'is_active',
            'deleted_at', 'deletion_reason', 'deletion_category', 'admission_number', 'roll_number', 'reg_no',
            'current_semester', 'total_credits_earned', 'cumulative_grade_point'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'max': timezone.now().date().isoformat()
                }
            ),
            'enrollment_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
             'passing_year': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'tc_issue_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'first_name': forms.TextInput(
                attrs={
                    'placeholder': _('Enter first name'),
                    'class': 'form-control',
                    'autocomplete': 'given-name'
                }
            ),
            'middle_name': forms.TextInput(
                 attrs={
                    'placeholder': _('Enter middle name (optional)'),
                    'class': 'form-control',
                    'autocomplete': 'additional-name'
                }
            ),
            'last_name': forms.TextInput(
                attrs={
                    'placeholder': _('Enter last name'),
                    'class': 'form-control',
                    'autocomplete': 'family-name'
                }
            ),
            'personal_email': forms.EmailInput(
                attrs={
                    'placeholder': _('student@example.com'),
                    'class': 'form-control',
                    'autocomplete': 'email'
                }
            ),
             'institutional_email': forms.EmailInput(
                attrs={
                    'placeholder': _('id@school.edu (Auto-generated if empty)'),
                    'class': 'form-control',
                    'readonly': 'readonly'
                }
            ),
            'mobile_primary': forms.TextInput(
                attrs={
                    'placeholder': _('+91 9876543210'),
                    'class': 'form-control',
                    'pattern': '[0-9+\s\-()]{10,15}',
                    'title': _('Enter valid phone number (e.g. +91 9876543210)')
                }
            ),
             'mobile_secondary': forms.TextInput(
                attrs={
                    'placeholder': _('+91 9876543210'),
                    'class': 'form-control',
                    'pattern': '[0-9+\s\-()]{10,15}'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': _('Any additional notes, medical info, etc.'),
                    'class': 'form-control',
                    'rows': 3
                }
            ),
            'annual_family_income': forms.NumberInput(
                attrs={
                    'placeholder': _('Annual Income (INR)'),
                    'class': 'form-control',
                    'min': 0,
                    'step': 1000
                }
            ),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'religion': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'admission_type': forms.Select(attrs={'class': 'form-select'}),
            'fee_category': forms.Select(attrs={'class': 'form-select'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'personal_email': _('Official email address for communication'),
            'mobile_primary': _('Primary contact number with country code'),
            'date_of_birth': _('Student\'s birth date (YYYY-MM-DD)'),
            'admission_number': _('Unique admission identifier'),
            'roll_number': _('Class roll number (if applicable)'),
        }
        error_messages = {
            'personal_email': {
                'unique': _('This email is already registered'),
                'invalid': _('Enter a valid email address')
            },
            'mobile_primary': {
                'unique': _('This phone number is already registered')
            },
            'admission_number': {
                'unique': _('This admission number already exists')
            },
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tenant-aware queryset configuration
        if self.tenant:
            self.configure_tenant_fields()
        
        # Set required fields
        self.set_field_requirements()
        
        # Add dynamic help text for existing instances
        if self.instance and self.instance.pk:
            self.add_existing_instance_context()
            
            # Remove fields not needed for update
            if 'accept_terms' in self.fields:
                del self.fields['accept_terms']
            if 'confirm_email' in self.fields:
                del self.fields['confirm_email']
                
            # Pre-fill address fields if available
            try:
                address = self.instance.addresses.filter(is_current=True).first()
                if address:
                    self.fields['address_line1'].initial = address.address_line1
                    self.fields['city'].initial = address.city
                    self.fields['state'].initial = address.state
                    self.fields['pincode'].initial = address.pincode
            except Exception:
                pass

    # Address fields (Manual handling since not on Student model)
    address_line1 = forms.CharField(
        required=False,
        label=_('Address Line 1'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('House No, Street, Locality')})
    )
    city = forms.CharField(
        required=False,
        label=_('City'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('City')})
    )
    state = forms.CharField(
        required=False,
        label=_('State'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('State')})
    )
    pincode = forms.CharField(
        required=False,
        label=_('Pincode'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Pincode'), 'pattern': '[0-9]{6}'})
    )

    def clean(self):
        cleaned_data = super().clean()
        
        # Address validation: if any field provided, all are required
        addr = cleaned_data.get('address_line1')
        city = cleaned_data.get('city')
        state = cleaned_data.get('state')
        pincode = cleaned_data.get('pincode')
        
        if any([addr, city, state, pincode]):
            if not all([addr, city, state, pincode]):
                raise ValidationError(_("If providing an address, please fill all address fields (Line 1, City, State, Pincode)."))
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        if commit:
            # Handle Address Saving
            addr_line1 = self.cleaned_data.get('address_line1')
            if addr_line1:
                from .models import StudentAddress
                try:
                    # Check for existing current address
                    addr = StudentAddress.objects.filter(student=instance, is_current=True).first()
                    if not addr:
                        addr = StudentAddress(student=instance, is_current=True, address_type='PERMANENT')
                    
                    addr.address_line1 = addr_line1
                    addr.city = self.cleaned_data.get('city')
                    addr.state = self.cleaned_data.get('state')
                    addr.pincode = self.cleaned_data.get('pincode')
                    addr.country = 'India' # Default
                    addr.save()
                except Exception as e:
                    logger.error(f"Failed to save student address: {e}")
                    
        return instance
    
    def configure_tenant_fields(self):
        """Configure tenant-specific dropdowns"""
        from apps.academics.models import (
            AcademicYear, SchoolClass, Section, Stream
        )
        
        # Academic Year - only active and future years
        if 'academic_year' in self.fields:
            self.fields['academic_year'].queryset = AcademicYear.objects.filter(
                tenant=self.tenant,
                end_date__gte=timezone.now().date()
            ).order_by('-is_current', '-start_date')
        
        # Current Class - active classes only
        if 'current_class' in self.fields:
            self.fields['current_class'].queryset = SchoolClass.objects.filter(
                tenant=self.tenant,
                is_active=True
            ).order_by('order', 'name')
        
        # Section - filtered by selected class
        if 'section' in self.fields:
            # Initial queryset - will be updated via JavaScript based on class selection
            self.fields['section'].queryset = Section.objects.filter(
                tenant=self.tenant,
                is_active=True
            ).order_by('name')
        
        # Stream - active streams only
        # if 'stream' in self.fields:
        #     self.fields['stream'].queryset = Stream.objects.filter(
        #         tenant=self.tenant,
        #         is_active=True
        #     ).order_by('name')
    
    def set_field_requirements(self):
        """Set field requirements and attributes"""
        # Required fields
        required_fields = [
            'first_name', 'last_name', 'date_of_birth', 
            'gender', 'personal_email', 'mobile_primary',
            'academic_year', 'current_class'
        ]
        
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].widget.attrs['required'] = 'required'
        
        # Read-only fields for existing instances
        if self.instance and self.instance.pk:
            read_only_fields = ['admission_number', 'created_at', 'updated_at']
            for field_name in read_only_fields:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].widget.attrs['class'] += ' bg-light'
    
    def add_existing_instance_context(self):
        """Add context for existing instances"""
        instance = self.instance
        
        # Add helpful information
        if hasattr(instance, 'admission_number') and instance.admission_number:
            if 'admission_number' in self.fields:
                self.fields['admission_number'].help_text = _(
                    f'Admission number: {instance.admission_number} (Cannot be changed)'
                )
        
        # Show last updated information
        if instance.updated_at:
            if 'status_changed_date' in self.fields:
                self.fields['status_changed_date'].help_text = _(
                    f'Last updated: {instance.updated_at.strftime("%Y-%m-%d %H:%M")}'
                )
    
    def clean_personal_email(self):
        """Validate and normalize email"""
        email = self.cleaned_data.get('personal_email', '').strip().lower()
        
        if not email:
            raise ValidationError(_('Email address is required'))
        
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError(_('Enter a valid email address'))
        
        # Check for duplicate email within tenant
        if self.tenant:
            qs = Student.objects.filter(
                tenant=self.tenant,
                personal_email=email
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    _('A student with this email already exists in your institution')
                )
        
        return email
    
    def clean_confirm_email(self):
        """Validate email confirmation"""
        email = self.cleaned_data.get('personal_email', '')
        confirm_email = self.cleaned_data.get('confirm_email', '')
        
        if email and confirm_email and email.lower() != confirm_email.lower():
            raise ValidationError(_('Email addresses do not match'))
        
        return confirm_email
    
    # def clean_mobile_primary(self):
    #     """Validate and normalize phone number"""
    #     phone = self.cleaned_data.get('mobile_primary', '').strip()
        
    #     if not phone:
    #         raise ValidationError(_('Mobile number is required'))
        
    #     # Remove all non-digit characters
    #     digits = re.sub(r'\D', '', phone)
        
    #     # Validate length (10 digits for India)
    #     if len(digits) not in [10, 11, 12]:
    #         raise ValidationError(_('Enter a valid 10-12 digit phone number'))
        
    #     # Format phone number
    #     if digits.startswith('91') and len(digits) == 12:
    #         formatted = f"+{digits[:2]} {digits[2:]}"
    #     elif len(digits) == 10:
    #         formatted = f"+91 {digits}"
    #     else:
    #         formatted = f"+{digits}"
        
    #     # Check for duplicate within tenant
    #     if self.tenant:
    #         qs = Student.objects.filter(
    #             tenant=self.tenant,
    #             mobile_primary__contains=digits[-10:]  # Check last 10 digits
    #         )
    #         if self.instance and self.instance.pk:
    #             qs = qs.exclude(pk=self.instance.pk)
            
    #         if qs.exists():
    #             raise ValidationError(
    #                 _('A student with this phone number already exists')
    #             )
        
    #     return formatted
    
    def clean_date_of_birth(self):
        """Validate date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        
        if dob:
            # Check if date is in the future
            if dob > timezone.now().date():
                raise ValidationError(_('Date of birth cannot be in the future'))
            
            # Check if student is too young (less than 3 years)
            age = (timezone.now().date() - dob).days / 365.25
            if age < 3:
                raise ValidationError(_('Student must be at least 3 years old'))
            
            # Check if student is too old (more than 25 years)
            if age > 25:
                raise ValidationError(_('Student age seems unreasonable. Please verify.'))
        
        return dob
    
    def clean_admission_number(self):
        """Validate admission number"""
        admission_no = self.cleaned_data.get('admission_number', '').strip().upper()
        
        if admission_no and self.tenant:
            # Check format (example: ADM-2024-001)
            if not re.match(r'^[A-Z]{3}-[0-9]{4}-[0-9]{3,6}$', admission_no):
                raise ValidationError(
                    _('Admission number format: ADM-YYYY-XXX (e.g., ADM-2024-001)')
                )
            
            # Check for duplicates within tenant
            qs = Student.objects.filter(
                tenant=self.tenant,
                admission_number=admission_no
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    _('This admission number is already assigned to another student')
                )
        
        return admission_no
    
    def clean_annual_family_income(self):
        """Validate family income"""
        income = self.cleaned_data.get('annual_family_income')
        
        if income is not None:
            if income < 0:
                raise ValidationError(_('Income cannot be negative'))
            if income > 100000000:  # 10 crore
                raise ValidationError(_('Income seems unrealistically high. Please verify.'))
        
        return income
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Validate enrollment date is after date of birth
        dob = cleaned_data.get('date_of_birth')
        enrollment_date = cleaned_data.get('enrollment_date')
        
        if dob and enrollment_date and enrollment_date < dob:
            self.add_error(
                'enrollment_date',
                _('Enrollment date cannot be before date of birth')
            )
        
        # Validate graduation date is after enrollment date
        graduation_date = cleaned_data.get('graduation_date')
        if enrollment_date and graduation_date and graduation_date < enrollment_date:
            self.add_error(
                'graduation_date',
                _('Graduation date cannot be before enrollment date')
            )
        
        # Validate class and section compatibility
        current_class = cleaned_data.get('current_class')
        section = cleaned_data.get('section')
        
        if current_class and section:
            if not current_class.sections.filter(id=section.id).exists():
                self.add_error(
                    'section',
                    _('Selected section does not belong to the chosen class')
                )
        
        return cleaned_data


class StudentQuickCreateForm(StudentForm):
    """
    Simplified student form for quick creation
    Used in bulk operations or quick add scenarios
    """
    
    class Meta(StudentForm.Meta):
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'personal_email', 'mobile_primary', 'academic_year',
            'current_class', 'section'
        ]


class StudentRegistrationForm(StudentForm):
    """
    Form for public student registration
    Excludes internal status fields
    """
    class Meta(StudentForm.Meta):
        exclude = StudentForm.Meta.exclude + ['status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make all fields required
        for field_name, field in self.fields.items():
            field.required = True
        
        # Remove confirm_email and accept_terms from quick form
        if 'confirm_email' in self.fields:
            del self.fields['confirm_email']
        if 'accept_terms' in self.fields:
            del self.fields['accept_terms']


# ============================================================================
# GUARDIAN FORMS
# ============================================================================

class GuardianForm(SecureStudentForm):
    """
    Professional guardian form with relationship validation
    and contact information management
    """
    
    # Additional validation fields
    same_as_student_address = forms.BooleanField(
        required=False,
        label=_('Same as student address'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Check if guardian address is same as student address')
    )
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        required_fields = ['first_name', 'last_name', 'relationship', 'mobile']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Auto-fill address if student is provided
        if self.student and self.student.address and 'address' in self.fields:
            self.fields['address'].initial = self.student.address
            self.fields['same_as_student_address'].initial = True
    
    class Meta:
        model = Guardian
        exclude = ['student', 'tenant', 'created_at', 'updated_at', 'created_by', 'updated_by']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': timezone.now().date().isoformat()
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': _('Guardian first name'),
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': _('Guardian last name'),
                'class': 'form-control'
            }),
            'relationship': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={
                'placeholder': _('guardian@example.com'),
                'class': 'form-control'
            }),
            'mobile': forms.TextInput(attrs={
                'placeholder': _('+91 9876543210'),
                'class': 'form-control',
                'pattern': '[0-9+\s\-()]{10,15}'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'placeholder': _('Alternate contact number'),
                'class': 'form-control'
            }),
            'address': forms.Textarea(attrs={
                'placeholder': _('Complete guardian address'),
                'class': 'form-control',
                'rows': 3
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_emergency_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_pickup_student': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'relationship': _('Relationship to the student'),
            'occupation': _('Guardian\'s profession'),
            'is_primary': _('Primary guardian for all communications'),
            'is_emergency_contact': _('Contact in case of emergencies'),
            'can_pickup_student': _('Authorized to pick up student from school'),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract student for context
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # KEY FIX: Assign student to instance immediately so model validation and __str__ work
        if self.student:
            self.instance.student = self.student
        
        # Set required fields
        required_fields = ['first_name', 'last_name', 'relationship', 'mobile']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Auto-fill address if student is provided
        # Auto-fill address if student is provided
        if self.student and 'address' in self.fields:
             # Use current_address property since 'address' field doesn't exist on model directly
            current_addr = getattr(self.student, 'current_address', '')
            if current_addr:
                self.fields['address'].initial = current_addr
                self.fields['same_as_student_address'].initial = True
    
    def clean_mobile(self):
        """Validate guardian mobile number"""
        mobile = self.cleaned_data.get('mobile', '').strip()
        
        if not mobile:
            raise ValidationError(_('Mobile number is required for guardian'))
        
        # Validate phone number
        digits = re.sub(r'\D', '', mobile)
        if len(digits) not in [10, 11, 12]:
            raise ValidationError(_('Enter a valid 10-12 digit phone number'))
        
        return mobile
    
    def clean_email(self):
        """Validate guardian email"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError(_('Enter a valid email address'))
        
        return email
    
    def clean_relationship(self):
        """Validate relationship"""
        relationship = self.cleaned_data.get('relationship', '').strip()
        
        if not relationship:
            raise ValidationError(_('Relationship is required'))
        
        # Validate relationship is in allowed choices
        allowed_relationships = ['FATHER', 'MOTHER', 'GUARDIAN', 'OTHER']
        if relationship.upper() not in allowed_relationships:
            raise ValidationError(_('Invalid relationship specified'))
        
        return relationship.upper()
    
    def clean(self):
        """Cross-field validation for guardians"""
        cleaned_data = super().clean()
        
        # Check for duplicate primary guardians
        is_primary = cleaned_data.get('is_primary', False)
        if is_primary and self.student:
            # Check if another primary guardian exists (excluding current instance)
            existing_primary = Guardian.objects.filter(
                student=self.student,
                is_primary=True
            )
            if self.instance and self.instance.pk:
                existing_primary = existing_primary.exclude(pk=self.instance.pk)
            
            if existing_primary.exists():
                self.add_error(
                    'is_primary',
                    _('Only one guardian can be marked as primary')
                )
        
        return cleaned_data


class GuardianBulkForm(forms.Form):
    """
    Form for bulk guardian upload
    Used in CSV/Excel imports
    """
    file = forms.FileField(
        label=_('Guardian Data File'),
        help_text=_('Upload CSV or Excel file with guardian information'),
        widget=forms.FileInput(attrs={
            'accept': '.csv,.xlsx,.xls',
            'class': 'form-control'
        })
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Update existing guardians'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Update guardians if they already exist')
    )
    
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Skip rows with errors'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Continue processing even if some rows have errors')
    )


# ============================================================================
# DOCUMENT FORMS
# ============================================================================

class StudentDocumentForm(SecureStudentForm):
    """
    Secure document upload form with validation
    for file type, size, and metadata
    """
    
    class Meta:
        model = StudentDocument
        fields = ['doc_type', 'file', 'description', 'issue_date', 'expiry_date', 'issuing_authority']
        widgets = {
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': timezone.now().date().isoformat()
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Document description and purpose')
            }),
            'issuing_authority': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Name of issuing authority/organization')
            }),
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'doc_type': _('Type of document being uploaded'),
            'file': _('Upload document (Max 10MB, PDF, JPG, PNG only)'),
            'issue_date': _('Date when document was issued'),
            'expiry_date': _('Document expiry date (if applicable)'),
            'issuing_authority': _('Organization that issued this document'),
        }
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # KEY FIX: Assign student to instance for model validation
        if self.student:
            self.instance.student = self.student
        
        # Set required fields
        required_fields = ['doc_type', 'file']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    def clean_file(self):
        """Enhanced file validation"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError(_('File is required'))
        
        # File size validation (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise ValidationError(
                _('File size must be less than 10MB. Current size: %sMB') % 
                round(file.size / (1024 * 1024), 2)
            )
        
        # File type validation
        allowed_types = [
            'image/jpeg', 'image/png', 'image/jpg',
            'application/pdf', 'image/webp'
        ]
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.webp']
        
        # Check MIME type
        if hasattr(file, 'content_type') and file.content_type not in allowed_types:
            raise ValidationError(
                _('Invalid file type. Allowed types: JPG, PNG, PDF, WEBP')
            )
        
        # Check file extension
        file_name = file.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                _('Invalid file extension. Allowed: .jpg, .jpeg, .png, .pdf, .webp')
            )
        
        # Security check: file content validation
        try:
            # Simple header check for images
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # Read first few bytes to verify it's an image
                file.seek(0)
                header = file.read(100)
                file.seek(0)
                
                # Check for common image headers
                if not (
                    header.startswith(b'\xff\xd8\xff') or  # JPEG
                    header.startswith(b'\x89PNG\r\n\x1a\n') or  # PNG
                    header.startswith(b'RIFF') and b'WEBP' in header  # WEBP
                ):
                    raise ValidationError(_('Invalid image file'))
            
            # PDF validation
            elif file_name.endswith('.pdf'):
                file.seek(0)
                header = file.read(5)
                file.seek(0)
                if not header.startswith(b'%PDF-'):
                    raise ValidationError(_('Invalid PDF file'))
                    
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            raise ValidationError(_('File validation failed. Please upload a valid file.'))
        
        return file
    
    def clean_expiry_date(self):
        """Validate expiry date"""
        issue_date = self.cleaned_data.get('issue_date')
        expiry_date = self.cleaned_data.get('expiry_date')
        
        if issue_date and expiry_date and expiry_date < issue_date:
            raise ValidationError(_('Expiry date cannot be before issue date'))
        
        if expiry_date and expiry_date < timezone.now().date():
            raise ValidationError(_('Document has already expired'))
        
        return expiry_date
    
    def clean(self):
        """Cross-field validation for documents"""
        cleaned_data = super().clean()
        
        doc_type = cleaned_data.get('doc_type')
        file = cleaned_data.get('file')
        
        # Validate file naming based on document type
        if doc_type and file:
            suggested_filename = f"{doc_type}_{timezone.now().strftime('%Y%m%d')}"
            if self.student:
                suggested_filename = f"{self.student.admission_number}_{suggested_filename}"
            
            # You could add filename validation/suggestion here
            cleaned_data['suggested_filename'] = suggested_filename
        
        return cleaned_data


class BulkDocumentUploadForm(forms.Form):
    """
    Form for bulk document upload
    Allows multiple documents for multiple students
    """
    student_ids = forms.CharField(
        required=True,
        label=_('Student IDs'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Comma-separated student IDs or admission numbers')
        }),
        help_text=_('Enter student IDs or admission numbers separated by commas')
    )
    
    doc_type = forms.ChoiceField(
        choices=StudentDocument.DOCUMENT_TYPE_CHOICES,
        label=_('Document Type'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    files = forms.FileField(
        required=True,
        label=_('Document Files'),
        widget=forms.FileInput(attrs={
            # 'multiple': True,
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.webp'
        }),
        help_text=_('Select multiple files (PDF, JPG, PNG, WEBP)')
    )
    
    issue_date = forms.DateField(
        required=False,
        label=_('Issue Date'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    issuing_authority = forms.CharField(
        required=False,
        label=_('Issuing Authority'),
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=200
    )


# ============================================================================
# ADDRESS FORMS
# ============================================================================

class StudentAddressForm(SecureStudentForm):
    """
    Address form with geographic validation
    and multiple address type support
    """
    
    # Address type choices
    ADDRESS_TYPE_CHOICES = [
        ('PERMANENT', _('Permanent Address')),
        ('CORRESPONDENCE', _('Correspondence Address')),
        ('LOCAL_GUARDIAN', _('Local Guardian Address')),
        ('HOSTEL', _('Hostel Address')),
    ]
    
    address_type = forms.ChoiceField(
        choices=ADDRESS_TYPE_CHOICES,
        label=_('Address Type'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = StudentAddress
        exclude = ['student', 'tenant', 'created_at', 'updated_at', 'created_by', 'updated_by']
        widgets = {
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('House number, Street name')
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Area, Locality')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City/Town')
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State/Province')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Country'),
                'value': 'India'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('PIN/ZIP Code'),
                'pattern': '[0-9]{6}'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        required_fields = ['address_line1', 'city', 'state', 'country', 'postal_code']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Set default country
        if 'country' in self.fields and not self.fields['country'].initial:
            self.fields['country'].initial = 'India'
    
    def clean_postal_code(self):
        """Validate postal code"""
        postal_code = self.cleaned_data.get('postal_code', '').strip()
        
        if not postal_code:
            raise ValidationError(_('Postal code is required'))
        
        # Indian PIN code validation (6 digits)
        if len(postal_code) != 6 or not postal_code.isdigit():
            raise ValidationError(_('Enter a valid 6-digit PIN code'))
        
        # First digit cannot be 0
        if postal_code[0] == '0':
            raise ValidationError(_('Invalid PIN code. First digit cannot be 0.'))
        
        return postal_code
    
    def clean(self):
        """Cross-field validation for addresses"""
        cleaned_data = super().clean()
        
        # Validate address type uniqueness
        address_type = cleaned_data.get('address_type')
        is_primary = cleaned_data.get('is_primary', False)
        
        if address_type and self.student:
            # Check for duplicate address type (excluding current instance)
            existing_address = StudentAddress.objects.filter(
                student=self.student,
                address_type=address_type
            )
            if self.instance and self.instance.pk:
                existing_address = existing_address.exclude(pk=self.instance.pk)
            
            if existing_address.exists():
                self.add_error(
                    'address_type',
                    _('An address of this type already exists for the student')
                )
            
            # Check for primary address
            if is_primary:
                existing_primary = StudentAddress.objects.filter(
                    student=self.student,
                    is_primary=True
                )
                if self.instance and self.instance.pk:
                    existing_primary = existing_primary.exclude(pk=self.instance.pk)
                
                if existing_primary.exists():
                    self.add_error(
                        'is_primary',
                        _('Only one address can be marked as primary')
                    )
        
        return cleaned_data


# ============================================================================
# FILTER AND SEARCH FORMS
# ============================================================================

class StudentFilterForm(forms.Form):
    """
    Advanced student filtering form
    Supports complex search queries and filtering
    """
    
    search = forms.CharField(
        required=False,
        label=_('Search'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by name, email, phone, admission number...')
        }),
        help_text=_('Search across multiple fields')
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Status'))] + list(Student.STATUS_CHOICES),
        required=False,
        label=_('Status'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    current_class = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Class'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    section = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Section'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    gender = forms.ChoiceField(
        choices=[('', _('All Genders'))] + list(Student.GENDER_CHOICES),
        required=False,
        label=_('Gender'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=[('', _('All Categories'))] + list(Student.CATEGORY_CHOICES),
        required=False,
        label=_('Category'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    admission_type = forms.ChoiceField(
        choices=[('', _('All Admission Types'))] + list(Student.ADMISSION_TYPE_CHOICES),
        required=False,
        label=_('Admission Type'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_of_birth_from = forms.DateField(
        required=False,
        label=_('Date of Birth From'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_of_birth_to = forms.DateField(
        required=False,
        label=_('Date of Birth To'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    enrollment_date_from = forms.DateField(
        required=False,
        label=_('Enrollment Date From'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    enrollment_date_to = forms.DateField(
        required=False,
        label=_('Enrollment Date To'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    has_guardians = forms.ChoiceField(
        choices=[('', _('All')), ('yes', _('Has Guardians')), ('no', _('No Guardians'))],
        required=False,
        label=_('Guardian Status'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    has_documents = forms.ChoiceField(
        choices=[('', _('All')), ('yes', _('Has Documents')), ('no', _('No Documents'))],
        required=False,
        label=_('Document Status'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('created_at', _('Date Created')),
            ('updated_at', _('Last Updated')),
            ('first_name', _('First Name')),
            ('admission_number', _('Admission Number')),
            ('date_of_birth', _('Date of Birth')),
        ],
        required=False,
        initial='created_at',
        label=_('Sort By'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_order = forms.ChoiceField(
        choices=[('asc', _('Ascending')), ('desc', _('Descending'))],
        required=False,
        initial='desc',
        label=_('Sort Order'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    page_size = forms.ChoiceField(
        choices=[('10', '10'), ('25', '25'), ('50', '50'), ('100', '100')],
        required=False,
        initial='25',
        label=_('Results per page'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            from apps.academics.models import SchoolClass, Section
            self.fields['current_class'].queryset = SchoolClass.objects.filter(
                tenant=tenant,
                is_active=True
            ).order_by('order', 'name')
            self.fields['section'].queryset = Section.objects.filter(
                tenant=tenant,
                is_active=True
            ).order_by('name')
    
    def get_filtered_queryset(self, queryset):
        """Apply filters to queryset"""
        # Search across multiple fields
        search = self.cleaned_data.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(personal_email__icontains=search) |
                models.Q(mobile_primary__icontains=search) |
                models.Q(admission_number__icontains=search) |
                models.Q(roll_number__icontains=search)
            )
        
        # Apply status filter
        status = self.cleaned_data.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply class filter
        current_class = self.cleaned_data.get('current_class')
        if current_class:
            queryset = queryset.filter(current_class=current_class)
        
        # Apply section filter
        section = self.cleaned_data.get('section')
        if section:
            queryset = queryset.filter(section=section)
        
        # Apply gender filter
        gender = self.cleaned_data.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Apply category filter
        category = self.cleaned_data.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Apply admission type filter
        admission_type = self.cleaned_data.get('admission_type')
        if admission_type:
            queryset = queryset.filter(admission_type=admission_type)
        
        # Apply date range filters
        dob_from = self.cleaned_data.get('date_of_birth_from')
        dob_to = self.cleaned_data.get('date_of_birth_to')
        if dob_from:
            queryset = queryset.filter(date_of_birth__gte=dob_from)
        if dob_to:
            queryset = queryset.filter(date_of_birth__lte=dob_to)
        
        enrollment_from = self.cleaned_data.get('enrollment_date_from')
        enrollment_to = self.cleaned_data.get('enrollment_date_to')
        if enrollment_from:
            queryset = queryset.filter(enrollment_date__gte=enrollment_from)
        if enrollment_to:
            queryset = queryset.filter(enrollment_date__lte=enrollment_to)
        
        # Apply guardian status filter
        has_guardians = self.cleaned_data.get('has_guardians')
        if has_guardians == 'yes':
            queryset = queryset.filter(guardians__isnull=False).distinct()
        elif has_guardians == 'no':
            queryset = queryset.filter(guardians__isnull=True)
        
        # Apply document status filter
        has_documents = self.cleaned_data.get('has_documents')
        if has_documents == 'yes':
            queryset = queryset.filter(documents__isnull=False).distinct()
        elif has_documents == 'no':
            queryset = queryset.filter(documents__isnull=True)
        
        # Apply sorting
        sort_by = self.cleaned_data.get('sort_by', 'created_at')
        sort_order = self.cleaned_data.get('sort_order', 'desc')
        
        if sort_order == 'desc':
            sort_by = f'-{sort_by}'
        
        queryset = queryset.order_by(sort_by)
        
        return queryset


class StudentBulkActionForm(forms.Form):
    """
    Form for bulk actions on students
    (Delete, Export, Change Status, etc.)
    """
    ACTION_CHOICES = [
        ('', _('Select Action')),
        ('export', _('Export Selected')),
        ('change_status', _('Change Status')),
        ('change_class', _('Change Class')),
        ('send_email', _('Send Email')),
        ('send_sms', _('Send SMS')),
        ('generate_id_cards', _('Generate ID Cards')),
        ('generate_reports', _('Generate Reports')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label=_('Bulk Action'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleActionFields(this)'
        })
    )
    
    student_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Fields for change_status action
    new_status = forms.ChoiceField(
        choices=[('', _('Select Status'))] + list(Student.STATUS_CHOICES),
        required=False,
        label=_('New Status'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status_reason = forms.CharField(
        required=False,
        label=_('Reason for Status Change'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Reason for changing student status')
        })
    )
    
    # Fields for change_class action
    new_class = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('New Class'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    new_section = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('New Section'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Fields for email/sms actions
    subject = forms.CharField(
        required=False,
        label=_('Email Subject'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    message = forms.CharField(
        required=False,
        label=_('Message'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Enter your message here...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            from apps.academics.models import SchoolClass, Section
            self.fields['new_class'].queryset = SchoolClass.objects.filter(
                tenant=tenant,
                is_active=True
            )
            self.fields['new_section'].queryset = Section.objects.filter(
                tenant=tenant,
                is_active=True
            )
    
    def clean(self):
        """Validate bulk action form"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if action == 'change_status':
            if not cleaned_data.get('new_status'):
                self.add_error('new_status', _('This field is required for status change'))
            if not cleaned_data.get('status_reason'):
                self.add_error('status_reason', _('Please provide a reason for status change'))
        
        elif action == 'change_class':
            if not cleaned_data.get('new_class'):
                self.add_error('new_class', _('This field is required for class change'))
        
        elif action in ['send_email', 'send_sms']:
            if not cleaned_data.get('message'):
                self.add_error('message', _('Message is required'))
            if action == 'send_email' and not cleaned_data.get('subject'):
                self.add_error('subject', _('Subject is required for emails'))
        
        return cleaned_data


class StudentBulkUploadForm(forms.Form):
    """
    Bulk upload students via CSV or Excel
    """
    file = forms.FileField(
        label=_('Student Data File'),
        help_text=_('Upload CSV or Excel file with student details'),
        widget=forms.FileInput(attrs={
            'accept': '.csv,.xlsx,.xls',
            'class': 'form-control'
        })
    )

    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Update existing students'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Skip rows with errors'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class StudentPromotionForm(forms.Form):
    """
    Form for promoting students to next class / academic year
    """

    student_ids = forms.CharField(
        label=_('Students'),
        widget=forms.HiddenInput(),
        help_text=_('Comma-separated student IDs')
    )

    from_academic_year = forms.ModelChoiceField(
        queryset=None,
        label=_('From Academic Year'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    to_academic_year = forms.ModelChoiceField(
        queryset=None,
        label=_('To Academic Year'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    from_class = forms.ModelChoiceField(
        queryset=None,
        label=_('Current Class'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    to_class = forms.ModelChoiceField(
        queryset=None,
        label=_('Promote To Class'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    to_section = forms.ModelChoiceField(
        queryset=None,
        label=_('Promote To Section'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    promotion_type = forms.ChoiceField(
        choices=[
            ('PROMOTED', _('Promoted')),
            ('RETAINED', _('Retained / Same Class')),
        ],
        label=_('Promotion Type'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='PROMOTED'
    )

    remarks = forms.CharField(
        required=False,
        label=_('Remarks'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Optional remarks for promotion')
        })
    )

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        if not self.tenant:
            return

        from apps.academics.models import AcademicYear, SchoolClass, Section

        self.fields['from_academic_year'].queryset = AcademicYear.objects.filter(
            tenant=self.tenant
        ).order_by('-start_date')

        self.fields['to_academic_year'].queryset = AcademicYear.objects.filter(
            tenant=self.tenant
        ).order_by('-start_date')

        self.fields['from_class'].queryset = SchoolClass.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).order_by('order')

        self.fields['to_class'].queryset = SchoolClass.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).order_by('order')

        self.fields['to_section'].queryset = Section.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).order_by('name')

    def clean_student_ids(self):
        raw = self.cleaned_data.get('student_ids', '')
        ids = [s.strip() for s in raw.split(',') if s.strip().isdigit()]

        if not ids:
            raise ValidationError(_('No students selected for promotion'))

        return ids

    def clean(self):
        cleaned_data = super().clean()

        from_class = cleaned_data.get('from_class')
        to_class = cleaned_data.get('to_class')
        from_year = cleaned_data.get('from_academic_year')
        to_year = cleaned_data.get('to_academic_year')
        promotion_type = cleaned_data.get('promotion_type')
        to_section = cleaned_data.get('to_section')

        # Academic year validation
        if from_year and to_year and from_year == to_year:
            self.add_error(
                'to_academic_year',
                _('Promotion academic year must be different')
            )

        # Class validation
        if promotion_type == 'PROMOTED' and from_class and to_class:
            if from_class == to_class:
                self.add_error(
                    'to_class',
                    _('Promoted class must be different from current class')
                )

        # Section belongs to class
        if to_class and to_section:
            if not to_class.sections.filter(id=to_section.id).exists():
                self.add_error(
                    'to_section',
                    _('Selected section does not belong to the selected class')
                )

        return cleaned_data

class StudentImportForm(forms.Form):
    """
    Import students using CSV / Excel
    """

    file = forms.FileField(
        label=_('Student Data File'),
        help_text=_('Upload CSV or Excel file (.csv, .xlsx, .xls)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )

    academic_year = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label=_('Academic Year'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    default_class = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Default Class'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('Used if class column is missing in file')
    )

    default_section = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Default Section'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('Used if section column is missing in file')
    )

    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Update existing students'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Match by admission number / email / mobile')
    )

    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Skip rows with errors'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Continue import even if some rows fail')
    )

    send_welcome_notification = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Send welcome notification'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Send email/SMS after successful import')
    )

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        if not self.tenant:
            return

        from apps.academics.models import AcademicYear, SchoolClass, Section

        self.fields['academic_year'].queryset = AcademicYear.objects.filter(
            tenant=self.tenant
        ).order_by('-start_date')

        self.fields['default_class'].queryset = SchoolClass.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).order_by('order')

        self.fields['default_section'].queryset = Section.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).order_by('name')

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError(_('File is required'))

        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise ValidationError(_('File size must be under 10MB'))

        allowed_extensions = ('.csv', '.xlsx', '.xls')
        if not file.name.lower().endswith(allowed_extensions):
            raise ValidationError(_('Only CSV or Excel files are allowed'))

        return file

    def clean(self):
        cleaned_data = super().clean()

        default_class = cleaned_data.get('default_class')
        default_section = cleaned_data.get('default_section')

        if default_class and default_section:
            if not default_class.sections.filter(id=default_section.id).exists():
                self.add_error(
                    'default_section',
                    _('Selected section does not belong to selected class')
                )

        return cleaned_data
