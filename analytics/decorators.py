"""
Professional Model Monitoring Decorators

Bu modul har bir model uchun monitoring decorator larini taqdim etadi:
- Performance tracking
- Query optimization monitoring
- Cache efficiency tracking
- Error rate monitoring
"""

import time
import functools
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
import logging

from .monitoring import (
    db_query_duration,
    cache_operations_total,
    api_request_duration,
    update_error_rate
)

logger = logging.getLogger(__name__)


def monitor_user_model_performance(func):
    """
    User model performance monitoring decorator
    
    Foydalanuvchi modeli uchun performance monitoring:
    - Query time tracking
    - Cache hit/miss rates
    - Response time monitoring
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            
            # Performance metrikalari
            execution_time = time.time() - start_time
            query_count = len(connection.queries) - initial_queries
            
            # Cache ga saqlash
            cache.set('user_model_response_time', execution_time, 300)
            cache.set('user_model_query_count', query_count, 300)
            
            # Prometheus metrics
            db_query_duration.labels(
                model='User',
                operation=func.__name__
            ).observe(execution_time)
            
            logger.debug(f"User model operation {func.__name__}: {execution_time:.3f}s, {query_count} queries")
            
            return result
            
        except Exception as e:
            # Xatolik darajasini yangilash
            error_count = cache.get('user_model_errors', 0) + 1
            total_requests = cache.get('user_model_requests', 0) + 1
            
            cache.set('user_model_errors', error_count, 3600)
            cache.set('user_model_requests', total_requests, 3600)
            
            update_error_rate('user_model', error_count, total_requests)
            
            logger.error(f"User model error in {func.__name__}: {e}")
            raise
        
        finally:
            # Umumiy so'rovlar sonini yangilash
            total_requests = cache.get('user_model_requests', 0) + 1
            cache.set('user_model_requests', total_requests, 3600)
    
    return wrapper


def monitor_book_model_performance(func):
    """
    Book model performance monitoring decorator
    
    Kitob modeli uchun performance monitoring:
    - Inventory tracking
    - Search performance
    - Popularity calculations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            
            # Performance metrikalari
            execution_time = time.time() - start_time
            query_count = len(connection.queries) - initial_queries
            
            # Cache ga saqlash
            cache.set('book_model_response_time', execution_time, 300)
            cache.set('book_model_query_count', query_count, 300)
            
            # Prometheus metrics
            db_query_duration.labels(
                model='Book',
                operation=func.__name__
            ).observe(execution_time)
            
            # Kitob inventarini yangilash
            if 'available_copies' in str(kwargs) or 'borrow' in func.__name__.lower():
                cache.delete('book_inventory_stats')
            
            logger.debug(f"Book model operation {func.__name__}: {execution_time:.3f}s, {query_count} queries")
            
            return result
            
        except Exception as e:
            # Xatolik darajasini yangilash
            error_count = cache.get('book_model_errors', 0) + 1
            total_requests = cache.get('book_model_requests', 0) + 1
            
            cache.set('book_model_errors', error_count, 3600)
            cache.set('book_model_requests', total_requests, 3600)
            
            update_error_rate('book_model', error_count, total_requests)
            
            logger.error(f"Book model error in {func.__name__}: {e}")
            raise
        
        finally:
            # Umumiy so'rovlar sonini yangilash
            total_requests = cache.get('book_model_requests', 0) + 1
            cache.set('book_model_requests', total_requests, 3600)
    
    return wrapper


def monitor_loan_model_performance(func):
    """
    Loan model performance monitoring decorator
    
    Qarz modeli uchun performance monitoring:
    - Loan processing time
    - Overdue calculations
    - Fine calculations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            
            # Performance metrikalari
            execution_time = time.time() - start_time
            query_count = len(connection.queries) - initial_queries
            
            # Cache ga saqlash
            cache.set('loan_model_response_time', execution_time, 300)
            cache.set('loan_model_query_count', query_count, 300)
            
            # Prometheus metrics
            db_query_duration.labels(
                model='Loan',
                operation=func.__name__
            ).observe(execution_time)
            
            # Qarz statistikalarini yangilash
            if any(keyword in func.__name__.lower() for keyword in ['create', 'return', 'overdue']):
                cache.delete('loan_statistics')
                cache.delete('overdue_loans_count')
            
            logger.debug(f"Loan model operation {func.__name__}: {execution_time:.3f}s, {query_count} queries")
            
            return result
            
        except Exception as e:
            # Xatolik darajasini yangilash
            error_count = cache.get('loan_model_errors', 0) + 1
            total_requests = cache.get('loan_model_requests', 0) + 1
            
            cache.set('loan_model_errors', error_count, 3600)
            cache.set('loan_model_requests', total_requests, 3600)
            
            update_error_rate('loan_model', error_count, total_requests)
            
            logger.error(f"Loan model error in {func.__name__}: {e}")
            raise
        
        finally:
            # Umumiy so'rovlar sonini yangilash
            total_requests = cache.get('loan_model_requests', 0) + 1
            cache.set('loan_model_requests', total_requests, 3600)
    
    return wrapper


def monitor_analytics_model_performance(func):
    """
    Analytics model performance monitoring decorator
    
    Analytics modeli uchun performance monitoring:
    - Data processing time
    - Report generation
    - Statistics calculations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        try:
            result = func(*args, **kwargs)
            
            # Performance metrikalari
            execution_time = time.time() - start_time
            query_count = len(connection.queries) - initial_queries
            
            # Cache ga saqlash
            cache.set('analytics_model_response_time', execution_time, 300)
            cache.set('analytics_model_query_count', query_count, 300)
            cache.set('analytics_processing_time', execution_time, 300)
            
            # Prometheus metrics
            db_query_duration.labels(
                model='Analytics',
                operation=func.__name__
            ).observe(execution_time)
            
            # Ma'lumotlar yangilanish vaqtini belgilash
            if 'generate' in func.__name__.lower() or 'calculate' in func.__name__.lower():
                cache.set('analytics_last_update', timezone.now(), None)
            
            logger.debug(f"Analytics model operation {func.__name__}: {execution_time:.3f}s, {query_count} queries")
            
            return result
            
        except Exception as e:
            # Xatolik darajasini yangilash
            error_count = cache.get('analytics_model_errors', 0) + 1
            total_requests = cache.get('analytics_model_requests', 0) + 1
            
            cache.set('analytics_model_errors', error_count, 3600)
            cache.set('analytics_model_requests', total_requests, 3600)
            
            update_error_rate('analytics_model', error_count, total_requests)
            
            logger.error(f"Analytics model error in {func.__name__}: {e}")
            raise
        
        finally:
            # Umumiy so'rovlar sonini yangilash
            total_requests = cache.get('analytics_model_requests', 0) + 1
            cache.set('analytics_model_requests', total_requests, 3600)
    
    return wrapper


