"""
Constants for Student Management Module
Contains all constants, enums, and configuration values used throughout the student app.
"""

from django.utils.translation import gettext_lazy as _

# ============================================================================
# STUDENT STATUS CONSTANTS
# ============================================================================

class StudentStatus:
    """
    Student status constants and choices
    """
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    GRADUATED = 'GRADUATED'
    SUSPENDED = 'SUSPENDED'
    TRANSFERRED = 'TRANSFERRED'
    WITHDRAWN = 'WITHDRAWN'
    DECEASED = 'DECEASED'
    
    CHOICES = (
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
        (GRADUATED, _('Graduated')),
        (SUSPENDED, _('Suspended')),
        (TRANSFERRED, _('Transferred')),
        (WITHDRAWN, _('Withdrawn')),
        (DECEASED, _('Deceased')),
    )
    
    # Status groups
    ACTIVE_STATUSES = [ACTIVE]
    INACTIVE_STATUSES = [INACTIVE, SUSPENDED, WITHDRAWN]
    COMPLETED_STATUSES = [GRADUATED, TRANSFERRED, DECEASED]
    
    # Status transitions (from -> to)
    ALLOWED_TRANSITIONS = {
        ACTIVE: [INACTIVE, SUSPENDED, GRADUATED, TRANSFERRED, WITHDRAWN, DECEASED],
        INACTIVE: [ACTIVE, SUSPENDED, GRADUATED, TRANSFERRED, WITHDRAWN, DECEASED],
        SUSPENDED: [ACTIVE, INACTIVE, WITHDRAWN, DECEASED],
        GRADUATED: [],  # Final state
        TRANSFERRED: [],  # Final state
        WITHDRAWN: [],  # Final state
        DECEASED: [],  # Final state
    }


# ============================================================================
# STUDENT GENDER CONSTANTS
# ============================================================================

class StudentGender:
    """
    Student gender constants and choices
    """
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    NOT_SPECIFIED = 'N'
    
    CHOICES = (
        (MALE, _('Male')),
        (FEMALE, _('Female')),
        (OTHER, _('Other')),
        (NOT_SPECIFIED, _('Not Specified')),
    )
    
    # Display mapping
    DISPLAY_MAP = dict(CHOICES)


# ============================================================================
# STUDENT CATEGORY CONSTANTS
# ============================================================================

class StudentCategory:
    """
    Student category constants (for reservations/caste)
    """
    GENERAL = 'GENERAL'
    OBC = 'OBC'
    SC = 'SC'
    ST = 'ST'
    OTHER = 'OTHER'
    NOT_APPLICABLE = 'NA'
    
    CHOICES = (
        (GENERAL, _('General')),
        (OBC, _('Other Backward Class')),
        (SC, _('Scheduled Caste')),
        (ST, _('Scheduled Tribe')),
        (OTHER, _('Other')),
        (NOT_APPLICABLE, _('Not Applicable')),
    )
    
    # Category codes for reporting
    CODES = {
        GENERAL: 'GEN',
        OBC: 'OBC',
        SC: 'SC',
        ST: 'ST',
        OTHER: 'OTH',
        NOT_APPLICABLE: 'NA'
    }


# ============================================================================
# ADMISSION TYPE CONSTANTS
# ============================================================================

class AdmissionType:
    """
    Student admission type constants
    """
    REGULAR = 'REGULAR'
    TRANSFER = 'TRANSFER'
    MANAGEMENT = 'MANAGEMENT'
    NRI = 'NRI'
    SPORTS = 'SPORTS'
    DEFENCE = 'DEFENCE'
    OTHER = 'OTHER'
    
    CHOICES = (
        (REGULAR, _('Regular Admission')),
        (TRANSFER, _('Transfer Admission')),
        (MANAGEMENT, _('Management Quota')),
        (NRI, _('NRI Quota')),
        (SPORTS, _('Sports Quota')),
        (DEFENCE, _('Defence Quota')),
        (OTHER, _('Other')),
    )
    
    # Fee categories
    FEE_CATEGORIES = {
        REGULAR: 'STANDARD',
        TRANSFER: 'STANDARD',
        MANAGEMENT: 'PREMIUM',
        NRI: 'PREMIUM',
        SPORTS: 'CONCESSIONAL',
        DEFENCE: 'CONCESSIONAL',
        OTHER: 'STANDARD'
    }


# ============================================================================
# BLOOD GROUP CONSTANTS
# ============================================================================

