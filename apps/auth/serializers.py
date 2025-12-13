from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.users.models import User
from apps.tenants.models import Tenant, Domain
from .models import SecurityEvent


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    domain = serializers.CharField(required=False)
    tenant_schema = serializers.CharField(required=False)
    remember_me = serializers.BooleanField(default=False)

    def validate(self, attrs):
        email = attrs.get('email').lower().strip()
        password = attrs.get('password')
        domain = attrs.get('domain')
        tenant_schema = attrs.get('tenant_schema')

        # Determine tenant
        tenant = self._get_tenant(domain, tenant_schema)
        if not tenant:
            raise serializers.ValidationError({
                'domain': 'Invalid domain or tenant schema'
            })

        # Authenticate user
        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
            tenant=tenant
        )

        if not user:
            raise serializers.ValidationError({
                'non_field_errors': 'Invalid email or password'
            })

        if not user.is_verified:
            raise serializers.ValidationError({
                'non_field_errors': 'Please verify your email address before logging in'
            })

        attrs['user'] = user
        attrs['tenant'] = tenant
        return attrs

    def _get_tenant(self, domain, tenant_schema):
        """Get tenant based on domain or schema name"""
        if domain:
            try:
                from django_tenants.utils import get_tenant_domain_model
                DomainModel = get_tenant_domain_model()
                domain_obj = DomainModel.objects.select_related('tenant').get(
                    domain=domain,
                    is_primary=True
                )
                return domain_obj.tenant
            except DomainModel.DoesNotExist:
                return None
        elif tenant_schema:
            try:
                return Tenant.objects.get(schema_name=tenant_schema, is_active=True)
            except Tenant.DoesNotExist:
                return None
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField()
    domain = serializers.CharField(required=False)

    def validate(self, attrs):
        email = attrs.get('email').lower().strip()
        domain = attrs.get('domain')

        # Get tenant
        tenant = self._get_tenant(domain)
        if not tenant:
            raise serializers.ValidationError({
                'domain': 'Invalid domain'
            })

        try:
            user = User.objects.get(email=email, tenant=tenant, is_active=True)
            attrs['user'] = user
        except User.DoesNotExist:
            # Don't reveal whether user exists
            pass

        return attrs

    def _get_tenant(self, domain):
        """Get tenant from domain"""
        if domain:
            try:
                from django_tenants.utils import get_tenant_domain_model
                DomainModel = get_tenant_domain_model()
                domain_obj = DomainModel.objects.select_related('tenant').get(
                    domain=domain,
                    is_primary=True
                )
                return domain_obj.tenant
            except DomainModel.DoesNotExist:
                return None
        return None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })

        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    tenant_schema = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'confirm_password', 'tenant_schema', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        tenant_schema = attrs.get('tenant_schema')

        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })

        # Validate tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema, is_active=True)
            attrs['tenant'] = tenant
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({
                'tenant_schema': 'Invalid organization'
            })

        # Check if tenant can add more users
        if not tenant.can_add_user():
            raise serializers.ValidationError({
                'tenant_schema': 'Organization has reached user limit'
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        tenant_schema = validated_data.pop('tenant_schema')
        tenant = validated_data.pop('tenant')

        user = User.objects.create_user(
            tenant=tenant,
            **validated_data
        )

        # Send verification email
        user.send_verification_email()

        # Log security event
        SecurityEvent.objects.create(
            user=user,
            event_type='user_registered',
            severity='low',
            description='New user registration',
            tenant=tenant
        )

        return user


class MFAEnableSerializer(serializers.Serializer):
    """
    Serializer for enabling MFA
    """
    token = serializers.CharField()

    def validate(self, attrs):
        user = self.context['request'].user
        token = attrs.get('token')

        if not user.verify_mfa_token(token):
            raise serializers.ValidationError({
                'token': 'Invalid verification code'
            })

        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if not user.check_password(current_password):
            raise serializers.ValidationError({
                'current_password': 'Current password is incorrect'
            })

        if new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })

        if current_password == new_password:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password'
            })

        return attrs