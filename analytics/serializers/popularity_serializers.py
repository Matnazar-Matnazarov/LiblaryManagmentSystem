"""
Book Popularity Serializers

Professional serializers for book popularity analytics with:
- Popularity metrics tracking
- Trending books analysis
- Engagement statistics
- Rating and view metrics
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from ..models import BookPopularity
from books.serializers import BookListSerializer


class BookPopularitySerializer(serializers.ModelSerializer):
    """
    Basic book popularity serializer for list views
    """
    book = BookListSerializer(read_only=True)
    popularity_score = serializers.FloatField(read_only=True)
    
    class Meta:
        model = BookPopularity
        fields = [
            'id', 'book', 'total_views', 'weekly_views', 'monthly_views',
            'total_borrows', 'monthly_borrows', 'average_rating', 'total_ratings',
            'current_reservations', 'popularity_score', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class BookPopularityDetailSerializer(BookPopularitySerializer):
    """
    Detailed book popularity serializer with full metrics
    """
    click_through_rate = serializers.SerializerMethodField()
    engagement_rate = serializers.SerializerMethodField()
    trending_score = serializers.SerializerMethodField()
    
    class Meta(BookPopularitySerializer.Meta):
        fields = BookPopularitySerializer.Meta.fields + [
            'daily_views', 'yearly_borrows', 'search_appearances', 
            'search_clicks', 'total_reservations', 'last_viewed', 
            'last_borrowed', 'click_through_rate', 'engagement_rate',
            'trending_score'
        ]
    
    def get_click_through_rate(self, obj):
        """Calculate click-through rate from search results"""
        if obj.search_appearances > 0:
            return round((obj.search_clicks / obj.search_appearances) * 100, 2)
        return 0.0
    
    def get_engagement_rate(self, obj):
        """Calculate engagement rate (borrows per view)"""
        if obj.total_views > 0:
            return round((obj.total_borrows / obj.total_views) * 100, 2)
        return 0.0
    
    def get_trending_score(self, obj):
        """Calculate trending score based on recent activity"""
        # Weight recent activity more heavily
        weekly_weight = 0.4
        monthly_weight = 0.3
        rating_weight = 0.2
        reservation_weight = 0.1
        
        weekly_score = min(obj.weekly_views + (obj.monthly_borrows * 5), 100) * weekly_weight
        monthly_score = min(obj.monthly_views + (obj.monthly_borrows * 3), 100) * monthly_weight
        rating_score = obj.average_rating * 20 * rating_weight if obj.total_ratings > 0 else 0
        reservation_score = min(obj.current_reservations * 10, 100) * reservation_weight
        
        return round(weekly_score + monthly_score + rating_score + reservation_score, 2)


class TrendingBooksSerializer(serializers.Serializer):
    """
    Serializer for trending books analytics
    """
    # Time period
    period = serializers.CharField()
    generated_at = serializers.DateTimeField()
    
    # Trending books lists
    most_viewed = BookPopularitySerializer(many=True)
    most_borrowed = BookPopularitySerializer(many=True)
    fastest_growing = BookPopularitySerializer(many=True)
    highest_rated = BookPopularitySerializer(many=True)
    most_reserved = BookPopularitySerializer(many=True)
    
    # Trend statistics
    total_views_period = serializers.IntegerField()
    total_borrows_period = serializers.IntegerField()
    avg_rating_period = serializers.FloatField()
    growth_rate = serializers.FloatField()
    
    # Category breakdown
    popular_categories = serializers.ListField()
    trending_authors = serializers.ListField()


class PopularityUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating popularity metrics
    """
    book_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=[
        ('view', 'View'),
        ('borrow', 'Borrow'),
        ('search_appearance', 'Search Appearance'),
        ('search_click', 'Search Click'),
        ('rate', 'Rate'),
        ('reserve', 'Reserve')
    ])
    rating = serializers.FloatField(required=False, min_value=0.0, max_value=5.0)
    
    def validate(self, attrs):
        """Validate update data"""
        if attrs['action'] == 'rate' and 'rating' not in attrs:
            raise serializers.ValidationError("Rating is required for rate action.")
        return attrs
    
    def update_popularity(self):
        """Update book popularity based on action"""
        from books.models import Book
        
        book_id = self.validated_data['book_id']
        action = self.validated_data['action']
        
        try:
            book = Book.objects.get(id=book_id)
            popularity, created = BookPopularity.objects.get_or_create(book=book)
            
            if action == 'view':
                popularity.increment_views()
            elif action == 'borrow':
                popularity.increment_borrows()
            elif action == 'search_appearance':
                popularity.search_appearances += 1
                popularity.calculate_popularity_score()
                popularity.save()
            elif action == 'search_click':
                popularity.search_clicks += 1
                popularity.calculate_popularity_score()
                popularity.save()
            elif action == 'rate':
                rating = self.validated_data['rating']
                # Update average rating
                total_rating_points = popularity.average_rating * popularity.total_ratings
                popularity.total_ratings += 1
                popularity.average_rating = (total_rating_points + rating) / popularity.total_ratings
                popularity.calculate_popularity_score()
                popularity.save()
            elif action == 'reserve':
                popularity.total_reservations += 1
                popularity.current_reservations += 1
                popularity.calculate_popularity_score()
                popularity.save()
            
            return popularity
            
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book not found.")