class BloodGroup:
    """
    Blood group constants
    """
    A_POSITIVE = 'A+'
    A_NEGATIVE = 'A-'
    B_POSITIVE = 'B+'
    B_NEGATIVE = 'B-'
    O_POSITIVE = 'O+'
    O_NEGATIVE = 'O-'
    AB_POSITIVE = 'AB+'
    AB_NEGATIVE = 'AB-'
    UNKNOWN = 'UNKNOWN'
    
    CHOICES = (
        (A_POSITIVE, _('A+')),
        (A_NEGATIVE, _('A-')),
        (B_POSITIVE, _('B+')),
        (B_NEGATIVE, _('B-')),
        (O_POSITIVE, _('O+')),
        (O_NEGATIVE, _('O-')),
        (AB_POSITIVE, _('AB+')),
        (AB_NEGATIVE, _('AB-')),
        (UNKNOWN, _('Unknown')),
    )
    
    # Blood group compatibility
    COMPATIBILITY = {
        A_POSITIVE: ['A+', 'A-', 'O+', 'O-'],
        A_NEGATIVE: ['A-', 'O-'],
        B_POSITIVE: ['B+', 'B-', 'O+', 'O-'],
        B_NEGATIVE: ['B-', 'O-'],
        O_POSITIVE: ['O+', 'O-'],
        O_NEGATIVE: ['O-'],
        AB_POSITIVE: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        AB_NEGATIVE: ['A-', 'B-', 'AB-', 'O-'],
    }


# ============================================================================
# RELIGION CONSTANTS
# ============================================================================

class Religion:
    """
    Religion constants
    """
    HINDU = 'HINDU'
    MUSLIM = 'MUSLIM'
    CHRISTIAN = 'CHRISTIAN'
    SIKH = 'SIKH'
    BUDDHIST = 'BUDDHIST'
    JAIN = 'JAIN'
    OTHER = 'OTHER'
    NOT_SPECIFIED = 'NOT_SPECIFIED'
    
    CHOICES = (
        (HINDU, _('Hindu')),
        (MUSLIM, _('Muslim')),
        (CHRISTIAN, _('Christian')),
        (SIKH, _('Sikh')),
        (BUDDHIST, _('Buddhist')),
        (JAIN, _('Jain')),
        (OTHER, _('Other')),
        (NOT_SPECIFIED, _('Not Specified')),
    )


# ============================================================================
# NATIONALITY CONSTANTS
# ============================================================================

class Nationality:
    """
    Nationality constants (commonly used)
    """
    INDIAN = 'INDIAN'
    NRI = 'NRI'
    OTHER = 'OTHER'
    
    CHOICES = (
        (INDIAN, _('Indian')),
        (NRI, _('Non-Resident Indian')),
        (OTHER, _('Other')),
    )
    
    # Country codes
    COUNTRY_CODES = {
        'INDIAN': 'IN',
        'NRI': 'IN',  # NRI is still Indian nationality
        'OTHER': 'XX'
    }


# ============================================================================
# GUARDIAN RELATIONSHIP CONSTANTS
# ============================================================================

class GuardianRelationship:
    """
    Guardian relationship constants
    """
    FATHER = 'FATHER'
    MOTHER = 'MOTHER'
    GUARDIAN = 'GUARDIAN'
    GRANDFATHER = 'GRANDFATHER'
    GRANDMOTHER = 'GRANDMOTHER'
    UNCLE = 'UNCLE'
    AUNT = 'AUNT'
    BROTHER = 'BROTHER'
    SISTER = 'SISTER'
    OTHER = 'OTHER'
    
    CHOICES = (
        (FATHER, _('Father')),
        (MOTHER, _('Mother')),
        (GUARDIAN, _('Guardian')),
        (GRANDFATHER, _('Grandfather')),
        (GRANDMOTHER, _('Grandmother')),
        (UNCLE, _('Uncle')),
        (AUNT, _('Aunt')),
        (BROTHER, _('Brother')),
        (SISTER, _('Sister')),
        (OTHER, _('Other Relative')),
    )
    
    # Primary relationships (for emergency contact priority)
    PRIMARY_RELATIONSHIPS = [FATHER, MOTHER, GUARDIAN]


# ============================================================================
# DOCUMENT TYPE CONSTANTS
# ============================================================================

