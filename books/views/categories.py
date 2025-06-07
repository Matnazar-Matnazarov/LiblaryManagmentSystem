"""
Professional Category Management Views
"""
from django.db.models import Count, Q
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..models import Category
from ..serializers import CategorySerializer
from accounts.permissions import (
    IsLibrarianOrReadOnly,
    IsAccountActive
)


@extend_schema_view(
    list=extend_schema(
        description="List all categories with book counts and statistics",
        summary="Get categories list",
        tags=['Categories']
    ),
    create=extend_schema(
        description="Create a new book category",
        summary="Create new category",
        tags=['Categories']
    ),
    retrieve=extend_schema(
        description="Get detailed category information with book statistics",
        summary="Get category details",
        tags=['Categories']
    ),
    update=extend_schema(
        description="Update category information completely",
        summary="Update category",
        tags=['Categories']
    ),
    partial_update=extend_schema(
        description="Partially update category information",
        summary="Partially update category",
        tags=['Categories']
    ),
    destroy=extend_schema(
        description="Delete category from the system",
        summary="Delete category",
        tags=['Categories']
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Professional ViewSet for managing book categories with advanced optimizations
    
    Features:
    - Optimized queries with prefetch_related for books
    - Advanced filtering and search capabilities
    - Role-based permissions
    - Professional pagination
    - Statistics and analytics
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActive, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Search across multiple fields
    search_fields = ['name', 'description']
    
    # Ordering options
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']  # Default ordering
    
    def get_queryset(self):
        """
        Get optimized queryset with book counts and related data
        """
        return Category.objects.prefetch_related(
            'books__authors'
        ).annotate(
            books_count=Count('books', distinct=True),
            available_books_count=Count(
                'books', 
                filter=Q(books__status='available', books__available_copies__gt=0),
                distinct=True
            )
        )
    
    @extend_schema(
        description="Search categories by name or description",
        summary="Advanced category search",
        tags=['Categories']
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with multiple criteria"""
        queryset = self.get_queryset()
        
        # Get search parameters
        query = request.query_params.get('q', '')
        has_books = request.query_params.get('has_books', 'false').lower() == 'true'
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        
        if has_books:
            queryset = queryset.filter(books_count__gt=0)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get categories with most books",
        summary="Popular categories",
        tags=['Categories']
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get categories with the most books"""
        queryset = self.get_queryset().filter(
            books_count__gt=0
        ).order_by('-books_count')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get categories with available books only",
        summary="Categories with available books",
        tags=['Categories']
    )
    @action(detail=False, methods=['get'])
    def with_available_books(self, request):
        """Get categories that have available books"""
        queryset = self.get_queryset().filter(
            available_books_count__gt=0
        ).order_by('-available_books_count')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get category statistics",
        summary="Category statistics",
        tags=['Categories']
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a specific category"""
        category = self.get_object()
        
        # Get additional statistics
        total_books = category.books.count()
        available_books = category.books.filter(
            status='available', 
            available_copies__gt=0
        ).count()
        total_copies = category.books.aggregate(
            total=Count('total_copies')
        )['total'] or 0
        
        return Response({
            'category': CategorySerializer(category).data,
            'statistics': {
                'total_books': total_books,
                'available_books': available_books,
                'checkout_rate': ((total_books - available_books) / total_books * 100) if total_books > 0 else 0,
                'total_copies': total_copies,
            }
        }) 