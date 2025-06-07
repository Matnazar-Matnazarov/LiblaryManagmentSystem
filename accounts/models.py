"""
Professional User Model Implementation for Library Management System.

This module contains the custom User model with comprehensive features including:
- Role-based access control
- Multi-step verification process
- Professional information tracking
- Address and contact management
- Document upload capabilities
"""

from typing import Optional, TYPE_CHECKING
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

if TYPE_CHECKING:
    from django.db.models import QuerySet


# Custom Validators
class UzbekistanPhoneValidator(RegexValidator):
    """Validator for Uzbekistan phone numbers."""
    
    regex = r'^(?:\+998)?[0-9]{9}$'
    message = _(
        "Phone number must be a valid Uzbekistan number. "
        "Format: +998901234567 or 901234567"
    )
    code = 'invalid_uzbekistan_phone'


class IDCardNumberValidator(RegexValidator):
    """Validator for Uzbekistan ID card numbers."""
    
    regex = r'^[A-Z]{2}[0-9]{7}$'
    message = _(
        "ID card number must be in format: AB1234567 "
        "(2 uppercase letters followed by 7 digits)"
    )
    code = 'invalid_id_card_number'


# Enums and Choices
class UserRole(models.TextChoices):
    """User role choices with hierarchical permissions."""
    
    SUPER_ADMIN = 'super_admin', _('Super Administrator')
    LIBRARIAN = 'librarian', _('Librarian')
    TEACHER = 'teacher', _('Teacher')
    STUDENT = 'student', _('Student')
    MEMBER = 'member', _('Library Member')

    @classmethod
    def get_admin_roles(cls) -> list[str]:
        """Get roles with administrative privileges."""
        return [cls.SUPER_ADMIN, cls.LIBRARIAN]
    
    @classmethod
    def get_academic_roles(cls) -> list[str]:
        """Get academic-related roles."""
        return [cls.TEACHER, cls.STUDENT]


class Gender(models.TextChoices):
    """Gender choices."""
    
    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
    OTHER = 'other', _('Other')
    PREFER_NOT_TO_SAY = 'prefer_not_to_say', _('Prefer not to say')


class DocumentType(models.TextChoices):
    """Identity document types."""
    
    NATIONAL_ID = 'national_id', _('National ID Card')
    PASSPORT = 'passport', _('Passport')
    STUDENT_ID = 'student_id', _('Student ID')
    EMPLOYEE_ID = 'employee_id', _('Employee ID')


class ProfessionCategory(models.TextChoices):
    """Professional categories."""
    
    EDUCATION = 'education', _('Education')
    HEALTHCARE = 'healthcare', _('Healthcare')
    TECHNOLOGY = 'technology', _('Technology')
    RESEARCH = 'research', _('Research')
    STUDENT = 'student', _('Student')
    OTHER = 'other', _('Other')


class VerificationStatus(models.TextChoices):
    """Verification status choices."""
    
    PENDING = 'pending', _('Pending')
    APPROVED = 'approved', _('Approved')
    REJECTED = 'rejected', _('Rejected')
    EXPIRED = 'expired', _('Expired')


class AccountStatus(models.TextChoices):
    """Account status choices."""
    
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    SUSPENDED = 'suspended', _('Suspended')
    PENDING_ACTIVATION = 'pending_activation', _('Pending Activation')


# Querysets and Managers
class UserQuerySet(models.QuerySet):
    """Custom QuerySet for User model with commonly used filters."""
    
    def active(self) -> 'QuerySet[User]':
        """Filter active users."""
        return self.filter(account_status=AccountStatus.ACTIVE)
    
    def verified(self) -> 'QuerySet[User]':
        """Filter fully verified users."""
        return self.filter(is_fully_verified=True)
    
    def by_role(self, role: UserRole) -> 'QuerySet[User]':
        """Filter users by role."""
        return self.filter(role=role)
    
    def administrators(self) -> 'QuerySet[User]':
        """Get users with administrative roles."""
        return self.filter(role__in=UserRole.get_admin_roles())
    
    def academic_users(self) -> 'QuerySet[User]':
        """Get academic users (teachers and students)."""
        return self.filter(role__in=UserRole.get_academic_roles())
    
    def pending_verification(self) -> 'QuerySet[User]':
        """Get users with pending verification."""
        return self.filter(
            models.Q(email_verification_status=VerificationStatus.PENDING) |
            models.Q(phone_verification_status=VerificationStatus.PENDING) |
            models.Q(identity_verification_status=VerificationStatus.PENDING)
        )
    

class UserManager(BaseUserManager):
    """Custom User Manager with enhanced functionality."""
    
    def get_queryset(self) -> UserQuerySet:
        """Return custom QuerySet."""
        return UserQuerySet(self.model, using=self._db)
    
    def create_user(
        self,
        email: str,
        username: str,
        password: Optional[str] = None,
        **extra_fields
    ) -> 'User':
        """Create and return a regular user."""
        if not email:
            raise ValueError(_('Email address is required'))
        
        if not username:
            raise ValueError(_('Username is required'))
        
        email = self.normalize_email(email)
        
        # Set default values
        extra_fields.setdefault('role', UserRole.MEMBER)
        extra_fields.setdefault('account_status', AccountStatus.PENDING_ACTIVATION)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user
    
    def create_superuser(
        self,
        email: str,
        username: str,
        password: str,
        **extra_fields
    ) -> 'User':
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)
        extra_fields.setdefault('account_status', AccountStatus.ACTIVE)
        extra_fields.setdefault('is_fully_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email, username, password, **extra_fields)


# Main User Model
class User(AbstractUser):
    """
    Professional User model for Library Management System.
    
    Features:
    - Custom authentication with email as primary identifier
    - Role-based access control
    - Comprehensive verification system
    - Professional information tracking
    - Document management
    - Address and contact information
    """
    
    # Manager and QuerySet
    objects = UserManager()
    
    # Authentication fields
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('Email address'), unique=True)
    username = models.CharField(_('Username'), max_length=150, unique=True)
    
    # Role and status
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.MEMBER,
        help_text=_('User role determines access permissions')
    )
    
    account_status = models.CharField(
        _('Account status'),
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING_ACTIVATION
    )
    
    # Personal information
    first_name = models.CharField(_('First name'), max_length=150, blank=True)
    last_name = models.CharField(_('Last name'), max_length=150, blank=True)
    middle_name = models.CharField(_('Middle name'), max_length=150, blank=True)
    
    date_of_birth = models.DateField(_('Date of birth'), null=True, blank=True)
    gender = models.CharField(
        _('Gender'),
        max_length=20,
        choices=Gender.choices,
        blank=True
    )
    
    # Contact information
    phone_number = models.CharField(
        _('Phone number'),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[UzbekistanPhoneValidator()],
        help_text=_('Format: +998901234567 or 901234567')
    )
    
    # Address information
    address_line_1 = models.CharField(_('Address line 1'), max_length=255, blank=True)
    address_line_2 = models.CharField(_('Address line 2'), max_length=255, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    state_province = models.CharField(_('State/Province'), max_length=100, blank=True)
    postal_code = models.CharField(_('Postal code'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=100, default='Uzbekistan')
    
    # Professional information
    profession_category = models.CharField(
        _('Profession category'),
        max_length=20,
        choices=ProfessionCategory.choices,
        blank=True
    )
    
    profession_title = models.CharField(
        _('Profession title'),
        max_length=100,
        blank=True,
        help_text=_('e.g., Software Engineer, Teacher, Student')
    )
    
    workplace_organization = models.CharField(
        _('Workplace/Organization'),
        max_length=200,
        blank=True
    )
    
    # Document uploads
    profile_photo = models.ImageField(
        _('Profile photo'),
        upload_to='users/profiles/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
        )],
        help_text=_('Upload a profile photo (JPG, PNG, WebP)')
    )
    
    identity_document_front = models.ImageField(
        _('Identity document (front)'),
        upload_to='users/documents/identity/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']
        )]
    )
    
    identity_document_back = models.ImageField(
        _('Identity document (back)'),
        upload_to='users/documents/identity/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'pdf']
        )]
    )
    
    identity_document_type = models.CharField(
        _('Identity document type'),
        max_length=20,
        choices=DocumentType.choices,
        blank=True
    )
    
    identity_document_number = models.CharField(
        _('Identity document number'),
        max_length=50,
        blank=True,
        validators=[IDCardNumberValidator()]
    )
    
    selfie_photo = models.ImageField(
        _('Selfie photo'),
        upload_to='users/selfies/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png']
        )],
        help_text=_('Upload a clear selfie for identity verification')
    )
    
    professional_document = models.FileField(
        _('Professional document'),
        upload_to='users/documents/professional/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
        )],
        help_text=_('Upload work ID, student ID, or professional certificate')
    )
    
    # Verification statuses
    email_verification_status = models.CharField(
        _('Email verification status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    phone_verification_status = models.CharField(
        _('Phone verification status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    identity_verification_status = models.CharField(
        _('Identity verification status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    professional_verification_status = models.CharField(
        _('Professional verification status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    # Computed fields
    is_fully_verified = models.BooleanField(
        _('Is fully verified'),
        default=False,
        help_text=_('True when all required verifications are approved')
    )
    
    # Timestamps
    email_verified_at = models.DateTimeField(_('Email verified at'), null=True, blank=True)
    phone_verified_at = models.DateTimeField(_('Phone verified at'), null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(_('Last login IP'), null=True, blank=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        _('Profile visibility'),
        max_length=20,
        choices=[
            ('public', _('Public')),
            ('members_only', _('Library members only')),
            ('private', _('Private'))
        ],
        default='members_only'
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(_('Email notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS notifications'), default=False)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'accounts_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['account_status']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self) -> str:
        """String representation of user."""
        return f"{self.get_full_name()} ({self.email})"
    
    def clean(self) -> None:
        """Validate model fields."""
        super().clean()
        
        # Validate age for certain roles
        if self.date_of_birth and self.role == UserRole.STUDENT:
            age = (timezone.now().date() - self.date_of_birth).days // 365
            if age < 16:
                raise ValidationError(_('Students must be at least 16 years old'))
    
    def save(self, *args, **kwargs) -> None:
        """Override save to compute verification status."""
        self.is_fully_verified = self._compute_verification_status()
        super().save(*args, **kwargs)
    
    # Properties
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return self.get_full_name()
    
    @property
    def age(self) -> Optional[int]:
        """Calculate user's age."""
        if not self.date_of_birth:
            return None
        return (timezone.now().date() - self.date_of_birth).days // 365
    
    @property
    def is_administrator(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role in UserRole.get_admin_roles()
    
    @property
    def is_academic_user(self) -> bool:
        """Check if user is in academic category."""
        return self.role in UserRole.get_academic_roles()
    
    @property
    def verification_completion_percentage(self) -> int:
        """Calculate verification completion percentage."""
        total_checks = 4  # email, phone, identity, professional
        completed = sum([
            self.email_verification_status == VerificationStatus.APPROVED,
            self.phone_verification_status == VerificationStatus.APPROVED,
            self.identity_verification_status == VerificationStatus.APPROVED,
            self.professional_verification_status == VerificationStatus.APPROVED,
        ])
        return int((completed / total_checks) * 100)
    
    # Methods
    def get_full_name(self) -> str:
        """Return the user's full name."""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(part for part in parts if part).strip() or self.username
    
    def get_short_name(self) -> str:
        """Return the user's short name."""
        return self.first_name or self.username
    
    def get_absolute_url(self) -> str:
        """Return the user's profile URL."""
        return f"/users/{self.id}/"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission based on role."""
        permission_map = {
            UserRole.SUPER_ADMIN: ['*'],  # All permissions
            UserRole.LIBRARIAN: [
                'manage_books', 'manage_loans', 'view_analytics', 
                'manage_members', 'manage_fines'
            ],
            UserRole.TEACHER: [
                'view_books', 'borrow_books', 'reserve_books', 
                'view_student_activity'
            ],
            UserRole.STUDENT: ['view_books', 'borrow_books', 'reserve_books'],
            UserRole.MEMBER: ['view_books', 'borrow_books', 'reserve_books'],
        }
        
        user_permissions = permission_map.get(self.role, [])
        return '*' in user_permissions or permission in user_permissions
    
    def activate_account(self) -> None:
        """Activate user account."""
        self.account_status = AccountStatus.ACTIVE
        self.save(update_fields=['account_status'])
    
    def suspend_account(self, reason: str = '') -> None:
        """Suspend user account."""
        self.account_status = AccountStatus.SUSPENDED
        self.save(update_fields=['account_status'])
        # TODO: Log suspension reason
    
    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verification_status = VerificationStatus.APPROVED
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verification_status', 'email_verified_at'])
    
    def verify_phone(self) -> None:
        """Mark phone as verified."""
        self.phone_verification_status = VerificationStatus.APPROVED
        self.phone_verified_at = timezone.now()
        self.save(update_fields=['phone_verification_status', 'phone_verified_at'])
    
    def _compute_verification_status(self) -> bool:
        """Compute if user is fully verified."""
        required_verifications = [
            self.email_verification_status == VerificationStatus.APPROVED,
            self.phone_verification_status == VerificationStatus.APPROVED,
        ]
        
        # For certain roles, additional verification is required
        if self.role in [UserRole.TEACHER, UserRole.LIBRARIAN]:
            required_verifications.extend([
                self.identity_verification_status == VerificationStatus.APPROVED,
                self.professional_verification_status == VerificationStatus.APPROVED,
            ])
        
        return all(required_verifications)


# Additional models for user management
class UserVerificationLog(models.Model):
    """Log verification attempts and changes."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_logs'
    )
    verification_type = models.CharField(max_length=50)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications_performed'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('User Verification Log')
        verbose_name_plural = _('User Verification Logs')
        db_table = 'accounts_user_verification_log'


class UserSession(models.Model):
    """Track user sessions for security purposes."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        db_table = 'accounts_user_session'
    