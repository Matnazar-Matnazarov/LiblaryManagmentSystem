"""
Professional Loan Management Views

This module contains ViewSets for loan management with:
- Complete CRUD operations
- Advanced filtering and search
- Business logic integration
- Comprehensive statistics
- Professional API documentation
"""

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, date
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from ..models import Loan, LoanStatus
from ..serializers import (
    LoanSerializer,
    LoanDetailSerializer,
    LoanCreateSerializer,
    LoanRenewalSerializer,
    LoanReturnSerializer,
    LoanStatisticsSerializer,
)
from accounts.permissions import (
    IsLibrarianOrReadOnly,
    IsAccountActive,
    IsAdminOrLibrarianOnly,
)


@extend_schema_view(
    list=extend_schema(
        summary="List Loans",
        description="Retrieve paginated list of loans with advanced filtering and search capabilities.",
        tags=['Loans'],
        parameters=[
            OpenApiParameter('user', OpenApiTypes.INT, description='Filter by user ID'),
            OpenApiParameter('book', OpenApiTypes.INT, description='Filter by book ID'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Filter by loan status'),
            OpenApiParameter('overdue', OpenApiTypes.BOOL, description='Filter overdue loans'),
            OpenApiParameter('renewable', OpenApiTypes.BOOL, description='Filter renewable loans'),
            OpenApiParameter('due_date_from', OpenApiTypes.DATE, description='Filter from due date'),
            OpenApiParameter('due_date_to', OpenApiTypes.DATE, description='Filter to due date'),
        ]
    ),
    create=extend_schema(
        summary="Create Loan",
        description="Create new book loan with validation and availability checking.",
        tags=['Loans']
    ),
    retrieve=extend_schema(
        summary="Get Loan Details",
        description="Retrieve detailed loan information including renewal history and notes.",
        tags=['Loans']
    ),
    update=extend_schema(
        summary="Update Loan",
        description="Update loan information (librarian only).",
        tags=['Loans']
    ),
    partial_update=extend_schema(
        summary="Partial Update Loan",
        description="Update specific loan fields (librarian only).",
        tags=['Loans']
    ),
    destroy=extend_schema(
        summary="Delete Loan",
        description="Delete loan record (admin only).",
        tags=['Loans']
    ),
)
class LoanViewSet(viewsets.ModelViewSet):
    """
    Professional Loan Management ViewSet
    
    Provides complete loan lifecycle management including:
    - Loan creation with validation
    - Renewal processing
    - Return handling
    - Fine management
    - Advanced statistics
    """
    
    permission_classes = [permissions.IsAuthenticated, IsAccountActive, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Advanced filtering options
    filterset_fields = {
        'user': ['exact'],
        'book': ['exact'],
        'status': ['exact', 'in'],
        'loan_date': ['exact', 'gte', 'lte'],
        'due_date': ['exact', 'gte', 'lte'],
        'return_date': ['exact', 'gte', 'lte', 'isnull'],
        'fine_amount': ['gt', 'gte'],
        'fine_paid': ['exact'],
        'renewal_count': ['exact', 'gte', 'lte'],
    }
    
    # Search across related fields
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'book__title', 'book__isbn', 'notes', 'librarian_notes'
    ]
    
    # Ordering options
    ordering_fields = ['loan_date', 'due_date', 'return_date', 'created_at', 'fine_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get optimized queryset with performance optimizations"""
        if getattr(self, 'swagger_fake_view', False):
            return Loan.objects.none()
        
        queryset = Loan.objects.select_related(
            'user', 'book', 'book__category', 'book__publisher', 'created_by'
        ).prefetch_related('book__authors')
        
        # Apply user-based filtering if not admin/librarian
        user = self.request.user
        if not user.has_perm('loans.view_all_loans'):
            queryset = queryset.filter(user=user)
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return LoanCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return LoanDetailSerializer
        return LoanSerializer

    def perform_create(self, serializer):
        """Override create to add created_by"""
        serializer.save(created_by=self.request.user)

    # Custom Actions
    @extend_schema(
        summary="Get Current User Loans",
        description="Retrieve current user's loan history and active loans.",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'])
    def my_loans(self, request):
        """Get current user's loans"""
        queryset = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get Overdue Loans",
        description="Retrieve all overdue loans with fine calculations.",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrLibrarianOnly])
    def overdue(self, request):
        """Get overdue loans"""
        queryset = self.get_queryset().overdue()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get Renewable Loans",
        description="Retrieve loans that can be renewed.",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'])
    def renewable(self, request):
        """Get loans that can be renewed"""
        queryset = self.get_queryset().renewable()
        
        # Filter by user if not librarian
        if not request.user.has_perm('loans.view_all_loans'):
            queryset = queryset.filter(user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Renew Loan",
        description="Renew a specific loan with optional reason and additional days.",
        request=LoanRenewalSerializer,
        tags=['Loans']
    )
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a loan"""
        loan = self.get_object()
        
        # Check permissions
        if loan.user != request.user and not request.user.has_perm('loans.change_loan'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LoanRenewalSerializer(instance=loan, data=request.data)
        if serializer.is_valid():
            loan = serializer.save()
            response_serializer = LoanDetailSerializer(loan)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Return Book",
        description="Process book return with condition notes and damage assessment.",
        request=LoanReturnSerializer,
        tags=['Loans']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def return_book(self, request, pk=None):
        """Return a book"""
        loan = self.get_object()
        
        if loan.status not in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
            return Response(
                {'error': 'Loan is not active and cannot be returned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = LoanReturnSerializer(instance=loan, data=request.data)
        if serializer.is_valid():
            loan = serializer.save()
            response_serializer = LoanDetailSerializer(loan)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Pay Fine",
        description="Mark loan fine as paid.",
        tags=['Loans']
    )
    @action(detail=True, methods=['post'])
    def pay_fine(self, request, pk=None):
        """Mark fine as paid"""
        loan = self.get_object()
        
        # Check permissions
        if loan.user != request.user and not request.user.has_perm('loans.change_loan'):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if loan.fine_amount <= 0:
            return Response(
                {'error': 'No fine to pay'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.fine_paid = True
        loan.save()
        
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data)

    @extend_schema(
        summary="Waive Fine",
        description="Waive loan fine (librarian only).",
        tags=['Loans']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def waive_fine(self, request, pk=None):
        """Waive fine (librarian only)"""
        loan = self.get_object()
        
        if loan.fine_amount <= 0:
            return Response(
                {'error': 'No fine to waive'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.fine_waived = True
        loan.save()
        
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data)

    @extend_schema(
        summary="Loan Statistics",
        description="Get comprehensive loan statistics and analytics.",
        responses={200: LoanStatisticsSerializer},
        tags=['Loans']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrLibrarianOnly])
    def statistics(self, request):
        """Get comprehensive loan statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_loans = queryset.count()
        active_loans = queryset.filter(status=LoanStatus.ACTIVE).count()
        overdue_loans = queryset.overdue().count()
        returned_loans = queryset.filter(status=LoanStatus.RETURNED).count()
        
        # Fine statistics
        total_fines = queryset.aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
        unpaid_fines = queryset.filter(
            fine_amount__gt=0, fine_paid=False, fine_waived=False
        ).aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
        
        # Duration and renewal statistics
        returned_loans_qs = queryset.filter(
            status=LoanStatus.RETURNED, 
            return_date__isnull=False
        )
        
        if returned_loans_qs.exists():
            avg_duration = 0
            total_duration_days = 0
            count = 0
            
            for loan in returned_loans_qs:
                if loan.return_date and loan.loan_date:
                    duration = (loan.return_date - loan.loan_date).days
                    total_duration_days += duration
                    count += 1
            
            avg_duration = total_duration_days / count if count > 0 else 0
        else:
            avg_duration = 0
        
        # Renewal rate
        loans_with_renewals = queryset.filter(renewal_count__gt=0).count()
        renewal_rate = (loans_with_renewals / total_loans * 100) if total_loans > 0 else 0
        
        # Monthly statistics
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        loans_this_month = queryset.filter(loan_date__gte=current_month.date()).count()
        returns_this_month = queryset.filter(
            return_date__gte=current_month.date()
        ).count()
        fines_this_month = queryset.filter(
            loan_date__gte=current_month.date()
        ).aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
        
        # Popular books and users
        most_borrowed_books = queryset.values(
            'book__title', 'book__id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        most_active_users = queryset.values(
            'user__username', 'user__id', 'user__first_name', 'user__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        statistics_data = {
            'total_loans': total_loans,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'returned_loans': returned_loans,
            'total_fines': total_fines,
            'unpaid_fines': unpaid_fines,
            'average_loan_duration': round(avg_duration, 1),
            'renewal_rate': round(renewal_rate, 1),
            'loans_this_month': loans_this_month,
            'returns_this_month': returns_this_month,
            'fines_this_month': fines_this_month,
            'most_borrowed_books': list(most_borrowed_books),
            'most_active_users': list(most_active_users),
        }
        
        serializer = LoanStatisticsSerializer(data=statistics_data)
        serializer.is_valid()
        return Response(serializer.data) 