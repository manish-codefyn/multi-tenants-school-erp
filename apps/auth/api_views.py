from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django_tenants.utils import tenant_context

from .serializers import (
    LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, UserRegistrationSerializer,
    MFAEnableSerializer, ChangePasswordSerializer
)
from .models import SecurityEvent
from apps.users.models import User
from apps.tenants.models import Tenant


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    User login with tenant awareness
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tenant = serializer.validated_data['tenant']
        remember_me = serializer.validated_data.get('remember_me', False)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Set session expiry based on remember_me
        if remember_me:
            request.session.set_expiry(1209600)  # 2 weeks
        else:
            request.session.set_expiry(3600)  # 1 hour

        # Login user for session-based auth
        login(request, user)

        response_data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_verified': user.is_verified,
                'mfa_enabled': user.mfa_enabled,
            },
            'tenant': {
                'name': tenant.name,
                'schema_name': tenant.schema_name,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    User logout
    """
    # Log security event
    SecurityEvent.objects.create(
        user=request.user,
        event_type='logout',
        severity='low',
        description='User logged out',
        ip_address=request.META.get('REMOTE_ADDR'),
        tenant=request.user.tenant
    )

    logout(request)
    return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """
    User registration with tenant context
    """
    serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.save()
        
        response_data = {
            'detail': 'Registration successful. Please check your email for verification.',
            'user_id': user.id
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    Request password reset
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        
        if user:
            # Generate reset token and send email
            reset_token = user.generate_password_reset_token()
            
            # Send reset email
            subject = 'Password Reset Request'
            html_message = render_to_string('emails/password_reset.html', {
                'user': user,
                'reset_token': reset_token,
                'tenant': user.tenant,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                'noreply@erpsystem.com',
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )

        # Always return success to prevent email enumeration
        return Response({
            'detail': 'If an account with this email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(password_reset_token=token, is_active=True)
            
            # Check if token is expired (24 hours)
            if user.password_reset_token_created < timezone.now() - timezone.timedelta(hours=24):
                return Response({
                    'detail': 'Password reset token has expired.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_token_created = None
            user.save()
            
            # Log security event
            SecurityEvent.objects.create(
                user=user,
                event_type='password_change',
                severity='medium',
                description='Password reset via email',
                ip_address=request.META.get('REMOTE_ADDR'),
                tenant=user.tenant
            )
            
            return Response({
                'detail': 'Password has been reset successfully.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'detail': 'Invalid or expired reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        # Log security event
        SecurityEvent.objects.create(
            user=user,
            event_type='password_change',
            severity='medium',
            description='Password changed by user',
            ip_address=request.META.get('REMOTE_ADDR'),
            tenant=user.tenant
        )
        
        return Response({
            'detail': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enable_mfa(request):
    """
    Enable multi-factor authentication
    """
    if request.user.mfa_enabled:
        return Response({
            'detail': 'MFA is already enabled.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = MFAEnableSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        request.user.mfa_enabled = True
        request.user.save()
        
        # Log security event
        SecurityEvent.objects.create(
            user=request.user,
            event_type='mfa_enabled',
            severity='medium',
            description='Multi-factor authentication enabled',
            ip_address=request.META.get('REMOTE_ADDR'),
            tenant=request.user.tenant
        )
        
        return Response({
            'detail': 'MFA has been enabled successfully.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def disable_mfa(request):
    """
    Disable multi-factor authentication
    """
    if not request.user.mfa_enabled:
        return Response({
            'detail': 'MFA is not enabled.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.mfa_enabled = False
    request.user.mfa_secret = None
    request.user.save()
    
    # Log security event
    SecurityEvent.objects.create(
        user=request.user,
        event_type='mfa_disabled',
        severity='medium',
        description='Multi-factor authentication disabled',
        ip_address=request.META.get('REMOTE_ADDR'),
        tenant=request.user.tenant
    )
    
    return Response({
        'detail': 'MFA has been disabled successfully.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    """
    user = request.user
    profile_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
        'role': user.role,
        'is_verified': user.is_verified,
        'mfa_enabled': user.mfa_enabled,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    return Response(profile_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """
    Verify user email address
    """
    token = request.data.get('token')
    
    if not token:
        return Response({
            'detail': 'Verification token is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(verification_token=token, is_active=True)
        user.is_verified = True
        user.verification_token = None
        user.save()
        
        # Log security event
        SecurityEvent.objects.create(
            user=user,
            event_type='email_verified',
            severity='low',
            description='Email address verified',
            tenant=user.tenant
        )
        
        return Response({
            'detail': 'Email verified successfully. You can now log in.'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'detail': 'Invalid or expired verification token.'
        }, status=status.HTTP_400_BAD_REQUEST)