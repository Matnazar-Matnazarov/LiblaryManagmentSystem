"""
Professional User Serializers for Library Management System

This module contains comprehensive serializers for:
- User management with profile pictures
- Document upload handling
- Identity verification
- Profile image optimization
- Multi-step verification process
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError as DjangoValidationError
from PIL import Image
import io
from django.core.files.base import ContentFile
from typing import Dict, Any
from drf_spectacular.utils import extend_schema_field

from .models import User, UserRole, AccountStatus, VerificationStatus


class ImageValidationMixin:
    """Mixin for image validation and processing"""
    
    def validate_image(self, image, max_size_mb=5, min_width=100, min_height=100, max_width=2000, max_height=2000):
        """
        Validate and process uploaded images
        
        Args:
            image: Uploaded image file
            max_size_mb: Maximum file size in MB
            min_width: Minimum image width
            min_height: Minimum image height
            max_width: Maximum image width
            max_height: Maximum image height
        """
        if not image:
            return image
            
        # Size validation
        if image.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f"Image file too large. Size should not exceed {max_size_mb}MB."
            )
        
        # Dimension validation
        try:
            width, height = get_image_dimensions(image)
            if width and height:
                if width < min_width or height < min_height:
                    raise serializers.ValidationError(
                        f"Image dimensions too small. Minimum size: {min_width}x{min_height}px"
                    )
                if width > max_width or height > max_height:
                    raise serializers.ValidationError(
                        f"Image dimensions too large. Maximum size: {max_width}x{max_height}px"
                    )
        except Exception:
            raise serializers.ValidationError("Invalid image file.")
        
        return image
    
    def optimize_image(self, image, quality=85, max_dimension=800):
        """
        Optimize image for web use
        
        Args:
            image: PIL Image object
            quality: JPEG quality (1-100)
            max_dimension: Maximum width or height
        """
        if not image:
            return image
            
        try:
            # Open image with PIL
            pil_image = Image.open(image)
            
            # Convert to RGB if necessary
            if pil_image.mode in ('RGBA', 'P'):
                pil_image = pil_image.convert('RGB')
            
            # Resize if too large
            width, height = pil_image.size
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            pil_image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Create new file
            return ContentFile(output.read(), name=image.name)
            
        except Exception as e:
            raise serializers.ValidationError(f"Error processing image: {str(e)}")


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for list views"""
    
    full_name = serializers.ReadOnlyField()
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'account_status', 'profile_photo_url', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
    
    @extend_schema_field(serializers.URLField())
    def get_profile_photo_url(self, obj):
        """Get full URL for profile photo"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None


class UserProfileSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Comprehensive user profile serializer with image handling"""
    
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    verification_completion_percentage = serializers.ReadOnlyField()
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'middle_name',
            'full_name', 'age', 'date_of_birth', 'gender', 'phone_number',
            'address_line_1', 'address_line_2', 'city', 'state_province',
            'postal_code', 'country', 'profession_category', 'profession_title',
            'workplace_organization', 'profile_photo', 'profile_photo_url',
            'profile_visibility', 'email_notifications', 'sms_notifications',
            'role', 'account_status', 'verification_completion_percentage',
            'email_verification_status', 'phone_verification_status',
            'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'account_status', 'verification_completion_percentage',
            'email_verification_status', 'phone_verification_status',
            'date_joined', 'last_login'
        ]
    
    @extend_schema_field(serializers.URLField())
    def get_profile_photo_url(self, obj):
        """Get full URL for profile photo"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None
    
    def validate_profile_photo(self, value):
        """Validate profile photo"""
        return super().validate_image(
            value,
            max_size_mb=3,
            min_width=150,
            min_height=150,
            max_width=1500,
            max_height=1500
        )
    
    def update(self, instance, validated_data):
        """Update user profile with optimized photo"""
        profile_photo = validated_data.get('profile_photo')
        if profile_photo:
            validated_data['profile_photo'] = self.optimize_image(
                profile_photo,
                quality=90,
                max_dimension=600
            )
        return super().update(instance, validated_data)


class UserDocumentUploadSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Serializer for document uploads during verification"""
    
    identity_document_front_url = serializers.SerializerMethodField()
    identity_document_back_url = serializers.SerializerMethodField()
    selfie_photo_url = serializers.SerializerMethodField()
    professional_document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'identity_document_front', 'identity_document_back',
            'identity_document_type', 'identity_document_number',
            'selfie_photo', 'professional_document',
            'identity_document_front_url', 'identity_document_back_url',
            'selfie_photo_url', 'professional_document_url',
            'identity_verification_status', 'professional_verification_status'
        ]
        read_only_fields = [
            'id', 'identity_verification_status', 'professional_verification_status'
        ]
    
    @extend_schema_field(serializers.URLField())
    def get_identity_document_front_url(self, obj):
        """Get full URL for identity document front"""
        if obj.identity_document_front:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.identity_document_front.url)
            return obj.identity_document_front.url
        return None
    
    @extend_schema_field(serializers.URLField())
    def get_identity_document_back_url(self, obj):
        """Get full URL for identity document back"""
        if obj.identity_document_back:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.identity_document_back.url)
            return obj.identity_document_back.url
        return None
    
    @extend_schema_field(serializers.URLField())
    def get_selfie_photo_url(self, obj):
        """Get full URL for selfie photo"""
        if obj.selfie_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.selfie_photo.url)
            return obj.selfie_photo.url
        return None
    
    @extend_schema_field(serializers.URLField())
    def get_professional_document_url(self, obj):
        """Get full URL for professional document"""
        if obj.professional_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.professional_document.url)
            return obj.professional_document.url
        return None
    
    def validate_identity_document_front(self, value):
        """Validate identity document front image"""
        return super().validate_image(
            value,
            max_size_mb=5,
            min_width=300,
            min_height=200,
            max_width=2000,
            max_height=2000
        )
    
    def validate_identity_document_back(self, value):
        """Validate identity document back image"""
        return super().validate_image(
            value,
            max_size_mb=5,
            min_width=300,
            min_height=200,
            max_width=2000,
            max_height=2000
        )
    
    def validate_selfie_photo(self, value):
        """Validate selfie photo"""
        return super().validate_image(
            value,
            max_size_mb=3,
            min_width=200,
            min_height=200,
            max_width=1500,
            max_height=1500
        )
    
    def update(self, instance, validated_data):
        """Update user documents with optimization"""
        # Optimize identity documents
        if validated_data.get('identity_document_front'):
            validated_data['identity_document_front'] = self.optimize_image(
                validated_data['identity_document_front'],
                quality=95,
                max_dimension=1200
            )
        
        if validated_data.get('identity_document_back'):
            validated_data['identity_document_back'] = self.optimize_image(
                validated_data['identity_document_back'],
                quality=95,
                max_dimension=1200
            )
        
        if validated_data.get('selfie_photo'):
            validated_data['selfie_photo'] = self.optimize_image(
                validated_data['selfie_photo'],
                quality=90,
                max_dimension=800
            )
        
        return super().update(instance, validated_data)


class UserRegistrationSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """User registration serializer with profile photo upload"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'middle_name',
            'date_of_birth', 'gender', 'phone_number', 'role',
            'profession_category', 'profession_title', 'workplace_organization',
            'profile_photo', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate registration data"""
        # Password confirmation
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Remove password_confirm from validated data
        attrs.pop('password_confirm')
        
        # Role validation
        role = attrs.get('role', UserRole.MEMBER)
        if role in [UserRole.SUPER_ADMIN, UserRole.LIBRARIAN]:
            raise serializers.ValidationError("Cannot register as admin or librarian.")
        
        return attrs
    
    def validate_profile_photo(self, value):
        """Validate profile photo during registration"""
        return super().validate_image(
            value,
            max_size_mb=3,
            min_width=150,
            min_height=150,
            max_width=1500,
            max_height=1500
        )
    
    def create(self, validated_data):
        """Create user with hashed password and optimized photo"""
        password = validated_data.pop('password')
        profile_photo = validated_data.get('profile_photo')
        
        # Optimize profile photo
        if profile_photo:
            validated_data['profile_photo'] = self.optimize_image(
                profile_photo,
                quality=90,
                max_dimension=600
            )
        
        # Create user
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfilePhotoSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Dedicated serializer for profile photo uploads"""
    
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'profile_photo', 'profile_photo_url']
        read_only_fields = ['id']
    
    @extend_schema_field(serializers.URLField())
    def get_profile_photo_url(self, obj):
        """Get full URL for profile photo"""
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None
    
    def validate_profile_photo(self, value):
        """Validate profile photo"""
        return super().validate_image(
            value,
            max_size_mb=3,
            min_width=150,
            min_height=150,
            max_width=1500,
            max_height=1500
        )
    
    def update(self, instance, validated_data):
        """Update profile photo with optimization"""
        profile_photo = validated_data.get('profile_photo')
        if profile_photo:
            validated_data['profile_photo'] = self.optimize_image(
                profile_photo,
                quality=90,
                max_dimension=600
            )
        return super().update(instance, validated_data)


class UserLoginSerializer(serializers.Serializer):
    """User login serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if user.account_status != AccountStatus.ACTIVE:
                raise serializers.ValidationError('Account is not active.')
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError('Must include email and password.')


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('New passwords do not match.')
        return attrs
    
    def save(self):
        """Change user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """Admin serializer for creating users"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role',
            'account_status', 'password'
        ]
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserRoleChangeSerializer(serializers.Serializer):
    """Serializer for changing user role"""
    role = serializers.ChoiceField(choices=UserRole.choices, required=True)
    
    def validate_role(self, value):
        """Validate role change permissions"""
        request = self.context.get('request')
        if request and request.user.role != UserRole.SUPER_ADMIN and value == UserRole.SUPER_ADMIN:
            raise serializers.ValidationError(
                "Only super admins can assign super admin role"
            )
        return value


class UserStatusChangeSerializer(serializers.Serializer):
    """Serializer for changing user account status"""
    status = serializers.ChoiceField(choices=AccountStatus.choices, required=True)


class UserDocumentVerificationSerializer(serializers.Serializer):
    """Serializer for document verification"""
    verification_type = serializers.ChoiceField(
        choices=['identity', 'professional'], 
        required=True
    )
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'], 
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500) 