class DocumentType:
    """
    Student document type constants
    """
    # Required Documents
    PHOTO = 'PHOTO'
    BIRTH_CERTIFICATE = 'BIRTH_CERTIFICATE'
    ADDRESS_PROOF = 'ADDRESS_PROOF'
    AADHAR_CARD = 'AADHAR_CARD'
    
    # Academic Documents
    PREVIOUS_MARKSHEET = 'PREVIOUS_MARKSHEET'
    TRANSFER_CERTIFICATE = 'TRANSFER_CERTIFICATE'
    CHARACTER_CERTIFICATE = 'CHARACTER_CERTIFICATE'
    MIGRATION_CERTIFICATE = 'MIGRATION_CERTIFICATE'
    
    # Category Documents
    CASTE_CERTIFICATE = 'CASTE_CERTIFICATE'
    INCOME_CERTIFICATE = 'INCOME_CERTIFICATE'
    DISABILITY_CERTIFICATE = 'DISABILITY_CERTIFICATE'
    
    # Medical Documents
    MEDICAL_CERTIFICATE = 'MEDICAL_CERTIFICATE'
    BLOOD_GROUP_REPORT = 'BLOOD_GROUP_REPORT'
    
    # Other Documents
    PASSPORT_PHOTO = 'PASSPORT_PHOTO'
    SIGNATURE = 'SIGNATURE'
    OTHER = 'OTHER'
    
    CHOICES = (
        # Required Documents
        (PHOTO, _('Student Photo')),
        (BIRTH_CERTIFICATE, _('Birth Certificate')),
        (ADDRESS_PROOF, _('Address Proof')),
        (AADHAR_CARD, _('Aadhar Card')),
        
        # Academic Documents
        (PREVIOUS_MARKSHEET, _('Previous Marksheet')),
        (TRANSFER_CERTIFICATE, _('Transfer Certificate')),
        (CHARACTER_CERTIFICATE, _('Character Certificate')),
        (MIGRATION_CERTIFICATE, _('Migration Certificate')),
        
        # Category Documents
        (CASTE_CERTIFICATE, _('Caste Certificate')),
        (INCOME_CERTIFICATE, _('Income Certificate')),
        (DISABILITY_CERTIFICATE, _('Disability Certificate')),
        
        # Medical Documents
        (MEDICAL_CERTIFICATE, _('Medical Certificate')),
        (BLOOD_GROUP_REPORT, _('Blood Group Report')),
        
        # Other Documents
        (PASSPORT_PHOTO, _('Passport Size Photo')),
        (SIGNATURE, _('Signature')),
        (OTHER, _('Other Document')),
    )
    
    # Required documents for admission
    REQUIRED_FOR_ADMISSION = [
        PHOTO,
        BIRTH_CERTIFICATE,
        ADDRESS_PROOF,
        AADHAR_CARD,
    ]
    
    # Document categories
    CATEGORIES = {
        'REQUIRED': REQUIRED_FOR_ADMISSION,
        'ACADEMIC': [
            PREVIOUS_MARKSHEET,
            TRANSFER_CERTIFICATE,
            CHARACTER_CERTIFICATE,
            MIGRATION_CERTIFICATE,
        ],
        'CATEGORY': [
            CASTE_CERTIFICATE,
            INCOME_CERTIFICATE,
            DISABILITY_CERTIFICATE,
        ],
        'MEDICAL': [
            MEDICAL_CERTIFICATE,
            BLOOD_GROUP_REPORT,
        ],
        'OTHER': [
            PASSPORT_PHOTO,
            SIGNATURE,
            OTHER,
        ]
    }
    
    # File extensions allowed for each document type
    ALLOWED_EXTENSIONS = {
        PHOTO: ['.jpg', '.jpeg', '.png'],
        BIRTH_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        ADDRESS_PROOF: ['.pdf', '.jpg', '.jpeg', '.png'],
        AADHAR_CARD: ['.pdf', '.jpg', '.jpeg', '.png'],
        PREVIOUS_MARKSHEET: ['.pdf', '.jpg', '.jpeg', '.png'],
        TRANSFER_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        CHARACTER_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        MIGRATION_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        CASTE_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        INCOME_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        DISABILITY_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        MEDICAL_CERTIFICATE: ['.pdf', '.jpg', '.jpeg', '.png'],
        BLOOD_GROUP_REPORT: ['.pdf', '.jpg', '.jpeg', '.png'],
        PASSPORT_PHOTO: ['.jpg', '.jpeg', '.png'],
        SIGNATURE: ['.jpg', '.jpeg', '.png'],
        OTHER: ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
    }
    
    # Maximum file sizes in MB for each document type
    MAX_FILE_SIZES_MB = {
        PHOTO: 2,  # 2MB for photos
        BIRTH_CERTIFICATE: 5,
        ADDRESS_PROOF: 5,
        AADHAR_CARD: 5,
        PREVIOUS_MARKSHEET: 10,
        TRANSFER_CERTIFICATE: 10,
        CHARACTER_CERTIFICATE: 5,
        MIGRATION_CERTIFICATE: 5,
        CASTE_CERTIFICATE: 5,
        INCOME_CERTIFICATE: 5,
        DISABILITY_CERTIFICATE: 5,
        MEDICAL_CERTIFICATE: 5,
        BLOOD_GROUP_REPORT: 2,
        PASSPORT_PHOTO: 2,
        SIGNATURE: 1,
        OTHER: 20,
    }


# ============================================================================
# BULK UPLOAD CONSTANTS
# ============================================================================

