"""
Analytics Serializers Module

Professional serializers for analytics data with:
- Activity tracking serializers
- Book popularity metrics serializers
- System statistics serializers
- Custom report serializers
"""

from .activity_serializers import (
    ActivityLogSerializer,
    ActivityLogDetailSerializer,
    ActivityLogCreateSerializer,
    ActivitySummarySerializer,
)

from .popularity_serializers import (
    BookPopularitySerializer,
    BookPopularityDetailSerializer,
    TrendingBooksSerializer,
    PopularityUpdateSerializer,
)

from .statistics_serializers import (
    SystemStatisticsSerializer,
    DashboardStatsSerializer,
    UserActivityStatsSerializer,
    BookStatsSerializer,
    FinancialStatsSerializer,
    SystemHealthSerializer,
    ComparativeStatsSerializer,
    ReportSummarySerializer,
)

from .report_serializers import (
    CustomReportSerializer,
    CustomReportDetailSerializer,
    CustomReportCreateSerializer,
    ReportGenerationSerializer,
    ReportExportSerializer,
)

__all__ = [
    # Activity serializers
    'ActivityLogSerializer',
    'ActivityLogDetailSerializer', 
    'ActivityLogCreateSerializer',
    'ActivitySummarySerializer',
    
    # Popularity serializers
    'BookPopularitySerializer',
    'BookPopularityDetailSerializer',
    'TrendingBooksSerializer',
    'PopularityUpdateSerializer',
    
    # Statistics serializers
    'SystemStatisticsSerializer',
    'DashboardStatsSerializer',
    'UserActivityStatsSerializer',
    'BookStatsSerializer',
    'FinancialStatsSerializer',
    'SystemHealthSerializer',
    'ComparativeStatsSerializer',
    'ReportSummarySerializer',
    
    # Report serializers
    'CustomReportSerializer',
    'CustomReportDetailSerializer',
    'CustomReportCreateSerializer',
    'ReportGenerationSerializer',
    'ReportExportSerializer',
] 