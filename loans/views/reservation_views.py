"""
Professional Reservation Management Views

This module contains ViewSets for reservation management with:
- Queue management system
- Automatic expiration handling
- Priority system
- Notification integration
- Professional API documentation
"""

from django.db import models
from django.db.models import Count, Max, F
from django.utils import timezone
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from ..models import Reservation, ReservationStatus
from ..serializers import (
    ReservationSerializer,
    ReservationDetailSerializer,
    ReservationCreateSerializer,
    ReservationStatisticsSerializer,
)
from accounts.permissions import (
    IsAccountActive,
    IsAdminOrLibrarianOnly,
)


@extend_schema_view(
    list=extend_schema(
        summary="List Reservations",
        description="Retrieve paginated list of reservations with queue information.",
        tags=['Loans'],
        parameters=[
            OpenApiParameter('user', OpenApiTypes.INT, description='Filter by user ID'),
            OpenApiParameter('book', OpenApiTypes.INT, description='Filter by book ID'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Filter by reservation status'),
            OpenApiParameter('queue_position', OpenApiTypes.INT, description='Filter by queue position'),
            OpenApiParameter('expired', OpenApiTypes.BOOL, description='Filter expired reservations'),
        ]
    ),
    create=extend_schema(
        summary="Create Reservation",
        description="Create new book reservation with queue management.",
        tags=['Loans']
    ),
    retrieve=extend_schema(
        summary="Get Reservation Details",
        description="Retrieve detailed reservation information including queue position.",
        tags=['Loans']
    ),
    destroy=extend_schema(
        summary="Cancel Reservation",
        description="Cancel reservation and update queue positions.",
        tags=['Loans']
    ),
)
class ReservationViewSet(viewsets.ModelViewSet):
    """
    Professional Reservation Management ViewSet
    
    Provides complete reservation management including:
    - Queue management
    - Automatic expiration handling
    - Notification integration
    - Priority system
    """
    
    permission_classes = [permissions.IsAuthenticated, IsAccountActive]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    http_method_names = ['get', 'post', 'delete']  # No PUT/PATCH for reservations
    
    # Advanced filtering options
    filterset_fields = {
        'user': ['exact'],
        'book': ['exact'],
        'status': ['exact', 'in'],
        'reserved_at': ['exact', 'gte', 'lte'],
        'expires_at': ['exact', 'gte', 'lte'],
        'queue_position': ['exact', 'gte', 'lte'],
        'priority': ['exact', 'gte', 'lte'],
    }
    
    # Search across related fields
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'book__title', 'book__isbn', 'notes'
    ]
    
    # Ordering options
    ordering_fields = ['reserved_at', 'expires_at', 'queue_position', 'priority']
    ordering = ['queue_position', 'reserved_at']

    def get_queryset(self):
        """Get optimized queryset based on user permissions"""
        if getattr(self, 'swagger_fake_view', False):
            return Reservation.objects.none()
        
        queryset = Reservation.objects.select_related(
            'user', 'book', 'book__category', 'book__publisher'
        ).prefetch_related('book__authors')
        
        # Apply user-based filtering if not admin/librarian
        user = self.request.user
        if not user.has_perm('loans.view_all_reservations'):
            queryset = queryset.filter(user=user)
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ReservationCreateSerializer
        elif self.action in ['retrieve']:
            return ReservationDetailSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        """Override create to set proper user"""
        # For users creating their own reservations
        if not self.request.user.has_perm('loans.add_reservation_for_others'):
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """Override destroy to properly cancel reservation"""
        instance.cancel(reason="Cancelled by user")

    # Custom Actions
    @extend_schema(
        summary="Get Current User Reservations",
        description="Retrieve current user's reservation history and active reservations.",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """Get current user's reservations"""
        queryset = self.get_queryset().filter(user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get Active Reservations",
        description="Retrieve all active reservations (pending/confirmed).",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active reservations"""
        queryset = self.get_queryset().active()
        
        # Filter by user if not librarian
        if not request.user.has_perm('loans.view_all_reservations'):
            queryset = queryset.filter(user=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get Expired Reservations",
        description="Retrieve expired reservations (librarian only).",
        tags=['Loans']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrLibrarianOnly])
    def expired(self, request):
        """Get expired reservations"""
        queryset = self.get_queryset().expired()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Confirm Reservation",
        description="Confirm reservation when book becomes available (librarian only).",
        tags=['Loans']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def confirm(self, request, pk=None):
        """Confirm reservation when book becomes available"""
        reservation = self.get_object()
        
        if reservation.status != ReservationStatus.PENDING:
            return Response(
                {'error': 'Only pending reservations can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if book is available
        if reservation.book.available_copies <= 0:
            return Response(
                {'error': 'Book is not available for confirmation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if this is the next in queue
        next_reservation = Reservation.objects.filter(
            book=reservation.book,
            status=ReservationStatus.PENDING,
            queue_position__lt=reservation.queue_position
        ).exists()
        
        if next_reservation:
            return Response(
                {'error': 'There are reservations ahead in the queue'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reservation.confirm()
        serializer = ReservationDetailSerializer(reservation)
        return Response(serializer.data)

    @extend_schema(
        summary="Fulfill Reservation",
        description="Fulfill reservation by creating a loan (librarian only).",
        tags=['Loans']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def fulfill(self, request, pk=None):
        """Fulfill reservation by creating a loan"""
        reservation = self.get_object()
        
        if reservation.status != ReservationStatus.CONFIRMED:
            return Response(
                {'error': 'Only confirmed reservations can be fulfilled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            loan = reservation.fulfill()
            # Import here to avoid circular import
            from ..serializers import LoanDetailSerializer
            loan_serializer = LoanDetailSerializer(loan)
            return Response({
                'message': 'Reservation fulfilled successfully',
                'loan': loan_serializer.data
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Update Queue Position",
        description="Manually update queue position (admin only).",
        tags=['Loans']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def update_queue_position(self, request, pk=None):
        """Update queue position manually"""
        reservation = self.get_object()
        new_position = request.data.get('queue_position')
        
        if not new_position or not isinstance(new_position, int):
            return Response(
                {'error': 'Valid queue_position is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_position < 1:
            return Response(
                {'error': 'Queue position must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if position is valid for this book
        max_position = Reservation.objects.filter(
            book=reservation.book,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
        ).aggregate(Max('queue_position'))['queue_position__max'] or 0
        
        if new_position > max_position + 1:
            return Response(
                {'error': f'Maximum queue position is {max_position + 1}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_position = reservation.queue_position
        reservation.queue_position = new_position
        reservation.save()
        
        # Update other reservations' positions accordingly
        if new_position < old_position:
            # Moving up in queue, push others down
            Reservation.objects.filter(
                book=reservation.book,
                queue_position__gte=new_position,
                queue_position__lt=old_position,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            ).exclude(id=reservation.id).update(
                queue_position=models.F('queue_position') + 1
            )
        elif new_position > old_position:
            # Moving down in queue, pull others up
            Reservation.objects.filter(
                book=reservation.book,
                queue_position__gt=old_position,
                queue_position__lte=new_position,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            ).exclude(id=reservation.id).update(
                queue_position=models.F('queue_position') - 1
            )
        
        serializer = ReservationDetailSerializer(reservation)
        return Response(serializer.data)

    @extend_schema(
        summary="Clean Expired Reservations",
        description="Mark expired reservations as expired (system action).",
        tags=['Loans']
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrLibrarianOnly])
    def clean_expired(self, request):
        """Mark expired reservations as expired"""
        expired_reservations = self.get_queryset().expired()
        count = expired_reservations.count()
        
        # Mark as expired and update queue
        for reservation in expired_reservations:
            reservation.status = ReservationStatus.EXPIRED
            reservation.save()
            
            # Move queue positions up
            Reservation.objects.filter(
                book=reservation.book,
                queue_position__gt=reservation.queue_position,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            ).update(queue_position=models.F('queue_position') - 1)
        
        return Response({
            'message': f'{count} expired reservations cleaned',
            'count': count
        })

    @extend_schema(
        summary="Reservation Statistics",
        description="Get comprehensive reservation statistics and analytics.",
        responses={200: ReservationStatisticsSerializer},
        tags=['Loans']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrLibrarianOnly])
    def statistics(self, request):
        """Get comprehensive reservation statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_reservations = queryset.count()
        active_reservations = queryset.active().count()
        fulfilled_reservations = queryset.filter(status=ReservationStatus.FULFILLED).count()
        cancelled_reservations = queryset.filter(status=ReservationStatus.CANCELLED).count()
        expired_reservations = queryset.filter(status=ReservationStatus.EXPIRED).count()
        
        # Calculate average queue time (for fulfilled reservations)
        fulfilled_with_times = queryset.filter(
            status=ReservationStatus.FULFILLED
        ).exclude(
            reserved_at__isnull=True
        ).exclude(
            notified_at__isnull=True
        )
        
        if fulfilled_with_times.exists():
            total_queue_time = 0
            count = 0
            
            for reservation in fulfilled_with_times:
                if reservation.notified_at and reservation.reserved_at:
                    queue_time = (reservation.notified_at - reservation.reserved_at).total_seconds() / 3600  # in hours
                    total_queue_time += queue_time
                    count += 1
            
            avg_queue_time = total_queue_time / count if count > 0 else 0
        else:
            avg_queue_time = 0
        
        # Calculate fulfillment rate
        completed_reservations = fulfilled_reservations + cancelled_reservations + expired_reservations
        fulfillment_rate = (fulfilled_reservations / completed_reservations * 100) if completed_reservations > 0 else 0
        
        # Most reserved books
        most_reserved_books = queryset.values(
            'book__title', 'book__id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        statistics_data = {
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
            'fulfilled_reservations': fulfilled_reservations,
            'cancelled_reservations': cancelled_reservations,
            'expired_reservations': expired_reservations,
            'average_queue_time': round(avg_queue_time, 1),
            'fulfillment_rate': round(fulfillment_rate, 1),
            'most_reserved_books': list(most_reserved_books),
        }
        
        serializer = ReservationStatisticsSerializer(data=statistics_data)
        serializer.is_valid()
        return Response(serializer.data) 