class BulkUpload:
    """
    Bulk upload constants
    """
    # File size limits
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE_MB = 10
    
    # Allowed file formats
    ALLOWED_FORMATS = ['csv', 'xls', 'xlsx']
    
    # Required fields in upload file
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Optional fields with validation
    OPTIONAL_FIELDS = [
        'middle_name',
        'date_of_birth',
        'gender',
        'personal_email',
        'mobile_primary',
        'mobile_secondary',
        'class_name',
        'section_name',
        'status',
        'category',
        'blood_group',
        'nationality',
        'religion',
        'caste',
        'admission_type',
        'father_name',
        'father_phone',
        'father_email',
        'father_occupation',
        'mother_name',
        'mother_phone',
        'mother_email',
        'mother_occupation',
        'guardian_name',
        'guardian_relationship',
        'guardian_phone',
        'guardian_email',
        'guardian_occupation',
    ]
    
    # Field mappings (CSV header -> model field)
    FIELD_MAPPINGS = {
        # Student fields
        'firstname': 'first_name',
        'first name': 'first_name',
        'first': 'first_name',
        'lastname': 'last_name',
        'last name': 'last_name',
        'last': 'last_name',
        'middlename': 'middle_name',
        'middle name': 'middle_name',
        'middle': 'middle_name',
        'fullname': 'full_name',
        'full name': 'full_name',
        'name': 'full_name',
        'dob': 'date_of_birth',
        'date of birth': 'date_of_birth',
        'birthdate': 'date_of_birth',
        'birth date': 'date_of_birth',
        'gender': 'gender',
        'sex': 'gender',
        'email': 'personal_email',
        'e-mail': 'personal_email',
        'mail': 'personal_email',
        'phone': 'mobile_primary',
        'mobile': 'mobile_primary',
        'contact': 'mobile_primary',
        'phone number': 'mobile_primary',
        'mobile number': 'mobile_primary',
        'contact number': 'mobile_primary',
        'secondary phone': 'mobile_secondary',
        'secondary mobile': 'mobile_secondary',
        'alt phone': 'mobile_secondary',
        'alternate phone': 'mobile_secondary',
        'class': 'class_name',
        'grade': 'class_name',
        'standard': 'class_name',
        'section': 'section_name',
        'division': 'section_name',
        'group': 'section_name',
        'status': 'status',
        'student status': 'status',
        'category': 'category',
        'caste category': 'category',
        'reservation': 'category',
        'blood group': 'blood_group',
        'blood type': 'blood_group',
        'blood': 'blood_group',
        'nationality': 'nationality',
        'country': 'nationality',
        'religion': 'religion',
        'faith': 'religion',
        'caste': 'caste',
        'community': 'caste',
        'admission type': 'admission_type',
        'admission category': 'admission_type',
        'quota': 'admission_type',
        
        # Guardian fields
        'father name': 'father_name',
        'father': 'father_name',
        'father phone': 'father_phone',
        'father mobile': 'father_phone',
        'father contact': 'father_phone',
        'father email': 'father_email',
        'father e-mail': 'father_email',
        'father occupation': 'father_occupation',
        'father job': 'father_occupation',
        'mother name': 'mother_name',
        'mother': 'mother_name',
        'mother phone': 'mother_phone',
        'mother mobile': 'mother_phone',
        'mother contact': 'mother_phone',
        'mother email': 'mother_email',
        'mother e-mail': 'mother_email',
        'mother occupation': 'mother_occupation',
        'mother job': 'mother_occupation',
        'guardian name': 'guardian_name',
        'guardian': 'guardian_name',
        'local guardian': 'guardian_name',
        'guardian relationship': 'guardian_relationship',
        'guardian relation': 'guardian_relationship',
        'relation': 'guardian_relationship',
        'guardian phone': 'guardian_phone',
        'guardian mobile': 'guardian_phone',
        'guardian contact': 'guardian_phone',
        'guardian email': 'guardian_email',
        'guardian e-mail': 'guardian_email',
        'guardian occupation': 'guardian_occupation',
        'guardian job': 'guardian_occupation',
    }
    
    # Validation rules for fields
    VALIDATION_RULES = {
        'first_name': {
            'required': True,
            'min_length': 2,
            'max_length': 50,
            'regex': r'^[a-zA-Z\s\.\-]+$'
        },
        'last_name': {
            'required': True,
            'min_length': 1,
            'max_length': 50,
            'regex': r'^[a-zA-Z\s\.\-]+$'
        },
        'personal_email': {
            'required': False,
            'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'unique': True
        },
        'mobile_primary': {
            'required': False,
            'regex': r'^\+?1?\d{9,15}$',
            'min_length': 10,
            'max_length': 15
        },
        'date_of_birth': {
            'required': False,
            'format': ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y'],
            'min_age': 3,
            'max_age': 25
        },
        'gender': {
            'required': False,
            'allowed_values': ['M', 'F', 'O', 'N']
        },
        'status': {
            'required': False,
            'allowed_values': ['ACTIVE', 'INACTIVE', 'GRADUATED', 'SUSPENDED', 'TRANSFERRED', 'WITHDRAWN']
        },
        'category': {
            'required': False,
            'allowed_values': ['GENERAL', 'OBC', 'SC', 'ST', 'OTHER', 'NA']
        },
        'blood_group': {
            'required': False,
            'allowed_values': ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-', 'UNKNOWN']
        },
    }
    
    # Sample CSV headers for download
    SAMPLE_CSV_HEADERS_SIMPLE = [
        'first_name',
        'last_name',
        'personal_email',
        'mobile_primary',
        'class_name',
        'section_name',
        'gender',
        'date_of_birth',
    ]
    
    SAMPLE_CSV_HEADERS_DETAILED = [
        'first_name',
        'middle_name',
        'last_name',
        'date_of_birth',
        'gender',
        'personal_email',
        'mobile_primary',
        'mobile_secondary',
        'class_name',
        'section_name',
        'status',
        'category',
        'blood_group',
        'nationality',
        'religion',
        'caste',
        'admission_type',
        'father_name',
        'father_phone',
        'father_email',
        'father_occupation',
        'mother_name',
        'mother_phone',
        'mother_email',
        'mother_occupation',
        'guardian_name',
        'guardian_relationship',
        'guardian_phone',
        'guardian_email',
        'guardian_occupation',
    ]
    
    # Sample data for templates
    SAMPLE_DATA_SIMPLE = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'personal_email': 'john.doe@example.com',
            'mobile_primary': '9876543210',
            'class_name': 'Class 1',
            'section_name': 'A',
            'gender': 'M',
            'date_of_birth': '2010-01-15',
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'personal_email': 'jane.smith@example.com',
            'mobile_primary': '9876543211',
            'class_name': 'Class 2',
            'section_name': 'B',
            'gender': 'F',
            'date_of_birth': '2010-05-20',
        },
    ]
    
    SAMPLE_DATA_DETAILED = [
        {
            'first_name': 'Rahul',
            'middle_name': 'Kumar',
            'last_name': 'Sharma',
            'date_of_birth': '2010-03-10',
            'gender': 'M',
            'personal_email': 'rahul.sharma@example.com',
            'mobile_primary': '9876543212',
            'mobile_secondary': '9876543213',
            'class_name': 'Class 3',
            'section_name': 'C',
            'status': 'ACTIVE',
            'category': 'GENERAL',
            'blood_group': 'O+',
            'nationality': 'INDIAN',
            'religion': 'HINDU',
            'caste': 'General',
            'admission_type': 'REGULAR',
            'father_name': 'Rajesh Sharma',
            'father_phone': '9876543214',
            'father_email': 'rajesh.sharma@example.com',
            'father_occupation': 'Engineer',
            'mother_name': 'Priya Sharma',
            'mother_phone': '9876543215',
            'mother_email': 'priya.sharma@example.com',
            'mother_occupation': 'Teacher',
            'guardian_name': 'Rajesh Sharma',
            'guardian_relationship': 'FATHER',
            'guardian_phone': '9876543214',
            'guardian_email': 'rajesh.sharma@example.com',
            'guardian_occupation': 'Engineer',
        },
    ]


