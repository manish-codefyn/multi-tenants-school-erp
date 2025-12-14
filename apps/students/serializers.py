# apps/students/serializers.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import (
    Student, Guardian, StudentAddress, 
    StudentDocument, StudentMedicalInfo,
    StudentAcademicHistory, StudentIdentification
)


class StudentListSerializer(serializers.ModelSerializer):
    """Serializer for listing students"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    current_class = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'full_name',
            'personal_email', 'mobile_primary', 'current_class',
            'section', 'gender', 'status', 'status_display', 'age',
            'created_at'
        ]


class GuardianSerializer(serializers.ModelSerializer):
    """Serializer for Guardian"""
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Guardian
        fields = '__all__'
        read_only_fields = ['student', 'tenant', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Custom validation"""
        if data.get('is_primary'):
            student = self.context.get('student')
            if student:
                existing_primary = student.guardians.filter(is_primary=True)
                if self.instance:
                    existing_primary = existing_primary.exclude(id=self.instance.id)
                if existing_primary.exists():
                    raise serializers.ValidationError({
                        'is_primary': _('This student already has a primary guardian')
                    })
        return data


class StudentAddressSerializer(serializers.ModelSerializer):
    """Serializer for Student Address"""
    formatted_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudentAddress
        fields = '__all__'
        read_only_fields = ['student', 'tenant', 'created_at', 'updated_at']


class StudentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Student Document"""
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentDocument
        fields = '__all__'
        read_only_fields = [
            'student', 'tenant', 'file_name', 'file_size',
            'file_hash', 'verified_by', 'verified_at',
            'version', 'is_current', 'previous_version',
            'created_at', 'updated_at'
        ]
    
    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_download_url())
        return None
    
    def validate_file(self, value):
        """Validate file size and type"""
        max_size = 10 * 1024 * 1024  # 10MB
        allowed_types = [
            'image/jpeg', 'image/png', 'image/jpg',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        if value.size > max_size:
            raise serializers.ValidationError(_('File size must be less than 10MB'))
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(_('Invalid file type. Allowed: JPG, PNG, PDF, DOC, DOCX'))
        
        return value


class StudentMedicalInfoSerializer(serializers.ModelSerializer):
    """Serializer for Medical Information"""
    bmi_category = serializers.CharField(read_only=True)
    
    class Meta:
        model = StudentMedicalInfo
        fields = '__all__'
        read_only_fields = ['student', 'tenant', 'bmi', 'created_at', 'updated_at']


class StudentAcademicHistorySerializer(serializers.ModelSerializer):
    """Serializer for Academic History"""
    class_name = serializers.StringRelatedField()
    academic_year = serializers.StringRelatedField()
    
    class Meta:
        model = StudentAcademicHistory
        fields = '__all__'
        read_only_fields = ['student', 'tenant', 'created_at', 'updated_at']


class StudentIdentificationSerializer(serializers.ModelSerializer):
    """Serializer for Student Identification"""
    
    class Meta:
        model = StudentIdentification
        fields = '__all__'
        read_only_fields = ['student', 'tenant', 'created_at', 'updated_at']


class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Student with nested relationships"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    academic_age = serializers.IntegerField(read_only=True)
    is_eligible_for_exams = serializers.BooleanField(read_only=True)
    current_address = serializers.CharField(read_only=True)
    permanent_address = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    admission_type_display = serializers.CharField(source='get_admission_type_display', read_only=True)
    
    # Nested serializers
    guardians = GuardianSerializer(many=True, read_only=True)
    addresses = StudentAddressSerializer(many=True, read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    medical_info = StudentMedicalInfoSerializer(read_only=True)
    academic_history = StudentAcademicHistorySerializer(many=True, read_only=True)
    identification = StudentIdentificationSerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = [
            # Core Information
            'id', 'admission_number', 'roll_number', 'university_reg_no',
            'full_name', 'first_name', 'middle_name', 'last_name',
            
            # Personal Information
            'date_of_birth', 'place_of_birth', 'age', 'gender', 'gender_display',
            'blood_group', 'nationality', 'marital_status',
            
            # Contact Information
            'personal_email', 'institutional_email', 'mobile_primary', 'mobile_secondary',
            
            # Academic Information
            'admission_type', 'admission_type_display', 'enrollment_date',
            'academic_year', 'current_class', 'section', 'current_semester',
            
            # Status & Tracking
            'status', 'status_display', 'status_changed_date',
            'graduation_date', 'academic_age',
            
            # Academic Performance
            'total_credits_earned', 'cumulative_grade_point',
            
            # Socio-economic
            'category', 'religion', 'is_minority', 'is_physically_challenged',
            'annual_family_income',
            
            # Fee Information
            'fee_category', 'scholarship_type',
            
            # Properties
            'is_eligible_for_exams', 'current_address', 'permanent_address',
            
            # Nested data
            'guardians', 'addresses', 'documents', 'medical_info',
            'academic_history', 'identification',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'tenant', 'user', 'admission_number', 'institutional_email',
            'status_changed_date', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Custom validation"""
        errors = {}
        
        # Email uniqueness validation
        if 'personal_email' in data:
            student = self.instance
            tenant = self.context.get('tenant')
            
            existing = Student.objects.filter(
                personal_email=data['personal_email'],
                tenant=tenant
            )
            
            if student:
                existing = existing.exclude(id=student.id)
                
            if existing.exists():
                errors['personal_email'] = _('A student with this email already exists')
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating students with initial data"""
    create_user_account = serializers.BooleanField(default=False, write_only=True)
    
    class Meta:
        model = Student
        fields = [
            'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'blood_group',
            'personal_email', 'mobile_primary',
            'admission_type', 'enrollment_date',
            'academic_year', 'current_class', 'section',
            'create_user_account'
        ]
    
    def create(self, validated_data):
        create_user_account = validated_data.pop('create_user_account', False)
        student = Student.objects.create(**validated_data)
        
        if create_user_account:
            student.create_user_account()
        
        return student


class StudentBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk student updates"""
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    update_data = serializers.DictField(required=True)
    
    def validate_update_data(self, value):
        """Validate update data"""
        allowed_fields = [
            'status', 'current_class', 'section', 'fee_category',
            'scholarship_type', 'current_semester'
        ]
        
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(
                    _('Field {} is not allowed for bulk update').format(field)
                )
        
        return value


