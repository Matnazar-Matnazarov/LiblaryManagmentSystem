"""
Professional Book Management Serializers for Library Management System

This module contains comprehensive serializers for:
- Book CRUD operations with image handling
- Author and Publisher management with images
- Category management
- Advanced search and filtering
- Image validation and optimization
"""

from rest_framework import serializers
from django.core.files.images import get_image_dimensions
from django.core.exceptions import ValidationError as DjangoValidationError
from PIL import Image
import io
from django.core.files.base import ContentFile
from typing import Dict, Any
from drf_spectacular.utils import extend_schema_field

from .models import Book, Author, Category, Publisher


class ImageValidationMixin:
    """Mixin for image validation and optimization"""
    
    def validate_image(self, image, max_size_mb=5, min_width=100, min_height=100, max_width=2000, max_height=2000):
        """
        Professional image validation with size and dimension checks
        """
        if not image:
            return image
        
        # Check file size
        if image.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f"Image file too large. Size should not exceed {max_size_mb}MB."
            )
        
        # Check image dimensions
        try:
            width, height = get_image_dimensions(image)
            if width and height:
                if width < min_width or height < min_height:
                    raise serializers.ValidationError(
                        f"Image dimensions too small. Minimum size is {min_width}x{min_height}px."
                    )
                if width > max_width or height > max_height:
                    raise serializers.ValidationError(
                        f"Image dimensions too large. Maximum size is {max_width}x{max_height}px."
                    )
        except Exception:
            raise serializers.ValidationError("Invalid image file.")
        
        return image
    
    def optimize_image(self, image, quality=85, max_dimension=1200):
        """
        Optimize image using PIL for better performance
        """
        try:
            # Open image with PIL
            pil_image = Image.open(image)
            
            # Convert to RGB if necessary
            if pil_image.mode in ('RGBA', 'LA', 'P'):
                pil_image = pil_image.convert('RGB')
            
            # Resize if needed
            if pil_image.width > max_dimension or pil_image.height > max_dimension:
                pil_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            pil_image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Create new ContentFile
            optimized_image = ContentFile(
                output.read(),
                name=f"optimized_{image.name.split('.')[0]}.jpg"
            )
            
            return optimized_image
            
        except Exception as e:
            # If optimization fails, return original
            return image


class AuthorSerializer(serializers.ModelSerializer):
    """
    Professional serializer for Author model
    """
    
    class Meta:
        model = Author
        fields = [
            'id', 'name', 'biography', 'birth_date', 'death_date', 
            'nationality', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance) -> Dict[str, Any]:
        """Add computed fields to representation"""
        data = super().to_representation(instance)
        if instance.birth_date:
            data['age'] = self._calculate_age(instance.birth_date, instance.death_date)
        return data
    
    def _calculate_age(self, birth_date, death_date=None) -> int:
        """Calculate age based on birth and death dates"""
        from datetime import date
        end_date = death_date or date.today()
        return end_date.year - birth_date.year - ((end_date.month, end_date.day) < (birth_date.month, birth_date.day))


class CategorySerializer(serializers.ModelSerializer):
    """
    Professional serializer for Category model with books count
    """
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'books_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField())
    def get_books_count(self, obj: Category) -> int:
        """
        Get total number of books in this category
        """
        return obj.books.count()


class PublisherSerializer(serializers.ModelSerializer):
    """
    Professional serializer for Publisher model
    """
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'address', 'city', 'country', 
            'website', 'email', 'books_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField())
    def get_books_count(self, obj: Publisher) -> int:
        """
        Get total number of books from this publisher
        """
        return obj.books.count()


class AuthorImageSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Serializer for Author with image handling"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'name', 'biography', 'birth_date', 'death_date', 
            'nationality', 'image', 'image_url', 'slug',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.URLField())
    def get_image_url(self, obj):
        """Get full URL for author image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate_image(self, value):
        """Validate author image"""
        return super().validate_image(
            value, 
            max_size_mb=3, 
            min_width=150, 
            min_height=150,
            max_width=800, 
            max_height=800
        )
    
    def create(self, validated_data):
        """Create author with optimized image"""
        image = validated_data.get('image')
        if image:
            validated_data['image'] = self.optimize_image(image, quality=85, max_dimension=600)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update author with optimized image"""
        image = validated_data.get('image')
        if image:
            validated_data['image'] = self.optimize_image(image, quality=85, max_dimension=600)
        return super().update(instance, validated_data)


class PublisherImageSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Serializer for Publisher with image handling"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'address', 'city', 'country', 'website', 
            'email', 'image', 'image_url', 'slug',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.URLField())
    def get_image_url(self, obj):
        """Get full URL for publisher logo"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate_image(self, value):
        """Validate publisher logo"""
        return super().validate_image(
            value, 
            max_size_mb=2, 
            min_width=100, 
            min_height=100,
            max_width=600, 
            max_height=600
        )
    
    def create(self, validated_data):
        """Create publisher with optimized logo"""
        image = validated_data.get('image')
        if image:
            validated_data['image'] = self.optimize_image(image, quality=85, max_dimension=400)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update publisher with optimized logo"""
        image = validated_data.get('image')
        if image:
            validated_data['image'] = self.optimize_image(image, quality=85, max_dimension=400)
        return super().update(instance, validated_data)


class BookListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for book list view with minimal data
    """
    authors_display = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)
    availability_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'isbn', 'authors_display',
            'category_name', 'publisher_name', 'publication_year',
            'language', 'format', 'availability_status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    @extend_schema_field(serializers.CharField())
    def get_authors_display(self, obj: Book) -> str:
        """
        Get comma-separated author names
        """
        return ", ".join([author.name for author in obj.authors.all()])
    
    @extend_schema_field(serializers.JSONField())
    def get_availability_status(self, obj: Book) -> Dict[str, Any]:
        """
        Get book availability information
        """
        return {
            'available': obj.available_copies > 0,
            'total_copies': obj.total_copies,
            'available_copies': obj.available_copies,
            'status': obj.status
        }


class BookDetailSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Detailed book serializer with full information and images"""
    
    authors = AuthorImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    publisher = PublisherImageSerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    
    # Write fields for creation/update
    author_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    category_id = serializers.IntegerField(write_only=True, required=False)
    publisher_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'authors', 'category', 'publisher',
            'isbn', 'publication_year', 'edition', 'language', 'pages',
            'format', 'total_copies', 'available_copies', 'location',
            'status', 'description', 'cover_image', 'cover_image_url',
            'slug', 'created_at', 'updated_at',
            # Write-only fields
            'author_ids', 'category_id', 'publisher_id'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.URLField())
    def get_cover_image_url(self, obj):
        """Get full URL for book cover"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def validate_cover_image(self, value):
        """Validate book cover image"""
        return super().validate_image(
            value, 
            max_size_mb=4, 
            min_width=200, 
            min_height=300,
            max_width=1600, 
            max_height=2400
        )
    
    def create(self, validated_data):
        """Create book with relationships and optimized cover"""
        author_ids = validated_data.pop('author_ids', [])
        category_id = validated_data.pop('category_id', None)
        publisher_id = validated_data.pop('publisher_id', None)
        cover_image = validated_data.get('cover_image')
        
        # Optimize cover image
        if cover_image:
            validated_data['cover_image'] = self.optimize_image(
                cover_image, 
                quality=90, 
                max_dimension=1000
            )
        
        # Set relationships
        if category_id:
            validated_data['category_id'] = category_id
        if publisher_id:
            validated_data['publisher_id'] = publisher_id
        
        book = Book.objects.create(**validated_data)
        
        # Set authors
        if author_ids:
            book.authors.set(author_ids)
        
        return book
    
    def update(self, instance, validated_data):
        """Update book with relationships and optimized cover"""
        author_ids = validated_data.pop('author_ids', None)
        category_id = validated_data.pop('category_id', None)
        publisher_id = validated_data.pop('publisher_id', None)
        cover_image = validated_data.get('cover_image')
        
        # Optimize cover image
        if cover_image:
            validated_data['cover_image'] = self.optimize_image(
                cover_image, 
                quality=90, 
                max_dimension=1000
            )
        
        # Update relationships
        if category_id is not None:
            validated_data['category_id'] = category_id
        if publisher_id is not None:
            validated_data['publisher_id'] = publisher_id
        
        # Update book
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update authors
        if author_ids is not None:
            instance.authors.set(author_ids)
        
        return instance


class BookCreateSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Serializer for book creation with simplified fields"""
    
    author_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )
    category_id = serializers.IntegerField(required=True)
    publisher_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Book
        fields = [
            'title', 'subtitle', 'isbn', 'publication_year',
            'edition', 'language', 'pages', 'format',
            'total_copies', 'location', 'description',
            'cover_image', 'author_ids', 'category_id', 'publisher_id'
        ]
    
    def validate_author_ids(self, value):
        """Validate author IDs exist"""
        if not Author.objects.filter(id__in=value).count() == len(value):
            raise serializers.ValidationError("One or more author IDs are invalid.")
        return value
    
    def validate_category_id(self, value):
        """Validate category ID exists"""
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category does not exist.")
        return value
    
    def validate_publisher_id(self, value):
        """Validate publisher ID exists"""
        if value and not Publisher.objects.filter(id=value).exists():
            raise serializers.ValidationError("Publisher does not exist.")
        return value
    
    def validate_cover_image(self, value):
        """Validate book cover image"""
        return super().validate_image(
            value, 
            max_size_mb=4, 
            min_width=200, 
            min_height=300,
            max_width=1600, 
            max_height=2400
        )
    
    def create(self, validated_data):
        """Create book with optimized cover and relationships"""
        author_ids = validated_data.pop('author_ids')
        category_id = validated_data.pop('category_id')
        publisher_id = validated_data.pop('publisher_id', None)
        cover_image = validated_data.get('cover_image')
        
        # Optimize cover image
        if cover_image:
            validated_data['cover_image'] = self.optimize_image(
                cover_image, 
                quality=90, 
                max_dimension=1000
            )
        
        # Set available copies to total copies initially
        validated_data['available_copies'] = validated_data.get('total_copies', 1)
        
        # Create book
        book = Book.objects.create(
            category_id=category_id,
            publisher_id=publisher_id,
            **validated_data
        )
        
        # Set authors
        book.authors.set(author_ids)
        
        return book


