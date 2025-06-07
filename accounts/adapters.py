"""
Custom Allauth Adapters for JWT Integration
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model
from django.http import HttpResponse
import json

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for JWT integration
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user with additional fields
        """
        data = form.cleaned_data
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        username = data.get('username')
        
        user_email(user, email)
        user_username(user, username)
        if first_name:
            user_field(user, 'first_name', first_name)
        if last_name:
            user_field(user, 'last_name', last_name)
            
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for JWT integration
    """
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user from social login with additional processing
        """
        user = sociallogin.user
        user.set_unusable_password()
        
        # Extract data from social account
        extra_data = sociallogin.account.extra_data
        
        # Set additional fields from Google
        if sociallogin.account.provider == 'google':
            if 'given_name' in extra_data:
                user.first_name = extra_data['given_name']
            if 'family_name' in extra_data:
                user.last_name = extra_data['family_name']
            if 'picture' in extra_data:
                # You can save profile picture URL here
                pass
        
        # Set default role for social users
        if not user.role:
            user.role = 'member'
            
        # Set email as verified since it comes from trusted provider
        user.email_verification_status = 'verified'
        user.account_status = 'active'
        
        user.save()
        return user
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle existing users trying to login with social account
        """
        # Check if user with this email already exists
        if sociallogin.is_existing:
            return
            
        try:
            user = User.objects.get(email=sociallogin.user.email)
            # Link the social account to existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Handle authentication errors
        """
        error_data = {
            'error': 'social_auth_failed',
            'provider': provider_id,
            'message': 'Social authentication failed'
        }
        if error:
            error_data['details'] = str(error)
            
        return HttpResponse(
            json.dumps(error_data),
            content_type='application/json',
            status=400
        ) 