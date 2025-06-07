"""
Professional Publisher Management Views
"""
from django.db.models import Count, Q
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..models import Publisher
from ..serializers import PublisherSerializer
from accounts.permissions import (
    IsLibrarianOrReadOnly,
    IsAccountActive
)


@extend_schema_view(
    list=extend_schema(
        description="List all publishers with book counts and contact information",
        summary="Get publishers list",
        tags=['Publishers']
    ),
    create=extend_schema(
        description="Create a new publisher profile",
        summary="Create new publisher",
        tags=['Publishers']
    ),
    retrieve=extend_schema(
        description="Get detailed publisher information with book statistics",
        summary="Get publisher details",
        tags=['Publishers']
    ),
    update=extend_schema(
        description="Update publisher information completely",
        summary="Update publisher",
        tags=['Publishers']
    ),
    partial_update=extend_schema(
        description="Partially update publisher information",
        summary="Partially update publisher",
        tags=['Publishers']
    ),
    destroy=extend_schema(
        description="Delete publisher from the system",
        summary="Delete publisher",
        tags=['Publishers']
    ),
)
class PublisherViewSet(viewsets.ModelViewSet):
    """
    Professional ViewSet for managing publishers with advanced optimizations
    
    Features:
    - Optimized queries with prefetch_related for books
    - Advanced filtering and search capabilities
    - Role-based permissions
    - Professional pagination
    - Statistics and analytics
    """
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountActive, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Advanced filtering options
    filterset_fields = {
        'city': ['exact', 'icontains'],
        'country': ['exact', 'icontains'],
    }
    
    # Search across multiple fields
    search_fields = ['name', 'address', 'city', 'country', 'website', 'email']
    
    # Ordering options
    ordering_fields = ['name', 'city', 'country', 'created_at', 'updated_at']
    ordering = ['name']  # Default ordering
    
    def get_queryset(self):
        """
        Get optimized queryset with book counts and related data
        """
        return Publisher.objects.prefetch_related(
            'books__authors', 'books__category'
        ).annotate(
            books_count=Count('books', distinct=True),
            available_books_count=Count(
                'books',
                filter=Q(books__status='available', books__available_copies__gt=0),
                distinct=True
            )
        )
    
    @extend_schema(
        description="Search publishers by name, location or contact information",
        summary="Advanced publisher search",
        tags=['Publishers']
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with multiple criteria"""
        queryset = self.get_queryset()
        
        # Get search parameters
        query = request.query_params.get('q', '')
        city = request.query_params.get('city', '')
        country = request.query_params.get('country', '')
        has_books = request.query_params.get('has_books', 'false').lower() == 'true'
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(website__icontains=query) |
                Q(email__icontains=query)
            )
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        if has_books:
            queryset = queryset.filter(books_count__gt=0)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get publishers with most books",
        summary="Top publishers by book count",
        tags=['Publishers']
    )
    @action(detail=False, methods=['get'])
    def top_publishers(self, request):
        """Get publishers with the most books"""
        queryset = self.get_queryset().filter(
            books_count__gt=0
        ).order_by('-books_count')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get publishers by location",
        summary="Publishers by location",
        tags=['Publishers']
    )
    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get publishers by city or country"""
        city = request.query_params.get('city', '')
        country = request.query_params.get('country', '')
        
        if not city and not country:
            return Response(
                {'error': 'City or country parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get publisher statistics",
        summary="Publisher statistics",
        tags=['Publishers']
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a specific publisher"""
        publisher = self.get_object()
        
        # Get additional statistics
        total_books = publisher.books.count()
        available_books = publisher.books.filter(
            status='available',
            available_copies__gt=0
        ).count()
        
        # Get books by category
        books_by_category = publisher.books.values(
            'category__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'publisher': PublisherSerializer(publisher).data,
            'statistics': {
                'total_books': total_books,
                'available_books': available_books,
                'checkout_rate': ((total_books - available_books) / total_books * 100) if total_books > 0 else 0,
                'books_by_category': books_by_category,
            }
        }) 