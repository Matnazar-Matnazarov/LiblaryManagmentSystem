"""
Professional Loan Management Models

This module contains models for book borrowing system with advanced features:
- Loan tracking and management
- Reservation system
- Fine calculation
- Renewal management
- Comprehensive audit trail
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta, date
from django.conf import settings
from books.models import Book


class LoanStatus(models.TextChoices):
    """Loan status choices"""
    ACTIVE = 'active', 'Active'
    RETURNED = 'returned', 'Returned'
    OVERDUE = 'overdue', 'Overdue'
    RENEWED = 'renewed', 'Renewed'
    LOST = 'lost', 'Lost'
    DAMAGED = 'damaged', 'Damaged'


class ReservationStatus(models.TextChoices):
    """Reservation status choices"""
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    FULFILLED = 'fulfilled', 'Fulfilled'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'


class LoanQuerySet(models.QuerySet):
    """Custom queryset for Loan model"""
    
    def active(self):
        """Get active loans"""
        return self.filter(status=LoanStatus.ACTIVE)
    
    def overdue(self):
        """Get overdue loans"""
        return self.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=timezone.now().date()
        )
    
    def for_user(self, user):
        """Get loans for specific user"""
        return self.filter(user=user)
    
    def by_book(self, book):
        """Get loans for specific book"""
        return self.filter(book=book)
    
    def renewable(self):
        """Get loans that can be renewed"""
        return self.filter(
            status=LoanStatus.ACTIVE,
            renewal_count__lt=settings.LIBRARY_SETTINGS.get('MAX_RENEWAL_COUNT', 2),
            due_date__gte=timezone.now().date()
        )


class LoanManager(models.Manager):
    """Custom manager for Loan model"""
    
    def get_queryset(self):
        return LoanQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def overdue(self):
        return self.get_queryset().overdue()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def renewable(self):
        return self.get_queryset().renewable()


class Loan(models.Model):
    """
    Professional loan management model with comprehensive tracking
    
    Features:
    - Complete loan lifecycle tracking
    - Automated fine calculation
    - Renewal management
    - Audit trail
    """
    
    # Core relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
        help_text="User who borrowed the book"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='loans',
        help_text="Book that was borrowed"
    )
    
    # Loan details
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.ACTIVE,
        help_text="Current status of the loan"
    )
    
    # Important dates
    loan_date = models.DateField(
        default=timezone.now,
        help_text="Date when book was borrowed"
    )
    due_date = models.DateField(
        help_text="Date when book should be returned"
    )
    return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual date when book was returned"
    )
    
    # Renewal tracking
    renewal_count = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(5)],
        help_text="Number of times this loan has been renewed"
    )
    renewal_history = models.JSONField(
        default=list,
        blank=True,
        help_text="History of renewal dates and reasons"
    )
    
    # Fine management
    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Fine amount for overdue/damage"
    )
    fine_paid = models.BooleanField(
        default=False,
        help_text="Whether fine has been paid"
    )
    fine_waived = models.BooleanField(
        default=False,
        help_text="Whether fine has been waived by librarian"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this loan"
    )
    librarian_notes = models.TextField(
        blank=True,
        help_text="Internal notes for librarians"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loans_created',
        help_text="Librarian who created this loan"
    )
    
    objects = LoanManager()
    
    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['loan_date']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fine_amount__gte=0),
                name='positive_fine_amount'
            ),
            models.CheckConstraint(
                check=models.Q(renewal_count__gte=0),
                name='positive_renewal_count'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.book.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to set due date and calculate fines"""
        if not self.due_date and self.loan_date:
            loan_duration = settings.LIBRARY_SETTINGS.get('LOAN_DURATION_DAYS', 14)
            self.due_date = self.loan_date + timedelta(days=loan_duration)
        
        # Update status if overdue
        if self.status == LoanStatus.ACTIVE and self.due_date and self.due_date < timezone.now().date():
            self.status = LoanStatus.OVERDUE
        
        # Calculate fine for overdue books
        if self.status in [LoanStatus.OVERDUE, LoanStatus.RETURNED] and not self.fine_waived:
            self.calculate_fine()
        
        super().save(*args, **kwargs)
    
    def calculate_fine(self):
        """Calculate fine amount for overdue loan"""
        if not self.due_date:
            return
        
        today = timezone.now().date()
        return_date = self.return_date or today
        
        if return_date > self.due_date:
            overdue_days = (return_date - self.due_date).days
            fine_per_day = settings.LIBRARY_SETTINGS.get('FINE_PER_DAY', 1000)
            self.fine_amount = overdue_days * fine_per_day
    
    def can_renew(self) -> bool:
        """Check if loan can be renewed"""
        max_renewals = settings.LIBRARY_SETTINGS.get('MAX_RENEWAL_COUNT', 2)
        return (
            self.status == LoanStatus.ACTIVE and
            self.renewal_count < max_renewals and
            self.due_date >= timezone.now().date() and
            not self.book.reservations.filter(status=ReservationStatus.PENDING).exists()
        )
    
    def renew(self, days=None, reason="User request"):
        """Renew the loan"""
        if not self.can_renew():
            raise ValueError("Loan cannot be renewed")
        
        if days is None:
            days = settings.LIBRARY_SETTINGS.get('LOAN_DURATION_DAYS', 14)
        
        old_due_date = self.due_date
        self.due_date = self.due_date + timedelta(days=days)
        self.renewal_count += 1
        
        # Add to renewal history
        self.renewal_history.append({
            'date': timezone.now().isoformat(),
            'old_due_date': old_due_date.isoformat(),
            'new_due_date': self.due_date.isoformat(),
            'reason': reason,
            'renewal_number': self.renewal_count
        })
        
        self.save()
    
    def return_book(self, condition_notes="", damage_fine=0):
        """Mark book as returned"""
        self.status = LoanStatus.RETURNED
        self.return_date = timezone.now().date()
        
        if condition_notes:
            self.notes += f"\nReturn condition: {condition_notes}"
        
        if damage_fine > 0:
            self.fine_amount += damage_fine
            self.status = LoanStatus.DAMAGED
        
        # Update book availability
        self.book.available_copies += 1
        self.book.save()
        
        self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if loan is overdue"""
        return self.due_date and self.due_date < timezone.now().date()
    
    @property
    def days_overdue(self) -> int:
        """Get number of days overdue"""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days
    
    @property
    def days_until_due(self) -> int:
        """Get number of days until due"""
        if not self.due_date:
            return 0
        return (self.due_date - timezone.now().date()).days


class ReservationQuerySet(models.QuerySet):
    """Custom queryset for Reservation model"""
    
    def active(self):
        """Get active reservations"""
        return self.filter(status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    
    def for_user(self, user):
        """Get reservations for specific user"""
        return self.filter(user=user)
    
    def for_book(self, book):
        """Get reservations for specific book"""
        return self.filter(book=book)
    
    def expired(self):
        """Get expired reservations"""
        return self.filter(
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            expires_at__lt=timezone.now()
        )


class ReservationManager(models.Manager):
    """Custom manager for Reservation model"""
    
    def get_queryset(self):
        return ReservationQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def expired(self):
        return self.get_queryset().expired()


class Reservation(models.Model):
    """
    Professional book reservation system
    
    Features:
    - Queue management
    - Automatic expiration
    - Priority system
    - Notification integration
    """
    
    # Core relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text="User who made the reservation"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text="Book that was reserved"
    )
    
    # Reservation details
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
        help_text="Current status of the reservation"
    )
    
    # Important dates
    reserved_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When reservation was made"
    )
    expires_at = models.DateTimeField(
        help_text="When reservation expires"
    )
    notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user was notified about availability"
    )
    
    # Queue management
    queue_position = models.PositiveIntegerField(
        default=1,
        help_text="Position in reservation queue"
    )
    
    # Priority system
    priority = models.IntegerField(
        default=0,
        help_text="Reservation priority (higher number = higher priority)"
    )
    
    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this reservation"
    )
    
    # Audit fields
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ReservationManager()
    
    class Meta:
        db_table = 'reservations'
        ordering = ['queue_position', 'reserved_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['queue_position']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                name='unique_active_reservation_per_user_book'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.book.title} (Queue: {self.queue_position})"
    
    def save(self, *args, **kwargs):
        """Override save to set expiration and queue position"""
        if not self.expires_at:
            hours = settings.LIBRARY_SETTINGS.get('RESERVATION_DURATION_HOURS', 24)
            self.expires_at = timezone.now() + timedelta(hours=hours)
        
        # Set queue position if not set
        if not self.queue_position:
            last_position = Reservation.objects.filter(
                book=self.book,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            ).aggregate(
                models.Max('queue_position')
            )['queue_position__max'] or 0
            self.queue_position = last_position + 1
        
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Confirm the reservation when book becomes available"""
        self.status = ReservationStatus.CONFIRMED
        self.notified_at = timezone.now()
        # Extend expiration for pickup
        pickup_hours = settings.LIBRARY_SETTINGS.get('RESERVATION_PICKUP_HOURS', 48)
        self.expires_at = timezone.now() + timedelta(hours=pickup_hours)
        self.save()
    
    def fulfill(self):
        """Fulfill the reservation by creating a loan"""
        if self.status != ReservationStatus.CONFIRMED:
            raise ValueError("Reservation must be confirmed before fulfillment")
        
        # Create loan
        loan = Loan.objects.create(
            user=self.user,
            book=self.book,
            created_by=None,  # Will be set by view
        )
        
        # Update reservation status
        self.status = ReservationStatus.FULFILLED
        self.save()
        
        # Update book availability
        self.book.available_copies -= 1
        self.book.save()
        
        # Move queue positions up
        Reservation.objects.filter(
            book=self.book,
            queue_position__gt=self.queue_position,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
        ).update(queue_position=models.F('queue_position') - 1)
        
        return loan
    
    def cancel(self, reason="User cancelled"):
        """Cancel the reservation"""
        self.status = ReservationStatus.CANCELLED
        self.notes += f"\nCancelled: {reason}"
        self.save()
        
        # Move queue positions up
        Reservation.objects.filter(
            book=self.book,
            queue_position__gt=self.queue_position,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
        ).update(queue_position=models.F('queue_position') - 1)
    
    @property
    def is_expired(self) -> bool:
        """Check if reservation is expired"""
        return timezone.now() > self.expires_at
    
    @property
    def time_until_expiry(self):
        """Get time until expiration"""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - timezone.now()