def monitor_cache_efficiency(cache_name):
    """
    Cache efficiency monitoring decorator
    
    Kesh samaradorligini kuzatish:
    - Hit/miss rates
    - Cache performance
    - Memory usage
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation = func.__name__
            
            try:
                result = func(*args, **kwargs)
                
                # Cache hit/miss tracking
                if result is not None:
                    hit_miss = 'hit'
                    # Hit rate ni yangilash
                    hits = cache.get(f'{cache_name}_hits', 0) + 1
                    cache.set(f'{cache_name}_hits', hits, 3600)
                else:
                    hit_miss = 'miss'
                    # Miss rate ni yangilash
                    misses = cache.get(f'{cache_name}_misses', 0) + 1
                    cache.set(f'{cache_name}_misses', misses, 3600)
                
                # Prometheus metrics
                cache_operations_total.labels(
                    operation=operation,
                    cache_name=cache_name,
                    hit_miss=hit_miss
                ).inc()
                
                # Cache efficiency hisoblash
                hits = cache.get(f'{cache_name}_hits', 0)
                misses = cache.get(f'{cache_name}_misses', 0)
                total = hits + misses
                
                if total > 0:
                    efficiency = (hits / total) * 100
                    cache.set(f'{cache_name}_efficiency', efficiency, 3600)
                
                return result
                
            except Exception as e:
                # Cache error tracking
                cache_operations_total.labels(
                    operation=operation,
                    cache_name=cache_name,
                    hit_miss='error'
                ).inc()
                
                logger.error(f"Cache error in {cache_name}.{operation}: {e}")
                raise
        
        return wrapper
    return decorator


def monitor_api_endpoint(endpoint_name):
    """
    API endpoint monitoring decorator
    
    API endpoint lar uchun monitoring:
    - Response time
    - Status codes
    - Request rates
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            method = request.method
            
            try:
                response = func(request, *args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                
                # Success tracking
                success_count = cache.get(f'{endpoint_name}_success', 0) + 1
                cache.set(f'{endpoint_name}_success', success_count, 3600)
                
                return response
                
            except Exception as e:
                status_code = 500
                
                # Error tracking
                error_count = cache.get(f'{endpoint_name}_errors', 0) + 1
                cache.set(f'{endpoint_name}_errors', error_count, 3600)
                
                logger.error(f"API endpoint error in {endpoint_name}: {e}")
                raise
                
            finally:
                # Performance tracking
                duration = time.time() - start_time
                
                # Prometheus metrics
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint_name,
                    status_code=status_code
                ).observe(duration)
                
                # Cache ga saqlash
                cache.set(f'{endpoint_name}_last_response_time', duration, 300)
                
                # Request rate tracking
                total_requests = cache.get(f'{endpoint_name}_requests', 0) + 1
                cache.set(f'{endpoint_name}_requests', total_requests, 3600)
        
        return wrapper
    return decorator


def monitor_database_queries(model_name):
    """
    Database query monitoring decorator
    
    Ma'lumotlar bazasi so'rovlarini kuzatish:
    - Query count
    - Execution time
    - Query optimization
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            initial_queries = len(connection.queries)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Query metrics
                query_count = len(connection.queries) - initial_queries
                execution_time = time.time() - start_time
                
                # Prometheus metrics
                db_query_duration.labels(
                    model=model_name,
                    operation=func.__name__
                ).observe(execution_time)
                
                # Query optimization alerts
                if query_count > 10:
                    logger.warning(f"High query count in {model_name}.{func.__name__}: {query_count} queries")
                
                if execution_time > 1.0:  # 1 soniya
                    logger.warning(f"Slow query in {model_name}.{func.__name__}: {execution_time:.3f}s")
                
                # Cache ga saqlash
                cache.set(f'{model_name}_last_query_count', query_count, 300)
                cache.set(f'{model_name}_last_query_time', execution_time, 300)
                
                return result
                
            except Exception as e:
                logger.error(f"Database query error in {model_name}.{func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator 