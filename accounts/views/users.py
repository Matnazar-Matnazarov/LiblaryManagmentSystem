"""
Professional User Management Views for Library Management System

This module contains comprehensive user management including:
- User CRUD operations with role-based permissions
- Profile management with image uploads
- Document verification system
- User statistics and analytics
- Admin user management functionality
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.utils import timezone

from ..models import User, UserRole, AccountStatus, VerificationStatus
from ..serializers import (
    UserSerializer, UserProfileSerializer, UserDocumentUploadSerializer,
    UserRegistrationSerializer, UserProfilePhotoSerializer, UserCreateSerializer,
    UserRoleChangeSerializer, UserStatusChangeSerializer, 
    UserDocumentVerificationSerializer, UserLoginSerializer
)
from ..permissions import (
    IsOwnerOrReadOnly, IsAdminOrLibrarianOnly,
    IsAccountActive
)


@extend_schema_view(
    list=extend_schema(
        summary="List Users",
        description="Retrieve paginated list of users with advanced filtering and search capabilities.",
        tags=['Users'],
        parameters=[
            OpenApiParameter('role', OpenApiTypes.STR, description='Filter by user role'),
            OpenApiParameter('account_status', OpenApiTypes.STR, description='Filter by account status'),
            OpenApiParameter('is_verified', OpenApiTypes.BOOL, description='Filter by verification status'),
            OpenApiParameter('date_joined_from', OpenApiTypes.DATE, description='Filter from join date'),
            OpenApiParameter('date_joined_to', OpenApiTypes.DATE, description='Filter to join date'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search across name, email, username'),
        ],
        responses={200: UserSerializer(many=True)}
    ),
    create=extend_schema(
        summary="Create User",
        description="Create a new user account (admin only).",
        tags=['Users'],
        request=UserCreateSerializer,
        responses={201: UserSerializer}
    ),
    retrieve=extend_schema(
        summary="Get User Details",
        description="Retrieve detailed information about a specific user.",
        tags=['Users'],
        responses={200: UserSerializer}
    ),
    update=extend_schema(
        summary="Update User",
        description="Update user information (owner or admin only).",
        tags=['Users'],
        request=UserSerializer,
        responses={200: UserSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially Update User",
        description="Partially update user information (owner or admin only).",
        tags=['Users'],
        request=UserSerializer,
        responses={200: UserSerializer}
    ),
    destroy=extend_schema(
        summary="Delete User",
        description="Delete a user account (admin only).",
        tags=['Users'],
        responses={204: None}
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Professional User Management ViewSet with comprehensive functionality
    
    Features:
    - CRUD operations with role-based permissions
    - Profile photo and document upload handling
    - User verification and status management
    - Statistics and analytics
    - Advanced search and filtering
    """
    
    queryset = User.objects.select_related().prefetch_related()
    permission_classes = [permissions.IsAuthenticated, IsAccountActive]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Advanced filtering options
    filterset_fields = {
        'role': ['exact', 'in'],
        'account_status': ['exact', 'in'],
        'email_verification_status': ['exact'],
        'phone_verification_status': ['exact'],
        'identity_verification_status': ['exact'],
        'professional_verification_status': ['exact'],
        'gender': ['exact'],
        'profession_category': ['exact'],
        'date_joined': ['gte', 'lte'],
        'last_login': ['gte', 'lte'],
    }
    
    # Search across multiple fields
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 'middle_name',
        'phone_number', 'profession_title', 'workplace_organization'
    ]
    
    # Ordering options
    ordering_fields = [
        'username', 'email', 'first_name', 'last_name', 'date_joined',
        'last_login', 'verification_completion_percentage'
    ]
    ordering = ['-date_joined']
    
    def get_queryset(self):
        """Get optimized queryset based on user permissions"""
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        
        user = self.request.user
        queryset = User.objects.all()
        
        # Apply role-based filtering
        if user.role in [UserRole.SUPER_ADMIN, UserRole.LIBRARIAN]:
            # Admins and librarians can see all users
            return queryset
        elif user.role == UserRole.TEACHER:
            # Teachers can see students and members
            return queryset.filter(
                Q(role__in=[UserRole.STUDENT, UserRole.MEMBER]) | Q(id=user.id)
            )
        else:
            # Regular users can only see their own profile
            return queryset.filter(id=user.id)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['profile', 'update_profile']:
            return UserProfileSerializer
        elif self.action == 'upload_documents':
            return UserDocumentUploadSerializer
        elif self.action == 'upload_profile_photo':
            return UserProfilePhotoSerializer
        elif self.action == 'change_role':
            return UserRoleChangeSerializer
        elif self.action == 'change_status':
            return UserStatusChangeSerializer
        elif self.action == 'verify_documents':
            return UserDocumentVerificationSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['Users'],
        summary="User Registration",
        description="Register a new user account with profile photo upload.",
        request=UserRegistrationSerializer,
        responses={201: UserRegistrationSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Public user registration endpoint"""
        serializer = UserRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data,
                'message': 'Registration successful!'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Users'],
        summary="User Login",
        description="Authenticate user and return JWT tokens.",
        request=UserLoginSerializer,
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
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """User login endpoint"""
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Users'],
        summary="Get User Profile",
        description="Get detailed profile information for current user.",
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Users'],
        summary="Update User Profile",
        description="Update profile information for current user.",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Users'],
        summary="Upload Profile Photo",
        description="Upload or update profile photo for current user.",
        request=UserProfilePhotoSerializer,
        responses={200: UserProfilePhotoSerializer}
    )
    @action(
        detail=False, 
        methods=['post', 'patch'], 
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_profile_photo(self, request):
        """Upload profile photo for current user"""
        serializer = UserProfilePhotoSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Users'],
        summary="Upload Verification Documents",
        description="Upload identity and professional verification documents.",
        request=UserDocumentUploadSerializer,
        responses={200: UserDocumentUploadSerializer}
    )
    @action(
        detail=False, 
        methods=['post', 'patch'], 
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_documents(self, request):
        """Upload verification documents for current user"""
        serializer = UserDocumentUploadSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Update verification status to pending
            if 'identity_document_front' in request.data or 'identity_document_back' in request.data:
                user.identity_verification_status = VerificationStatus.PENDING
            
            if 'professional_document' in request.data:
                user.professional_verification_status = VerificationStatus.PENDING
            
            user.save()
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Users'],
        summary="Get User Statistics",
        description="Get comprehensive statistics for a specific user.",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get user statistics"""
        user = self.get_object()
        
        # Import models to avoid circular imports
        from loans.models import Loan
        from books.models import Book
        
        # Calculate statistics
        stats = {
            'profile_completion': user.verification_completion_percentage,
            'account_age_days': (timezone.now().date() - user.date_joined.date()).days,
            'last_login_days_ago': (timezone.now().date() - user.last_login.date()).days if user.last_login else None,
            'total_loans': Loan.objects.filter(user=user).count(),
            'active_loans': Loan.objects.filter(user=user, status='active').count(),
            'overdue_loans': Loan.objects.filter(user=user, status='overdue').count(),
            'total_reservations': 0,  # Would be user.reservations.count() if model exists
            'total_fines': 0,  # Would calculate total fines
            'verification_status': {
                'email': user.email_verification_status,
                'phone': user.phone_verification_status,
                'identity': user.identity_verification_status,
                'professional': user.professional_verification_status,
            }
        }
        
        return Response(stats)
    
    @extend_schema(
        tags=['Users'],
        summary="Verify User Documents",
        description="Approve or reject user verification documents (admin only).",
        request=UserDocumentVerificationSerializer,
        responses={200: dict}
    )
    @action(
        detail=True, 
        methods=['post'], 
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def verify_documents(self, request, pk=None):
        """Verify user documents (admin only)"""
        user = self.get_object()
        serializer = UserDocumentVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        verification_type = serializer.validated_data['verification_type']
        status_value = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        # Update verification status
        if verification_type == 'identity':
            user.identity_verification_status = status_value
        else:
            user.professional_verification_status = status_value
        
        user.save()
        
        # Log verification action
        # You could create a verification log entry here
        
        return Response({
            'message': f'{verification_type.title()} verification {status_value}',
            'user_id': user.id,
            'verification_type': verification_type,
            'status': status_value,
            'notes': notes
        })
    
    @extend_schema(
        tags=['Users'],
        summary="Change User Role",
        description="Change user role (admin only).",
        request=UserRoleChangeSerializer,
        responses={200: UserSerializer}
    )
    @action(
        detail=True, 
        methods=['post'], 
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def change_role(self, request, pk=None):
        """Change user role (admin only)"""
        user = self.get_object()
        serializer = UserRoleChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_role = serializer.validated_data['role']
        
        user.role = new_role
        user.save()
        
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Users'],
        summary="Change User Status",
        description="Change user account status (admin only).",
        request=UserStatusChangeSerializer,
        responses={200: UserSerializer}
    )
    @action(
        detail=True, 
        methods=['post'], 
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def change_status(self, request, pk=None):
        """Change user account status (admin only)"""
        user = self.get_object()
        serializer = UserStatusChangeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        
        user.account_status = new_status
        user.save()
        
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Users'],
        summary="Get Active Users",
        description="Get list of currently active users.",
        responses={200: UserSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active users"""
        queryset = self.get_queryset().filter(account_status=AccountStatus.ACTIVE)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Users'],
        summary="Get Pending Verifications",
        description="Get users with pending verification requests (admin only).",
        responses={200: UserSerializer(many=True)}
    )
    @action(
        detail=False, 
        methods=['get'], 
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def pending_verifications(self, request):
        """Get users with pending verifications (admin only)"""
        queryset = self.get_queryset().filter(
            Q(identity_verification_status=VerificationStatus.PENDING) |
            Q(professional_verification_status=VerificationStatus.PENDING)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data) 