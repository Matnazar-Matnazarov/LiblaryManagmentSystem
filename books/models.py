"""
Models for Books App
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
import uuid


class Category(models.Model):
    """Book categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class Author(models.Model):
    """Book authors"""
    name = models.CharField(max_length=200, unique=True)
    biography = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='author_images/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class Publisher(models.Model):
    """Book publishers"""
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='publisher_images/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class Book(models.Model):
    """Book model"""
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('uz', 'Uzbek'),
        ('ru', 'Russian'),
        ('ar', 'Arabic'),
        ('other', 'Other'),
    ]
    
    FORMAT_CHOICES = [
        ('hardcover', 'Hardcover'),
        ('paperback', 'Paperback'),
        ('ebook', 'E-book'),
        ('audiobook', 'Audiobook'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True)
    authors = models.ManyToManyField(Author, related_name='books')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, related_name='books')
    
    # Publication Details
    isbn = models.CharField(max_length=17, unique=True, blank=True)
    publication_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(2030)],
        null=True, blank=True
    )
    edition = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    # Physical Properties
    pages = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='paperback')
    
    # Library Management
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=100, blank=True, help_text="Shelf location")
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    
    slug = models.SlugField(unique=True, blank=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['isbn']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_available(self):
        """Check if book is available for borrowing"""
        return self.status == 'available' and self.available_copies > 0
    
    def reserve_copy(self):
        """Reserve a copy of the book"""
        if self.available_copies > 0:
            self.available_copies -= 1
            self.save()
            return True
        return False
    
    def return_copy(self):
        """Return a copy of the book"""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save()
            return True
        return False
