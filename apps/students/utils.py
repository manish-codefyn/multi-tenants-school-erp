# ============================================================================
# VALIDATION UTILITY FUNCTIONS
# ============================================================================

def validate_student_data(data, tenant, instance=None):
    """
    Utility function to validate student data
    Used in bulk uploads and API endpoints
    """
    errors = {}
    warnings = []
    
    # Required fields validation
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
    for field in required_fields:
        if not data.get(field):
            errors[field] = _('This field is required')
    
    # Email validation
    email = data.get('personal_email', '').strip().lower()
    if email:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['personal_email'] = _('Invalid email format')
        else:
            # Check for duplicates
            qs = Student.objects.filter(tenant=tenant, personal_email=email)
            if instance and instance.pk:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                errors['personal_email'] = _('Email already exists')
    
    # Phone validation
    phone = data.get('mobile_primary', '').strip()
    if phone:
        digits = re.sub(r'\D', '', phone)
        if len(digits) not in [10, 11, 12]:
            errors['mobile_primary'] = _('Invalid phone number')
    
    # Date validation
    dob = data.get('date_of_birth')
    if dob:
        try:
            dob_date = timezone.datetime.strptime(str(dob), '%Y-%m-%d').date()
            if dob_date > timezone.now().date():
                errors['date_of_birth'] = _('Date cannot be in future')
        except ValueError:
            errors['date_of_birth'] = _('Invalid date format')
    
    return errors, warnings


def generate_admission_number(tenant, year=None):
    """
    Generate a unique admission number for a student
    Format: INST-YYYY-XXXXX
    """
    if not year:
        year = timezone.now().year
    
    # Get institution code from tenant
    inst_code = tenant.code if hasattr(tenant, 'code') else 'INST'
    
    # Find the last admission number for this year
    last_student = Student.objects.filter(
        tenant=tenant,
        admission_number__startswith=f"{inst_code}-{year}-"
    ).order_by('-admission_number').first()
    
    if last_student:
        try:
            last_number = int(last_student.admission_number.split('-')[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    # Format with leading zeros
    return f"{inst_code}-{year}-{next_number:05d}"