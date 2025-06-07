"""
Professional Book Management Views
"""
from django.db.models import Count, Q, Prefetch, Avg
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from ..models import Book, Author, Category, Publisher
from ..serializers import (
    BookListSerializer,
    BookDetailSerializer, 
    BookCreateSerializer,
)
from accounts.permissions import (
    IsLibrarianOrReadOnly,
    IsAccountActive
)


@extend_schema_view(
    list=extend_schema(
        summary="List Books",
        description="Retrieve paginated list of books with advanced filtering and search capabilities.",
        tags=['Books'],
        parameters=[
            OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category'),
            OpenApiParameter('language', OpenApiTypes.STR, description='Filter by language'),
            OpenApiParameter('format', OpenApiTypes.STR, description='Filter by format'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Filter by availability status'),
            OpenApiParameter('year_from', OpenApiTypes.INT, description='Filter from publication year'),
            OpenApiParameter('year_to', OpenApiTypes.INT, description='Filter to publication year'),
            OpenApiParameter('available_only', OpenApiTypes.BOOL, description='Show only available books'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search across title, author, ISBN'),
        ]
    ),
    create=extend_schema(
        summary="Add Book",
        description="Add new book to catalog with complete metadata and validation.",
        tags=['Books']
    ),
    retrieve=extend_schema(
        summary="Get Book Details",
        description="Retrieve comprehensive book information including availability and statistics.",
        tags=['Books']
    ),
    update=extend_schema(
        summary="Update Book",
        description="Update book information and metadata.",
        tags=['Books']
    ),
    partial_update=extend_schema(
        summary="Partial Update Book",
        description="Update specific book fields.",
        tags=['Books']
    ),
    destroy=extend_schema(
        summary="Remove Book",
        description="Remove book from catalog (requires librarian permissions).",
        tags=['Books']
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    """
    Professional Book Management ViewSet
    
    Provides comprehensive book catalog management with advanced search,
    filtering, and inventory tracking capabilities.
    """
    
    permission_classes = [permissions.IsAuthenticated, IsAccountActive, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Advanced filtering options
    filterset_fields = {
        'category': ['exact'],
        'language': ['exact', 'icontains'],
        'format': ['exact'],
        'status': ['exact'],
        'publication_year': ['exact', 'gte', 'lte'],
        'available_copies': ['gt', 'gte'],
    }
    
    # Search across multiple fields
    search_fields = ['title', 'subtitle', 'isbn', 'description']
    
    # Ordering options
    ordering_fields = ['title', 'publication_year', 'created_at', 'updated_at']
    ordering = ['title']  # Default ordering

    def get_queryset(self):
        """Get optimized queryset based on action"""
        if getattr(self, 'swagger_fake_view', False):
            return Book.objects.none()
            
        if self.action == 'list':
            return self._get_list_queryset()
        elif self.action == 'retrieve':
            return self._get_detail_queryset()
        else:
            return self._get_base_queryset()

    def _get_base_queryset(self):
        """Base queryset with essential relationships"""
        return Book.objects.select_related('category', 'publisher').prefetch_related('authors')

    def _get_list_queryset(self):
        """Optimized queryset for list view"""
        return self._get_base_queryset()

    def _get_detail_queryset(self):
        """Detailed queryset for single book view"""
        return self._get_base_queryset()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookCreateSerializer
        return BookDetailSerializer

    @extend_schema(
        summary="List Available Books",
        description="Get books that are currently available for borrowing",
        tags=['Books']
    )
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available books only"""
        queryset = self.get_queryset().filter(
            status='available',
            available_copies__gt=0
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Advanced Search",
        description="Search books by multiple criteria with relevance ranking",
        tags=['Books'],
        parameters=[
            OpenApiParameter('q', OpenApiTypes.STR, description='Search query'),
            OpenApiParameter('category', OpenApiTypes.STR, description='Category filter'),
            OpenApiParameter('author', OpenApiTypes.STR, description='Author filter'),
            OpenApiParameter('year_from', OpenApiTypes.INT, description='From year'),
            OpenApiParameter('year_to', OpenApiTypes.INT, description='To year'),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced book search"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        author = request.query_params.get('author')
        year_from = request.query_params.get('year_from')
        year_to = request.query_params.get('year_to')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(authors__name__icontains=query) |
                Q(description__icontains=query) |
                Q(isbn__icontains=query)
            ).distinct()
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        
        if author:
            queryset = queryset.filter(authors__name__icontains=author)
        
        if year_from:
            queryset = queryset.filter(publication_year__gte=year_from)
        
        if year_to:
            queryset = queryset.filter(publication_year__lte=year_to)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Books by Category",
        description="Get books filtered by specific category",
        tags=['Books']
    )
    @action(detail=False, methods=['get'], url_path='by-category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        """Get books by category"""
        try:
            category = Category.objects.get(Q(id=category_id) | Q(name=category_id))
            queryset = self.get_queryset().filter(category=category)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Popular Books",
        description="Get most popular books based on availability and recent additions",
        tags=['Books']
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular books"""
        queryset = self.get_queryset().filter(
            status='available'
        ).order_by('-created_at', 'title')[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Book Statistics",
        description="Get comprehensive catalog statistics and analytics.",
        tags=['Books'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_books': {'type': 'integer'},
                    'available_books': {'type': 'integer'},
                    'total_categories': {'type': 'integer'},
                    'languages': {'type': 'object'},
                    'format_distribution': {'type': 'object'},
                    'category_distribution': {'type': 'object'}
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive book statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_books = queryset.count()
        available_books = queryset.filter(status='available', available_copies__gt=0).count()
        total_categories = Category.objects.count()
        
        # Language distribution
        languages = queryset.values('language').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Format distribution
        formats = queryset.values('format').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Category distribution
        categories = queryset.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        statistics = {
            'total_books': total_books,
            'available_books': available_books,
            'total_categories': total_categories,
            'languages': {item['language']: item['count'] for item in languages},
            'format_distribution': {item['format']: item['count'] for item in formats},
            'category_distribution': {item['category__name']: item['count'] for item in categories if item['category__name']}
        }
        
        return Response(statistics)

    @extend_schema(
        summary="Trending Books",
        description="Get currently trending and popular books.",
        tags=['Books'],
        parameters=[
            OpenApiParameter('period', OpenApiTypes.STR, description='Time period', enum=['week', 'month', 'year']),
            OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category'),
            OpenApiParameter('limit', OpenApiTypes.INT, description='Number of books (max 50)'),
        ]
    )
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending books"""
        period = request.query_params.get('period', 'month')
        category = request.query_params.get('category')
        limit = min(int(request.query_params.get('limit', 20)), 50)
        
        queryset = self.get_queryset()
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        
        # Order by recent additions and availability
        queryset = queryset.order_by('-created_at', 'title')[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Book Recommendations",
        description="Get personalized book recommendations.",
        tags=['Books'],
        parameters=[
            OpenApiParameter('book_id', OpenApiTypes.STR, description='Similar to this book'),
            OpenApiParameter('category', OpenApiTypes.STR, description='Focus on category'),
            OpenApiParameter('author', OpenApiTypes.STR, description='Focus on author'),
            OpenApiParameter('limit', OpenApiTypes.INT, description='Number of recommendations'),
        ]
    )
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get book recommendations"""
        book_id = request.query_params.get('book_id')
        category = request.query_params.get('category')
        author = request.query_params.get('author')
        limit = min(int(request.query_params.get('limit', 10)), 20)
        
        queryset = self.get_queryset()
        
        if book_id:
            try:
                book = Book.objects.get(id=book_id)
                queryset = queryset.filter(
                    Q(category=book.category) | 
                    Q(authors__in=book.authors.all())
                ).exclude(id=book_id).distinct()
            except Book.DoesNotExist:
                pass
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        
        if author:
            queryset = queryset.filter(authors__name__icontains=author)
        
        # Order by availability and recent additions
        queryset = queryset.order_by('-created_at', 'title')[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 