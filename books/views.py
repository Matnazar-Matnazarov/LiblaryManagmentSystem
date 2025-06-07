"""
Professional Views for Books App

This module contains comprehensive ViewSets for:
- Book management with cover image handling
- Author management with profile pictures
- Publisher management with logos
- Category organization
- Advanced image upload and optimization
- Professional API endpoints
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q, Count, Avg, Min, Max
from django.shortcuts import get_object_or_404

from .models import Book, Author, Publisher, Category
from .serializers import (
    BookListSerializer, BookDetailSerializer, BookCreateSerializer,
    BookCoverSerializer, AuthorSerializer, AuthorImageSerializer,
    PublisherSerializer, PublisherImageSerializer, CategorySerializer
)
from accounts.permissions import IsAdminOrLibrarianOnly


class BookViewSet(viewsets.ModelViewSet):
    """
    Professional Book ViewSet with comprehensive image handling
    
    Features:
    - CRUD operations for books
    - Cover image upload and optimization
    - Advanced search and filtering
    - Bulk operations
    - Statistics and analytics
    """
    
    queryset = Book.objects.select_related('category', 'publisher').prefetch_related('authors')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtering configuration
    filterset_fields = {
        'category': ['exact'],
        'status': ['exact'],
        'language': ['exact'],
        'format': ['exact'],
        'publication_year': ['exact', 'gte', 'lte'],
        'available_copies': ['gt', 'gte'],
    }
    
    search_fields = ['title', 'subtitle', 'isbn', 'authors__name', 'description']
    ordering_fields = ['title', 'publication_year', 'created_at', 'available_copies']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BookListSerializer
        elif self.action == 'create':
            return BookCreateSerializer
        elif self.action == 'upload_cover':
            return BookCoverSerializer
        return BookDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_cover']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['Books'],
        summary="Upload Book Cover Image",
        description="Upload or update cover image for a specific book.",
        request=BookCoverSerializer,
        responses={200: BookCoverSerializer}
    )
    @action(
        detail=True, 
        methods=['post', 'patch'], 
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def upload_cover(self, request, pk=None):
        """Upload or update book cover image"""
        book = self.get_object()
        serializer = BookCoverSerializer(
            book, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Books'],
        summary="Get Book Statistics",
        description="Get statistics for a specific book including loan history and popularity.",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get book statistics"""
        book = self.get_object()
        
        # Import here to avoid circular imports
        from loans.models import Loan
        
        stats = {
            'total_loans': Loan.objects.filter(book=book).count(),
            'current_loans': Loan.objects.filter(book=book, status='active').count(),
            'total_reservations': book.reservations.count(),
            'availability_rate': (book.available_copies / book.total_copies) * 100 if book.total_copies > 0 else 0,
            'popularity_score': book.total_loans if hasattr(book, 'total_loans') else 0,
        }
        
        return Response(stats)
    
    @extend_schema(
        tags=['Books'],
        summary="Get Popular Books",
        description="Get list of most popular books based on loan statistics.",
        parameters=[
            OpenApiParameter('limit', OpenApiTypes.INT, description='Number of books to return', default=10),
            OpenApiParameter('period', OpenApiTypes.STR, description='Time period (week, month, year)', default='month'),
        ],
        responses={200: BookListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular books"""
        limit = int(request.query_params.get('limit', 10))
        period = request.query_params.get('period', 'month')
        
        # For now, return books with most total copies as a placeholder
        # In production, this would use actual analytics data
        popular_books = Book.objects.annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:limit]
        
        serializer = BookListSerializer(popular_books, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Books'],
        summary="Search Books",
        description="Advanced search functionality for books.",
        parameters=[
            OpenApiParameter('q', OpenApiTypes.STR, description='Search query'),
            OpenApiParameter('author', OpenApiTypes.STR, description='Author name'),
            OpenApiParameter('category', OpenApiTypes.INT, description='Category ID'),
            OpenApiParameter('available_only', OpenApiTypes.BOOL, description='Show only available books'),
        ],
        responses={200: BookListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced book search"""
        queryset = self.get_queryset()
        
        # Basic text search
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(subtitle__icontains=q) |
                Q(authors__name__icontains=q) |
                Q(description__icontains=q)
            ).distinct()
        
        # Author filter
        author = request.query_params.get('author')
        if author:
            queryset = queryset.filter(authors__name__icontains=author)
        
        # Category filter
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Available only filter
        available_only = request.query_params.get('available_only')
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(available_copies__gt=0, status='available')
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BookListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class AuthorViewSet(viewsets.ModelViewSet):
    """
    Professional Author ViewSet with image handling
    
    Features:
    - CRUD operations for authors
    - Profile image upload and optimization
    - Author statistics and book listings
    """
    
    queryset = Author.objects.prefetch_related('books')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    search_fields = ['name', 'biography', 'nationality']
    ordering_fields = ['name', 'created_at', 'birth_date']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update', 'upload_image']:
            return AuthorImageSerializer
        return AuthorSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_image']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['Authors'],
        summary="Upload Author Image",
        description="Upload or update profile image for a specific author.",
        request=AuthorImageSerializer,
        responses={200: AuthorImageSerializer}
    )
    @action(
        detail=True, 
        methods=['post', 'patch'], 
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def upload_image(self, request, pk=None):
        """Upload or update author image"""
        author = self.get_object()
        serializer = AuthorImageSerializer(
            author, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Authors'],
        summary="Get Author Books",
        description="Get all books by a specific author.",
        responses={200: BookListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get books by this author"""
        author = self.get_object()
        books = author.books.select_related('category', 'publisher').prefetch_related('authors')
        
        # Apply pagination
        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Authors'],
        summary="Get Author Statistics",
        description="Get statistics for a specific author including book count and popularity.",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get author statistics"""
        author = self.get_object()
        
        stats = {
            'total_books': author.books.count(),
            'available_books': author.books.filter(available_copies__gt=0).count(),
            'total_copies': author.books.aggregate(total=Count('total_copies'))['total'] or 0,
            'average_rating': 0,  # Placeholder for when rating system is implemented
            'most_popular_book': None,  # Placeholder
        }
        
        # Get most popular book
        popular_book = author.books.annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count').first()
        
        if popular_book:
            stats['most_popular_book'] = {
                'id': popular_book.id,
                'title': popular_book.title,
                'loan_count': popular_book.loan_count if hasattr(popular_book, 'loan_count') else 0
            }
        
        return Response(stats)


class PublisherViewSet(viewsets.ModelViewSet):
    """
    Professional Publisher ViewSet with image handling
    
    Features:
    - CRUD operations for publishers
    - Logo upload and optimization
    - Publisher statistics and book listings
    """
    
    queryset = Publisher.objects.prefetch_related('books')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    search_fields = ['name', 'address', 'city', 'country']
    ordering_fields = ['name', 'created_at', 'city']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update', 'upload_logo']:
            return PublisherImageSerializer
        return PublisherSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_logo']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['Publishers'],
        summary="Upload Publisher Logo",
        description="Upload or update logo for a specific publisher.",
        request=PublisherImageSerializer,
        responses={200: PublisherImageSerializer}
    )
    @action(
        detail=True, 
        methods=['post', 'patch'], 
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
    )
    def upload_logo(self, request, pk=None):
        """Upload or update publisher logo"""
        publisher = self.get_object()
        serializer = PublisherImageSerializer(
            publisher, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['Publishers'],
        summary="Get Publisher Books",
        description="Get all books by a specific publisher.",
        responses={200: BookListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get books by this publisher"""
        publisher = self.get_object()
        books = publisher.books.select_related('category').prefetch_related('authors')
        
        # Apply pagination
        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Publishers'],
        summary="Get Publisher Statistics",
        description="Get statistics for a specific publisher including book count and distribution.",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get publisher statistics"""
        publisher = self.get_object()
        
        stats = {
            'total_books': publisher.books.count(),
            'available_books': publisher.books.filter(available_copies__gt=0).count(),
            'total_copies': publisher.books.aggregate(total=Count('total_copies'))['total'] or 0,
            'categories_count': publisher.books.values('category').distinct().count(),
            'languages': list(publisher.books.values_list('language', flat=True).distinct()),
            'publication_years': {
                'earliest': publisher.books.aggregate(min_year=Min('publication_year'))['min_year'],
                'latest': publisher.books.aggregate(max_year=Max('publication_year'))['max_year']
            }
        }
        
        return Response(stats)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category ViewSet for book categorization
    
    Features:
    - CRUD operations for categories
    - Category statistics
    - Book listings by category
    """
    
    queryset = Category.objects.prefetch_related('books')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrLibrarianOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['Categories'],
        summary="Get Category Books",
        description="Get all books in a specific category.",
        responses={200: BookListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        """Get books in this category"""
        category = self.get_object()
        books = category.books.select_related('publisher').prefetch_related('authors')
        
        # Apply pagination
        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = BookListSerializer(books, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Categories'],
        summary="Get Category Statistics",
        description="Get statistics for a specific category including book count and availability.",
        responses={200: dict}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get category statistics"""
        category = self.get_object()
        
        stats = {
            'total_books': category.books.count(),
            'available_books': category.books.filter(available_copies__gt=0).count(),
            'total_copies': category.books.aggregate(total=Count('total_copies'))['total'] or 0,
            'authors_count': category.books.values('authors').distinct().count(),
            'publishers_count': category.books.values('publisher').distinct().count(),
            'languages': list(category.books.values_list('language', flat=True).distinct()),
        }
        
        return Response(stats) 