"""
Professional Authentication Views for Library Management System

This module contains authentication-related views including:
- User login and registration
- JWT token management
- Password reset functionality
- Email verification
- Social authentication integration
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from typing import Dict, Any

from ..models import User, AccountStatus, VerificationStatus
from ..serializers import (
    UserLoginSerializer, UserRegistrationSerializer, 
    PasswordChangeSerializer, UserSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with additional user information
    """
    serializer_class = UserLoginSerializer

    @extend_schema(
        tags=['Authentication'],
        summary="User Login",
        description="Authenticate user and return JWT tokens with user profile information.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user': {'$ref': '#/components/schemas/User'}
                }
            }
        }
    )
    def post(self, request, *args, **kwargs):
        """Login user and return tokens with user data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.update_last_login()
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class UserRegistrationView(APIView):
    """
    Professional user registration with email verification
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary="User Registration",
        description="Register a new user account with profile photo and role assignment.",
        request=UserRegistrationSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                    'user': {'$ref': '#/components/schemas/User'}
                }
            }
        }
    )
    def post(self, request):
        """Register new user"""
        serializer = UserRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Send verification email
            self.send_verification_email(user, request)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'message': 'Registration successful. Please check your email for verification.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_verification_email(self, user: User, request) -> None:
        """Send email verification link to user"""
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            verification_url = request.build_absolute_uri(
                f'/api/auth/verify-email/{uid}/{token}/'
            )
            
            subject = 'Verify your email address'
            message = render_to_string('accounts/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'domain': request.get_host(),
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=True
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")


class EmailVerificationView(APIView):
    """
    Email verification endpoint
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Verify Email",
        description="Verify user email address using verification token.",
        parameters=[
            OpenApiParameter('uidb64', OpenApiTypes.STR, OpenApiParameter.PATH),
            OpenApiParameter('token', OpenApiTypes.STR, OpenApiParameter.PATH),
        ],
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        }
    )
    def get(self, request, uidb64, token):
        """Verify email with token"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.email_verification_status = VerificationStatus.APPROVED
                user.email_verified_at = timezone.now()
                
                # Activate account if it was pending
                if user.account_status == AccountStatus.PENDING_ACTIVATION:
                    user.account_status = AccountStatus.ACTIVE
                
                user.save()
                
                return Response({
                    'message': 'Email verified successfully!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid verification token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid verification link'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Request password reset
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Request Password Reset",
        description="Send password reset email to user.",
        request={
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'}
            },
            'required': ['email']
        },
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        }
    )
    def post(self, request):
        """Send password reset email"""
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Send reset email
            reset_url = request.build_absolute_uri(
                f'/reset-password/{uid}/{token}/'
            )
            
            subject = 'Password Reset Request'
            message = render_to_string('accounts/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'domain': request.get_host(),
            })
            
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=True
            )
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            pass
        
        return Response({
            'message': 'If an account with this email exists, you will receive password reset instructions.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with new password
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Reset Password",
        description="Reset user password using reset token and new password.",
        parameters=[
            OpenApiParameter('uidb64', OpenApiTypes.STR, OpenApiParameter.PATH),
            OpenApiParameter('token', OpenApiTypes.STR, OpenApiParameter.PATH),
        ],
        request={
            'type': 'object',
            'properties': {
                'new_password': {'type': 'string', 'minLength': 8}
            },
            'required': ['new_password']
        },
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        }
    )
    def post(self, request, uidb64, token):
        """Reset password with token"""
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response({
                'error': 'New password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'message': 'Password reset successfully!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    Change password for authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Change Password",
        description="Change password for authenticated user.",
        request=PasswordChangeSerializer,
        responses={
            200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        }
    )
    def post(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully!'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary="User Logout",
    description="Logout user and invalidate refresh token.",
    request={
        'type': 'object',
        'properties': {
            'refresh': {'type': 'string'}
        }
    },
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user and blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Django logout
        logout(request)
        
        return Response({
            'message': 'Logged out successfully!'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary="Resend Verification Email",
    description="Resend email verification link to user.",
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_verification_email(request):
    """Resend email verification"""
    user = request.user
    
    if user.email_verification_status == VerificationStatus.APPROVED:
        return Response({
            'message': 'Email is already verified!'
        }, status=status.HTTP_200_OK)
    
    # Send verification email
    view = UserRegistrationView()
    view.send_verification_email(user, request)
    
    return Response({
        'message': 'Verification email sent!'
    }, status=status.HTTP_200_OK) 