# ============================================================================
# EXPORT CONSTANTS
# ============================================================================

class ExportFormat:
    """
    Export format constants
    """
    CSV = 'csv'
    EXCEL = 'excel'
    PDF = 'pdf'
    
    CHOICES = (
        (CSV, _('CSV File')),
        (EXCEL, _('Excel File')),
        (PDF, _('PDF Document')),
    )
    
    # MIME types
    MIME_TYPES = {
        CSV: 'text/csv',
        EXCEL: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        PDF: 'application/pdf',
    }
    
    # File extensions
    FILE_EXTENSIONS = {
        CSV: '.csv',
        EXCEL: '.xlsx',
        PDF: '.pdf',
    }


class ExportType:
    """
    Export type constants (level of detail)
    """
    BASIC = 'basic'
    DETAILED = 'detailed'
    COMPREHENSIVE = 'comprehensive'
    
    CHOICES = (
        (BASIC, _('Basic Information')),
        (DETAILED, _('Detailed Information')),
        (COMPREHENSIVE, _('Comprehensive Report')),
    )
    
    # Fields included in each export type
    FIELDS = {
        BASIC: [
            'admission_number',
            'full_name',
            'date_of_birth',
            'gender',
            'personal_email',
            'mobile_primary',
            'current_class',
            'section',
            'status',
            'category',
        ],
        DETAILED: [
            'admission_number',
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'age',
            'gender',
            'personal_email',
            'mobile_primary',
            'mobile_secondary',
            'current_class',
            'section',
            'stream',
            'academic_year',
            'status',
            'category',
            'blood_group',
            'nationality',
            'religion',
            'caste',
            'admission_date',
            'admission_type',
            'created_at',
            'updated_at',
        ],
        COMPREHENSIVE: [
            'admission_number',
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'date_of_birth',
            'age',
            'gender',
            'personal_email',
            'mobile_primary',
            'mobile_secondary',
            'current_class',
            'section',
            'stream',
            'academic_year',
            'status',
            'category',
            'blood_group',
            'nationality',
            'religion',
            'caste',
            'admission_date',
            'admission_type',
            'profile_picture_url',
            'created_at',
            'updated_at',
            # Guardian information
            'guardian_names',
            'guardian_emails',
            'guardian_phones',
            'guardian_relationships',
            # Address information
            'address_line1',
            'address_line2',
            'city',
            'state',
            'pincode',
            'country',
            # Document information
            'documents_count',
            'verified_documents_count',
            # Academic history
            'academic_history_count',
        ]
    }