class BookEngagementSerializer(serializers.Serializer):
    """
    Serializer for book engagement analytics
    """
    book = BookListSerializer()
    
    # Engagement metrics
    view_to_borrow_rate = serializers.FloatField()
    search_to_click_rate = serializers.FloatField()
    view_to_reservation_rate = serializers.FloatField()
    
    # Time-based metrics
    avg_time_to_borrow = serializers.FloatField()  # days from first view to borrow
    peak_interest_period = serializers.CharField()  # when book gets most attention
    
    # User behavior
    repeat_viewers = serializers.IntegerField()
    user_retention_rate = serializers.FloatField()
    
    # Comparative metrics
    category_rank = serializers.IntegerField()
    author_rank = serializers.IntegerField()
    overall_rank = serializers.IntegerField()


class PopularityTrendsSerializer(serializers.Serializer):
    """
    Serializer for popularity trend analysis
    """
    book = BookListSerializer()
    
    # Trend data (time series)
    daily_trends = serializers.ListField()
    weekly_trends = serializers.ListField()
    monthly_trends = serializers.ListField()
    
    # Trend analysis
    trend_direction = serializers.CharField()  # 'rising', 'falling', 'stable'
    trend_strength = serializers.FloatField()  # 0-100
    growth_rate = serializers.FloatField()
    
    # Predictions
    predicted_next_week = serializers.FloatField()
    predicted_next_month = serializers.FloatField()
    seasonality_pattern = serializers.CharField()


class CategoryPopularitySerializer(serializers.Serializer):
    """
    Serializer for category-wise popularity analytics
    """
    category_name = serializers.CharField()
    category_id = serializers.IntegerField()
    
    # Aggregate metrics
    total_books = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_borrows = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    
    # Top performers
    most_popular_book = BookPopularitySerializer()
    fastest_growing_book = BookPopularitySerializer()
    highest_rated_book = BookPopularitySerializer()
    
    # Trends
    growth_rate = serializers.FloatField()
    market_share = serializers.FloatField()  # percentage of total activity


class AuthorPopularitySerializer(serializers.Serializer):
    """
    Serializer for author popularity analytics
    """
    author_name = serializers.CharField()
    author_id = serializers.IntegerField()
    
    # Book metrics
    total_books = serializers.IntegerField()
    published_books = serializers.IntegerField()
    
    # Popularity metrics
    total_views = serializers.IntegerField()
    total_borrows = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    total_ratings = serializers.IntegerField()
    
    # Top books
    most_popular_books = BookPopularitySerializer(many=True)
    latest_book_performance = BookPopularitySerializer()
    
    # Author trends
    popularity_trend = serializers.CharField()
    reader_loyalty = serializers.FloatField()  # how often users read multiple books by same author


class SearchAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for search-related popularity analytics
    """
    # Search terms
    top_search_terms = serializers.ListField()
    trending_search_terms = serializers.ListField()
    no_result_searches = serializers.ListField()
    
    # Book performance in search
    most_searched_books = BookPopularitySerializer(many=True)
    highest_click_through_books = BookPopularitySerializer(many=True)
    search_position_performance = serializers.ListField()
    
    # Search behavior
    avg_results_per_search = serializers.FloatField()
    avg_clicks_per_search = serializers.FloatField()
    search_to_borrow_conversion = serializers.FloatField()
    
    # Search improvements
    suggested_new_books = serializers.ListField()
    underperforming_books = serializers.ListField() 