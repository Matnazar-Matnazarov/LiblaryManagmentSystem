"""
Professional DRF Spectacular hooks for API documentation
"""
from typing import Dict, Set, List, Any


# Official API tags that should be used
OFFICIAL_TAGS = [
    'Authentication',
    'Users', 
    'Books',
    'Authors',
    'Categories',
    'Publishers',
    'Loans',
    'Analytics',
    'Notifications'
]


def fix_duplicate_tags(result: Dict[str, Any], generator, request, public) -> Dict[str, Any]:
    """
    Fix duplicate tags and organize API schema structure
    
    Args:
        result: OpenAPI schema result
        generator: Schema generator instance
        request: HTTP request object
        public: Whether schema is public
        
    Returns:
        Cleaned OpenAPI schema with standardized tags
    """
    # Remove duplicate tags
    if 'tags' in result:
        seen_tags = set()
        unique_tags = []
        
        for tag in result['tags']:
            tag_name = tag.get('name', '')
            if tag_name not in seen_tags:
                seen_tags.add(tag_name)
                unique_tags.append(tag)
        
        result['tags'] = unique_tags
    
    # Ensure consistent tag ordering
    if 'tags' in result:
        tag_order = [
            'Authentication',
            'Users', 
            'Books',
            'Authors',
            'Categories',
            'Publishers',
            'Loans',
            'Analytics',
            'Notifications',
        ]
        
        # Sort tags based on predefined order
        sorted_tags = []
        used_tags = set()
        
        # Add tags in predefined order
        for tag_name in tag_order:
            for tag in result['tags']:
                if tag.get('name') == tag_name and tag_name not in used_tags:
                    sorted_tags.append(tag)
                    used_tags.add(tag_name)
                    break
        
        # Add any remaining tags
        for tag in result['tags']:
            tag_name = tag.get('name', '')
            if tag_name not in used_tags:
                sorted_tags.append(tag)
                used_tags.add(tag_name)
        
        result['tags'] = sorted_tags
    
    return result 