# ============================================================================
# VALIDATION MESSAGES
# ============================================================================

class ValidationMessages:
    """
    Standard validation messages
    """
    # Common messages
    REQUIRED_FIELD = _('This field is required.')
    INVALID_EMAIL = _('Enter a valid email address.')
    INVALID_PHONE = _('Enter a valid phone number.')
    INVALID_DATE = _('Enter a valid date in YYYY-MM-DD format.')
    UNIQUE_EMAIL = _('A student with this email already exists.')
    UNIQUE_ADMISSION_NUMBER = _('Admission number already exists.')
    
    # Student-specific messages
    MIN_AGE = _('Student must be at least {age} years old.')
    MAX_AGE = _('Student cannot be older than {age} years.')
    INVALID_GENDER = _('Invalid gender value.')
    INVALID_STATUS = _('Invalid status value.')
    INVALID_CATEGORY = _('Invalid category value.')
    INVALID_BLOOD_GROUP = _('Invalid blood group value.')
    
    # File upload messages
    FILE_TOO_LARGE = _('File size exceeds maximum allowed size of {size}MB.')
    INVALID_FILE_TYPE = _('Invalid file type. Allowed types: {types}.')
    INVALID_FILE_NAME = _('File name contains invalid characters.')
    FILE_REQUIRED = _('Please select a file to upload.')
    
    # Bulk upload messages
    INVALID_CSV_FORMAT = _('Invalid CSV file format.')
    MISSING_REQUIRED_COLUMNS = _('Missing required columns: {columns}.')
    DUPLICATE_EMAIL = _('Duplicate email found at row {row}: {email}.')
    DUPLICATE_PHONE = _('Duplicate phone number found at row {row}: {phone}.')
    INVALID_CLASS = _('Invalid class name at row {row}: {class_name}.')
    INVALID_SECTION = _('Invalid section name at row {row}: {section_name}.')
    
    # Document validation messages
    DOCUMENT_REQUIRED = _('{document_type} is required for admission.')
    DOCUMENT_EXPIRED = _('{document_type} has expired.')
    DOCUMENT_VERIFICATION_FAILED = _('{document_type} verification failed.')


# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

class SystemConfig:
    """
    System configuration constants
    """
    # Pagination
    DEFAULT_PAGE_SIZE = 25
    PAGE_SIZE_OPTIONS = [10, 25, 50, 100]
    
    # Cache timeouts (in seconds)
    CACHE_TIMEOUT_STUDENT_LIST = 300  # 5 minutes
    CACHE_TIMEOUT_STUDENT_STATS = 600  # 10 minutes
    CACHE_TIMEOUT_CLASS_LIST = 1800  # 30 minutes
    
    # Rate limiting
    RATE_LIMIT_STUDENT_CREATE = '10/minute'
    RATE_LIMIT_BULK_UPLOAD = '2/hour'
    RATE_LIMIT_EXPORT = '5/minute'
    
    # Default values
    DEFAULT_ACADEMIC_YEAR = None  # Will use current academic year
    DEFAULT_STATUS = StudentStatus.ACTIVE
    DEFAULT_CATEGORY = StudentCategory.GENERAL
    DEFAULT_GENDER = StudentGender.NOT_SPECIFIED
    
    # Age limits
    MIN_AGE_YEARS = 3
    MAX_AGE_YEARS = 25
    
    # Admission number format
    ADMISSION_NUMBER_FORMAT = '{tenant_code}/{year_code}/{sequence:05d}'
    ADMISSION_NUMBER_PREFIX = 'ADM'
    
    # Search settings
    SEARCH_MIN_CHARS = 2
    SEARCH_MAX_RESULTS = 20
    SEARCH_FIELDS = [
        'admission_number',
        'first_name',
        'last_name',
        'personal_email',
        'mobile_primary',
    ]


# ============================================================================
# ERROR CODES
# ============================================================================

