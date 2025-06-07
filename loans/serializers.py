"""
Professional Loan Management Serializers

This module contains serializers for loan and reservation management with:
- Comprehensive validation
- Nested relationships
- Business logic integration
- Professional documentation
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from drf_spectacular.utils import extend_schema_field

from .models import Loan, Reservation, LoanStatus, ReservationStatus
from books.serializers import BookListSerializer
from accounts.serializers import UserSerializer


class LoanSerializer(serializers.ModelSerializer):
    """
    Basic loan serializer for list views
    """
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    
    # Computed fields
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()
    can_renew = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'book', 'status', 'loan_date', 'due_date', 
            'return_date', 'renewal_count', 'fine_amount', 'fine_paid',
            'fine_waived', 'is_overdue', 'days_overdue', 'days_until_due',
            'can_renew', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'fine_amount', 'is_overdue', 'days_overdue', 
            'days_until_due', 'can_renew', 'created_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_can_renew(self, obj: Loan) -> bool:
        """Check if loan can be renewed"""
        return obj.can_renew()


class LoanDetailSerializer(LoanSerializer):
    """
    Detailed loan serializer with full information
    """
    renewal_history = serializers.ReadOnlyField()
    notes = serializers.CharField(read_only=True)
    librarian_notes = serializers.CharField(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta(LoanSerializer.Meta):
        fields = LoanSerializer.Meta.fields + [
            'renewal_history', 'notes', 'librarian_notes', 'created_by'
        ]
    
    @extend_schema_field(serializers.BooleanField)
    def get_can_renew(self, obj: Loan) -> bool:
        """Check if loan can be renewed"""
        return obj.can_renew()


class LoanCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new loans
    """
    user_id = serializers.IntegerField(write_only=True)
    book_id = serializers.IntegerField(write_only=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Loan
        fields = [
            'user_id', 'book_id', 'loan_date', 'due_date', 'notes'
        ]
    
    def validate(self, attrs):
        """Comprehensive validation for loan creation"""
        from books.models import Book
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Validate user exists and is active
        try:
            user = User.objects.get(id=attrs['user_id'])
            if user.account_status != 'active':
                raise serializers.ValidationError(
                    "User account is not active and cannot borrow books."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        # Validate book exists and is available
        try:
            book = Book.objects.get(id=attrs['book_id'])
            if book.available_copies <= 0:
                raise serializers.ValidationError(
                    "Book is not available for borrowing."
                )
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book not found.")
        
        # Check user loan limits
        max_books = settings.LIBRARY_SETTINGS.get('MAX_BOOKS_PER_USER', 5)
        active_loans = user.loans.filter(status=LoanStatus.ACTIVE).count()
        
        if active_loans >= max_books:
            raise serializers.ValidationError(
                f"User has reached maximum loan limit ({max_books} books)."
            )
        
        # Check for existing active loan of same book
        existing_loan = user.loans.filter(
            book=book,
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE]
        ).exists()
        
        if existing_loan:
            raise serializers.ValidationError(
                "User already has an active loan for this book."
            )
        
        # Check for unpaid fines
        unpaid_fines = user.loans.filter(
            fine_amount__gt=0,
            fine_paid=False,
            fine_waived=False
        ).exists()
        
        if unpaid_fines:
            raise serializers.ValidationError(
                "User has unpaid fines and cannot borrow new books."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create loan and update book availability"""
        from books.models import Book
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        user = User.objects.get(id=validated_data.pop('user_id'))
        book = Book.objects.get(id=validated_data.pop('book_id'))
        
        # Set due date if not provided
        if 'due_date' not in validated_data:
            loan_duration = settings.LIBRARY_SETTINGS.get('LOAN_DURATION_DAYS', 14)
            validated_data['due_date'] = validated_data.get('loan_date', timezone.now().date()) + timedelta(days=loan_duration)
        
        # Create loan
        loan = Loan.objects.create(
            user=user,
            book=book,
            created_by=self.context['request'].user if 'request' in self.context else None,
            **validated_data
        )
        
        # Update book availability
        book.available_copies -= 1
        book.save()
        
        return loan


class LoanRenewalSerializer(serializers.Serializer):
    """
    Serializer for loan renewal requests
    """
    reason = serializers.CharField(
        max_length=255,
        required=False,
        default="User request",
        help_text="Reason for renewal"
    )
    additional_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        help_text="Additional days (uses default if not provided)"
    )
    
    def validate(self, attrs):
        """Validate renewal request"""
        loan = self.instance
        
        if not loan.can_renew():
            raise serializers.ValidationError(
                "Loan cannot be renewed. Check renewal limits and due date."
            )
        
        return attrs
    
    def save(self):
        """Perform loan renewal"""
        loan = self.instance
        days = self.validated_data.get('additional_days')
        reason = self.validated_data.get('reason', "User request")
        
        loan.renew(days=days, reason=reason)
        return loan


class LoanReturnSerializer(serializers.Serializer):
    """
    Serializer for book return process
    """
    condition_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes about book condition upon return"
    )
    damage_fine = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        default=0,
        help_text="Additional fine for damage"
    )
    
    def save(self):
        """Process book return"""
        loan = self.instance
        condition_notes = self.validated_data.get('condition_notes', '')
        damage_fine = self.validated_data.get('damage_fine', 0)
        
        loan.return_book(
            condition_notes=condition_notes,
            damage_fine=damage_fine
        )
        return loan


class ReservationSerializer(serializers.ModelSerializer):
    """
    Basic reservation serializer for list views
    """
    user = UserSerializer(read_only=True)
    book = BookListSerializer(read_only=True)
    
    # Computed fields
    is_expired = serializers.ReadOnlyField()
    time_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'book', 'status', 'reserved_at', 'expires_at',
            'notified_at', 'queue_position', 'priority', 'is_expired',
            'time_until_expiry', 'updated_at'
        ]
        read_only_fields = [
            'id', 'queue_position', 'is_expired', 'time_until_expiry',
            'notified_at', 'updated_at'
        ]
    
    @extend_schema_field(serializers.FloatField)
    def get_time_until_expiry(self, obj: Reservation) -> float:
        """Get time until expiration in hours"""
        time_delta = obj.time_until_expiry
        if time_delta.total_seconds() <= 0:
            return 0
        return round(time_delta.total_seconds() / 3600, 1)


class ReservationDetailSerializer(ReservationSerializer):
    """
    Detailed reservation serializer
    """
    notes = serializers.CharField(read_only=True)
    
    class Meta(ReservationSerializer.Meta):
        fields = ReservationSerializer.Meta.fields + ['notes']
    
    @extend_schema_field(serializers.FloatField)
    def get_time_until_expiry(self, obj: Reservation) -> float:
        """Get time until expiration in hours"""
        time_delta = obj.time_until_expiry
        if time_delta.total_seconds() <= 0:
            return 0
        return round(time_delta.total_seconds() / 3600, 1)


class ReservationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new reservations
    """
    user_id = serializers.IntegerField(write_only=True)
    book_id = serializers.IntegerField(write_only=True)
    priority = serializers.IntegerField(required=False, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Reservation
        fields = ['user_id', 'book_id', 'priority', 'notes']
    
    def validate(self, attrs):
        """Comprehensive validation for reservation creation"""
        from books.models import Book
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Validate user exists and is active
        try:
            user = User.objects.get(id=attrs['user_id'])
            if user.account_status != 'active':
                raise serializers.ValidationError(
                    "User account is not active and cannot make reservations."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        # Validate book exists
        try:
            book = Book.objects.get(id=attrs['book_id'])
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book not found.")
        
        # Check if book is available (no need to reserve)
        if book.available_copies > 0:
            raise serializers.ValidationError(
                "Book is currently available. No reservation needed."
            )
        
        # Check for existing active reservation
        existing_reservation = user.reservations.filter(
            book=book,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
        ).exists()
        
        if existing_reservation:
            raise serializers.ValidationError(
                "User already has an active reservation for this book."
            )
        
        # Check for existing active loan
        existing_loan = user.loans.filter(
            book=book,
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE]
        ).exists()
        
        if existing_loan:
            raise serializers.ValidationError(
                "User already has an active loan for this book."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create reservation"""
        from books.models import Book
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        user = User.objects.get(id=validated_data.pop('user_id'))
        book = Book.objects.get(id=validated_data.pop('book_id'))
        
        reservation = Reservation.objects.create(
            user=user,
            book=book,
            **validated_data
        )
        
        return reservation


class LoanStatisticsSerializer(serializers.Serializer):
    """
    Serializer for loan statistics
    """
    total_loans = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    overdue_loans = serializers.IntegerField()
    returned_loans = serializers.IntegerField()
    total_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    unpaid_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_loan_duration = serializers.FloatField()
    renewal_rate = serializers.FloatField()
    
    # Monthly statistics
    loans_this_month = serializers.IntegerField()
    returns_this_month = serializers.IntegerField()
    fines_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Popular books/users
    most_borrowed_books = serializers.ListField()
    most_active_users = serializers.ListField()


class ReservationStatisticsSerializer(serializers.Serializer):
    """
    Serializer for reservation statistics
    """
    total_reservations = serializers.IntegerField()
    active_reservations = serializers.IntegerField()
    fulfilled_reservations = serializers.IntegerField()
    cancelled_reservations = serializers.IntegerField()
    expired_reservations = serializers.IntegerField()
    
    average_queue_time = serializers.FloatField()
    fulfillment_rate = serializers.FloatField()
    
    # Popular reserved books
    most_reserved_books = serializers.ListField() 