class BookCoverSerializer(ImageValidationMixin, serializers.ModelSerializer):
    """Serializer specifically for book cover image uploads"""
    
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = ['id', 'title', 'cover_image', 'cover_image_url']
        read_only_fields = ['id', 'title']
    
    @extend_schema_field(serializers.URLField())
    def get_cover_image_url(self, obj):
        """Get full URL for book cover"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def validate_cover_image(self, value):
        """Validate book cover image"""
        return super().validate_image(
            value, 
            max_size_mb=4, 
            min_width=200, 
            min_height=300,
            max_width=1600, 
            max_height=2400
        )
    
    def update(self, instance, validated_data):
        """Update book cover with optimization"""
        cover_image = validated_data.get('cover_image')
        
        if cover_image:
            validated_data['cover_image'] = self.optimize_image(
                cover_image, 
                quality=90, 
                max_dimension=1000
            )
        
        return super().update(instance, validated_data)


# Renamed to avoid conflict with the optimized version above
class BookListWithImagesSerializer(serializers.ModelSerializer):
    """Book list serializer with essential fields and images"""
    
    authors = AuthorImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    publisher = PublisherImageSerializer(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'subtitle', 'authors', 'category', 'publisher',
            'isbn', 'publication_year', 'edition', 'language', 'format',
            'total_copies', 'available_copies', 'status',
            'cover_image_url', 'created_at'
        ]
    
    @extend_schema_field(serializers.URLField())
    def get_cover_image_url(self, obj):
        """Get full URL for book cover"""
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


