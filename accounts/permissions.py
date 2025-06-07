"""
Professional Permission Classes for Library Management System
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class IsSelfOrLibrarianOrReadOnly(permissions.BasePermission):
    """
    Permission that allows users to edit their own profile,
    or allows librarians/admins to edit any profile.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for profile owner or librarian/admin
        if hasattr(obj, 'id'):  # User object
            return (obj == request.user or 
                   request.user.role in ['super_admin', 'librarian'])
        
        return False


class IsLibrarianOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to authenticated users,
    but write access only to librarians and admins.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions only for librarians and admins
        return request.user.role in ['super_admin', 'librarian']


class IsAdminOrLibrarianOnly(permissions.BasePermission):
    """
    Permission that allows access only to administrators and librarians.
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role in ['super_admin', 'librarian'])


class IsTeacherOrAbove(permissions.BasePermission):
    """
    Permission that allows access to teachers, librarians, and admins.
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role in ['super_admin', 'librarian', 'teacher'])


class IsSuperAdminOnly(permissions.BasePermission):
    """
    Permission that allows access only to super administrators.
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role == 'super_admin')


class CanBorrowBooks(permissions.BasePermission):
    """
    Permission to check if user can borrow books.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Check if user account is active and verified
        return (request.user.account_status == 'active' and
                request.user.email_verification_status == 'verified')


class CanManageLoans(permissions.BasePermission):
    """
    Permission to manage loan operations (approve, extend, etc.).
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role in ['super_admin', 'librarian'])

    def has_object_permission(self, request, view, obj):
        # Users can view their own loans
        if request.method in permissions.SAFE_METHODS:
            return (obj.user == request.user or 
                   request.user.role in ['super_admin', 'librarian'])
        
        # Only librarians can modify loans
        return request.user.role in ['super_admin', 'librarian']


class RoleBasedPermission(permissions.BasePermission):
    """
    Dynamic permission based on user roles and actions.
    """
    
    # Define role hierarchy
    ROLE_HIERARCHY = {
        'super_admin': 100,
        'librarian': 80,
        'teacher': 60,
        'student': 40,
        'member': 20,
    }
    
    # Define minimum role requirements for actions
    ACTION_PERMISSIONS = {
        'create': 'librarian',
        'update': 'librarian', 
        'partial_update': 'librarian',
        'destroy': 'super_admin',
        'list': 'member',
        'retrieve': 'member',
    }
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        user_role = request.user.role
        action = getattr(view, 'action', None)
        
        # Get required role for this action
        required_role = self.ACTION_PERMISSIONS.get(action, 'member')
        
        # Check if user's role is sufficient
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        
        return user_level >= required_level


class IsAccountActive(permissions.BasePermission):
    """
    Permission to check if user account is active.
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.account_status == 'active')


class IsEmailVerified(permissions.BasePermission):
    """
    Permission to check if user's email is verified.
    """
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.email_verification_status == 'verified')


class CombinedPermission(permissions.BasePermission):
    """
    Combines multiple permission classes with AND logic.
    """
    
    def __init__(self, *permission_classes):
        self.permission_classes = permission_classes
    
    def has_permission(self, request, view):
        for permission_class in self.permission_classes:
            permission = permission_class()
            if not permission.has_permission(request, view):
                return False
        return True
    
    def has_object_permission(self, request, view, obj):
        for permission_class in self.permission_classes:
            permission = permission_class()
            if hasattr(permission, 'has_object_permission'):
                if not permission.has_object_permission(request, view, obj):
                    return False
        return True 