class ErrorCodes:
    """
    Error codes for API responses
    """
    # General errors
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    NOT_FOUND = 'NOT_FOUND'
    DUPLICATE_ENTRY = 'DUPLICATE_ENTRY'
    INTEGRITY_ERROR = 'INTEGRITY_ERROR'
    
    # Student errors
    STUDENT_NOT_FOUND = 'STUDENT_NOT_FOUND'
    STUDENT_INACTIVE = 'STUDENT_INACTIVE'
    STUDENT_DELETED = 'STUDENT_DELETED'
    STUDENT_CANNOT_DELETE = 'STUDENT_CANNOT_DELETE'
    
    # Guardian errors
    GUARDIAN_NOT_FOUND = 'GUARDIAN_NOT_FOUND'
    GUARDIAN_PRIMARY_EXISTS = 'GUARDIAN_PRIMARY_EXISTS'
    
    # Document errors
    DOCUMENT_NOT_FOUND = 'DOCUMENT_NOT_FOUND'
    DOCUMENT_INVALID_TYPE = 'DOCUMENT_INVALID_TYPE'
    DOCUMENT_TOO_LARGE = 'DOCUMENT_TOO_LARGE'
    DOCUMENT_VERIFICATION_REQUIRED = 'DOCUMENT_VERIFICATION_REQUIRED'
    
    # Bulk operation errors
    BULK_UPLOAD_FAILED = 'BULK_UPLOAD_FAILED'
    BULK_UPDATE_FAILED = 'BULK_UPDATE_FAILED'
    BULK_DELETE_FAILED = 'BULK_DELETE_FAILED'
    
    # Export errors
    EXPORT_FAILED = 'EXPORT_FAILED'
    EXPORT_TOO_LARGE = 'EXPORT_TOO_LARGE'
    EXPORT_FORMAT_UNSUPPORTED = 'EXPORT_FORMAT_UNSUPPORTED'


# ============================================================================
# PERMISSION CONSTANTS
# ============================================================================

class Permissions:
    """
    Permission constants for student management
    """
    # Student permissions
    VIEW_STUDENT = 'students.view_student'
    ADD_STUDENT = 'students.add_student'
    CHANGE_STUDENT = 'students.change_student'
    DELETE_STUDENT = 'students.delete_student'
    
    # Guardian permissions
    VIEW_GUARDIAN = 'students.view_guardian'
    ADD_GUARDIAN = 'students.add_guardian'
    CHANGE_GUARDIAN = 'students.change_guardian'
    DELETE_GUARDIAN = 'students.delete_guardian'
    
    # Document permissions
    VIEW_STUDENTDOCUMENT = 'students.view_studentdocument'
    ADD_STUDENTDOCUMENT = 'students.add_studentdocument'
    CHANGE_STUDENTDOCUMENT = 'students.change_studentdocument'
    DELETE_STUDENTDOCUMENT = 'students.delete_studentdocument'
    VERIFY_STUDENTDOCUMENT = 'students.verify_studentdocument'
    DOWNLOAD_STUDENTDOCUMENT = 'students.download_studentdocument'
    
    # Special permissions
    VIEW_STUDENT_DASHBOARD = 'students.view_student_dashboard'
    EXPORT_STUDENT_DATA = 'students.export_student_data'
    IMPORT_STUDENT_DATA = 'students.import_student_data'
    BULK_UPDATE_STUDENTS = 'students.bulk_update_students'
    BULK_DELETE_STUDENTS = 'students.bulk_delete_students'
    PROMOTE_STUDENTS = 'students.promote_students'
    GENERATE_ID_CARDS = 'students.generate_id_cards'
    VIEW_STUDENT_REPORTS = 'students.view_student_reports'
    
    # Permission groups
    STUDENT_VIEW_PERMISSIONS = [
        VIEW_STUDENT,
        VIEW_GUARDIAN,
        VIEW_STUDENTDOCUMENT,
        VIEW_STUDENT_DASHBOARD,
        VIEW_STUDENT_REPORTS,
    ]
    
    STUDENT_EDIT_PERMISSIONS = [
        ADD_STUDENT,
        CHANGE_STUDENT,
        ADD_GUARDIAN,
        CHANGE_GUARDIAN,
        ADD_STUDENTDOCUMENT,
        CHANGE_STUDENTDOCUMENT,
        VERIFY_STUDENTDOCUMENT,
        DOWNLOAD_STUDENTDOCUMENT,
        PROMOTE_STUDENTS,
        GENERATE_ID_CARDS,
    ]
    
    STUDENT_ADMIN_PERMISSIONS = [
        DELETE_STUDENT,
        DELETE_GUARDIAN,
        DELETE_STUDENTDOCUMENT,
        EXPORT_STUDENT_DATA,
        IMPORT_STUDENT_DATA,
        BULK_UPDATE_STUDENTS,
        BULK_DELETE_STUDENTS,
    ]


# ============================================================================
# TEMPLATE CONSTANTS
# ============================================================================

