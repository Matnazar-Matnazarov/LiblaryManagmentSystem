"""
Professional Author Management Views
"""
from django.db.models import Count, Q
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..models import Author
from ..serializers import AuthorSerializer
from accounts.permissions import (
    IsLibrarianOrReadOnly,
    IsAccountActive
)


@extend_schema_view(
    list=extend_schema(
        description="List all authors with their book counts and filtering",
        summary="Get authors list",
        tags=['Authors']
    ),
    create=extend_schema(
        description="Create a new author profile",
        summary="Create new author",
        tags=['Authors']
    ),
    retrieve=extend_schema(
        description="Get detailed author information with book statistics",
        summary="Get author details",
        tags=['Authors']
    ),
    update=extend_schema(
        description="Update author information completely",
        summary="Update author",
        tags=['Authors']
    ),
    partial_update=extend_schema(
        description="Partially update author information",
        summary="Partially update author",
        tags=['Authors']
    ),
    destroy=extend_schema(
        description="Delete author from the system",
        summary="Delete author",
        tags=['Authors']
    ),
)
class AuthorViewSet(viewsets.ModelViewSet):
    """
    Professional ViewSet for managing authors with advanced optimizations
    
    Features:
    - Optimized queries with prefetch_related for books
    - Advanced filtering and search capabilities
    - Role-based permissions
    - Professional pagination
    - Statistics and analytics
    """
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActive, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Advanced filtering options
    filterset_fields = {
        'nationality': ['exact', 'icontains'],
        'birth_date': ['exact', 'gte', 'lte'],
        'death_date': ['exact', 'gte', 'lte', 'isnull'],
    }
    
    # Search across multiple fields
    search_fields = ['name', 'biography', 'nationality']
    
    # Ordering options
    ordering_fields = ['name', 'birth_date', 'created_at', 'updated_at']
    ordering = ['name']  # Default ordering
    
    def get_queryset(self):
        """
        Get optimized queryset with book counts and prefetch
        """
        return Author.objects.prefetch_related(
            'books__category', 'books__publisher'
        ).annotate(
            books_count=Count('books', distinct=True)
        )
    
    @extend_schema(
        description="Search authors by name or biography",
        summary="Advanced author search",
        tags=['Authors']
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with multiple criteria"""
        queryset = self.get_queryset()
        
        # Get search parameters
        query = request.query_params.get('q', '')
        nationality = request.query_params.get('nationality', '')
        alive_only = request.query_params.get('alive_only', 'false').lower() == 'true'
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(biography__icontains=query)
            )
        
        if nationality:
            queryset = queryset.filter(nationality__icontains=nationality)
        
        if alive_only:
            queryset = queryset.filter(death_date__isnull=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get authors with most books",
        summary="Top authors by book count",
        tags=['Authors']
    )
    @action(detail=False, methods=['get'])
    def top_authors(self, request):
        """Get authors with the most books"""
        queryset = self.get_queryset().filter(
            books_count__gt=0
        ).order_by('-books_count')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get authors by nationality",
        summary="Authors by nationality",
        tags=['Authors']
    )
    @action(detail=False, methods=['get'])
    def by_nationality(self, request):
        """Get authors grouped by nationality"""
        nationality = request.query_params.get('nationality', '')
        if not nationality:
            return Response(
                {'error': 'Nationality parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(nationality__icontains=nationality)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data) 