class StudentExportSerializer(serializers.ModelSerializer):
    """Serializer for exporting student data"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    current_class_name = serializers.CharField(source='current_class.name', read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'admission_number', 'roll_number', 'full_name',
            'date_of_birth', 'age', 'gender', 'personal_email',
            'mobile_primary', 'current_class_name', 'section_name',
            'academic_year_name', 'status', 'category',
            'total_credits_earned', 'cumulative_grade_point'
        ]


class StudentSerializer(serializers.ModelSerializer):
    """
    Base serializer for Student (used for create/update/simple retrieve)
    """
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',

            # Identity
            'admission_number',
            'roll_number',
            'university_reg_no',

            # Name
            'first_name',
            'middle_name',
            'last_name',
            'full_name',

            # Personal
            'date_of_birth',
            'age',
            'gender',
            'blood_group',
            'nationality',

            # Contact
            'personal_email',
            'institutional_email',
            'mobile_primary',
            'mobile_secondary',

            # Academic
            'academic_year',
            'current_class',
            'section',
            'current_semester',
            'admission_type',
            'enrollment_date',

            # Status
            'status',
            'status_display',
            'status_changed_date',

            # Meta
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'tenant',
            'user',
            'admission_number',
            'institutional_email',
            'status_changed_date',
            'created_at',
            'updated_at',
        ]

    def validate_personal_email(self, value):
        """
        Ensure email uniqueness per tenant
        """
        tenant = self.context.get('tenant')
        qs = Student.objects.filter(
            personal_email=value,
            tenant=tenant
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                _('A student with this email already exists')
            )

        return value