class Templates:
    """
    Template path constants
    """
    # Base template directory
    BASE_DIR = 'students/'
    
    # Dashboard templates
    DASHBOARD = BASE_DIR + 'dashboard.html'
    
    # Student CRUD templates
    STUDENT_LIST = BASE_DIR + 'student_list.html'
    STUDENT_DETAIL = BASE_DIR + 'student_detail.html'
    STUDENT_FORM = BASE_DIR + 'student_form.html'
    STUDENT_CONFIRM_DELETE = BASE_DIR + 'student_confirm_delete.html'
    
    # Guardian templates
    GUARDIAN_FORM = BASE_DIR + 'guardian_form.html'
    GUARDIAN_CONFIRM_DELETE = BASE_DIR + 'guardian_confirm_delete.html'
    
    # Document templates
    DOCUMENT_FORM = BASE_DIR + 'document_form.html'
    DOCUMENT_CONFIRM_DELETE = BASE_DIR + 'document_confirm_delete.html'
    
    # Bulk operation templates
    BULK_UPLOAD = BASE_DIR + 'student_bulk_upload.html'
    BULK_UPLOAD_SUMMARY = BASE_DIR + 'bulk_upload_summary.html'
    BATCH_ID_CARDS = BASE_DIR + 'batch_id_cards.html'
    
    # Specialized templates
    STUDENT_ACADEMIC_HISTORY = BASE_DIR + 'student_academic_history.html'
    STUDENT_PROMOTE = BASE_DIR + 'student_promote.html'
    STUDENT_REPORT = BASE_DIR + 'student_report.html'
    
    # Registration wizard templates
    REGISTRATION_WIZARD = BASE_DIR + 'registration/wizard.html'
    REGISTRATION_STEP1 = BASE_DIR + 'registration/step1_student.html'
    REGISTRATION_STEP2 = BASE_DIR + 'registration/step2_guardian.html'
    REGISTRATION_STEP3 = BASE_DIR + 'registration/step3_address.html'
    REGISTRATION_STEP4 = BASE_DIR + 'registration/step4_documents.html'
    
    # Error templates
    ERROR = BASE_DIR + 'error.html'


# ============================================================================
# URL PATTERN CONSTANTS
# ============================================================================

class URLPatterns:
    """
    URL pattern names for reverse lookups
    """
    # Dashboard
    DASHBOARD = 'students:student_dashboard'
    
    # Student CRUD
    LIST = 'students:student_list'
    CREATE = 'students:student_create'
    DETAIL = 'students:student_detail'
    EDIT = 'students:student_edit'
    DELETE = 'students:student_delete'
    
    # Guardian operations
    GUARDIAN_CREATE = 'students:guardian_create'
    GUARDIAN_EDIT = 'students:guardian_edit'
    GUARDIAN_DELETE = 'students:guardian_delete'
    
    # Document operations
    DOCUMENT_UPLOAD = 'students:document_upload'
    DOCUMENT_DOWNLOAD = 'students:document_download'
    DOCUMENT_DELETE = 'students:document_delete'
    
    # Bulk operations
    BULK_UPLOAD = 'students:student_bulk_upload'
    BULK_UPLOAD_SUMMARY = 'students:bulk_upload_summary'
    BULK_UPLOAD_SAMPLE = 'students:bulk_upload_sample'
    BULK_UPLOAD_VALIDATE = 'students:bulk_upload_validate'
    
    # Export operations
    EXPORT = 'students:student_export'
    
    # Specialized operations
    ACADEMIC_HISTORY = 'students:student_academic_history'
    PROMOTE = 'students:student_promote'
    REPORT = 'students:student_report'
    ID_CARD = 'students:student_id_card'
    BATCH_ID_CARDS = 'students:batch_id_cards'
    
    # Registration wizard
    REGISTRATION_WIZARD = 'students:registration_wizard'
    
    # API endpoints
    SEARCH_API = 'students:student_search_api'
    STATS_API = 'students:student_stats_api'
    
    # Error handling
    ERROR = 'students:student_error'


# ============================================================================
# MODULE-LEVEL EXPORTS FOR BACKWARD COMPATIBILITY
# ============================================================================

# Bulk upload constants (exported for backward compatibility)
MAX_BULK_UPLOAD_SIZE = BulkUpload.MAX_FILE_SIZE_BYTES
ALLOWED_UPLOAD_FORMATS = BulkUpload.ALLOWED_FORMATS
REQUIRED_STUDENT_FIELDS = BulkUpload.REQUIRED_FIELDS

# Export commonly used constants
StudentStatus = StudentStatus
StudentGender = StudentGender
StudentCategory = StudentCategory
AdmissionType = AdmissionType
BloodGroup = BloodGroup
Religion = Religion
Nationality = Nationality
GuardianRelationship = GuardianRelationship
DocumentType = DocumentType
BulkUpload = BulkUpload
ExportFormat = ExportFormat
ExportType = ExportType
ValidationMessages = ValidationMessages
SystemConfig = SystemConfig
ErrorCodes = ErrorCodes
Permissions = Permissions
Templates = Templates
URLPatterns = URLPatterns