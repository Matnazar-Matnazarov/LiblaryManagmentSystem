from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import jwt
import requests
import logging
import json
import string
import random
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

User = get_user_model()
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = "322786648793-lahah2h86g0pgfe45ips0rua3tp1ngtv.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

@method_decorator(csrf_exempt, name='dispatch')
class CustomGoogleLoginView(APIView):
    """
    Custom view to handle Google login without relying on the allauth adapter
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access
    
    def post(self, request, *args, **kwargs):
        try:
            # Log request
            logger.info(f"Google login request received at: {request.path}")
            print(f"Google login request headers: {request.headers}")
            print(f"Google login request body: {request.data}")
            print(f"Role received in request: {request.data.get('role', 'Not provided')}")
            
            # Set CORS headers for the actual response
            response_headers = {
                'Access-Control-Allow-Origin': request.headers.get('Origin', 'http://localhost:3000'),
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
                'Access-Control-Allow-Credentials': 'true',
            }
            
            # Check for token
            access_token = request.data.get('access_token')
            if not access_token:
                return Response(
                    {"detail": "Missing access_token"}, 
                    status=status.HTTP_400_BAD_REQUEST,
                    headers=response_headers
                )
            
            try:
                # First check if we have an ID token (JWT from Google)
                try:
                    # Try to decode the token as an ID token (JWT from Google)
                    decoded_token = jwt.decode(
                        access_token,
                        options={"verify_signature": False},
                        algorithms=["RS256"]
                    )
                    print(f"Decoded ID token: {decoded_token}")
                    
                    # Extract user info from the token
                    user_info = {
                        'id': decoded_token.get('sub'),
                        'email': decoded_token.get('email'),
                        'verified_email': decoded_token.get('email_verified', True),
                        'name': decoded_token.get('name'),
                        'given_name': decoded_token.get('given_name'),
                        'family_name': decoded_token.get('family_name'),
                        'picture': decoded_token.get('picture')
                    }
                except Exception as jwt_error:
                    # Not a JWT, maybe an access token - try to get user info from Google
                    print(f"Not a JWT or error decoding: {str(jwt_error)}")
                    print("Trying to get user info from Google API")
                    userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
                    headers = {'Authorization': f'Bearer {access_token}'}
                    
                    userinfo_response = requests.get(userinfo_url, headers=headers)
                    if userinfo_response.status_code != 200:
                        raise Exception(f"Failed to get user info from Google: {userinfo_response.text}")
                    
                    user_data = userinfo_response.json()
                    user_info = {
                        'id': user_data.get('sub'),
                        'email': user_data.get('email'),
                        'verified_email': user_data.get('email_verified', True),
                        'name': user_data.get('name'),
                        'given_name': user_data.get('given_name'),
                        'family_name': user_data.get('family_name'),
                        'picture': user_data.get('picture')
                    }
                
                print(f"User info: {user_info}")
                
                if not user_info.get('email'):
                    return Response(
                        {"detail": "Email not provided by Google"}, 
                        status=status.HTTP_400_BAD_REQUEST,
                        headers=response_headers
                    )
                
                # Get or create user
                social_email = user_info.get('email')
                
                try:
                    email_address = EmailAddress.objects.get(email=social_email)
                    user = email_address.user
                except EmailAddress.DoesNotExist:
                    # Create user if doesn't exist
                    if not User.objects.filter(email=social_email).exists():
                        username = social_email.split('@')[0]
                        # Ensure username is unique
                        if User.objects.filter(username=username).exists():
                            username = f"{username}_{User.objects.count()}"
                        
                        # Generate a random password
                        random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                        
                        # Get role from request data or default to 'CLIENT'
                        role = request.data.get('role', 'CLIENT')
                        if role not in ['CLIENT', 'MASTER']:
                            role = 'CLIENT'  # Fallback to CLIENT if invalid role
                        
                        print(f"Creating user with role: {role}")
                        
                        user = User.objects.create_user(
                            username=username,
                            email=social_email,
                            first_name=user_info.get('given_name', ''),
                            last_name=user_info.get('family_name', ''),
                            password=random_password,
                            is_active=True,
                            role=role  # Use the role from request or default
                        )
                        EmailAddress.objects.create(
                            user=user,
                            email=social_email,
                            primary=True,
                            verified=True
                        )
                    else:
                        user = User.objects.get(email=social_email)
                        
                        # Update role if provided in request
                        if 'role' in request.data and request.data['role'] in ['CLIENT', 'MASTER']:
                            user.role = request.data['role']
                            user.save()
                            print(f"Updated user role to: {user.role}")
                
                # Create or get social account
                try:
                    social_account = SocialAccount.objects.get(provider='google', user=user)
                except SocialAccount.DoesNotExist:
                    social_account = SocialAccount.objects.create(
                        provider='google',
                        user=user,
                        uid=user_info.get('id'),
                        extra_data=user_info
                    )
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Format user data
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'role': user.role,
                    'is_active': user.is_active,
                    'picture': request.build_absolute_uri(user.picture.url) if hasattr(user, 'picture') and user.picture else user_info.get('picture'),
                }
                
                # Format response
                formatted_response = {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': user_data
                }
                
                print(f"Google login successful for user: {user.email}")
                
                # Return response with CORS headers
                response = JsonResponse(formatted_response)
                for header, value in response_headers.items():
                    response[header] = value
                
                return response
                
            except Exception as e:
                logger.exception(f"Error in Google authentication: {str(e)}")
                print(f"Google login error: {str(e)}")
                
                response = JsonResponse(
                    {"detail": f"Google authentication failed: {str(e)}"},
                    status=400
                )
                
                for header, value in response_headers.items():
                    response[header] = value
                
                return response
            
        except Exception as e:
            logger.exception(f"Google login exception: {str(e)}")
            print(f"Google login exception: {str(e)}")
            
            response = JsonResponse(
                {"detail": f"Google login failed: {str(e)}"},
                status=500
            )
            
            response["Access-Control-Allow-Origin"] = request.headers.get('Origin', 'http://localhost:3000')
            response["Access-Control-Allow-Credentials"] = "true"
            
            return response
    
    def options(self, request, *args, **kwargs):
        """
        Handle preflight OPTIONS requests for CORS
        """
        print(f"OPTIONS request received at: {request.path}")
        print(f"OPTIONS request headers: {request.headers}")
        
        response = JsonResponse({})
        
        response["Access-Control-Allow-Origin"] = request.headers.get('Origin', 'http://localhost:3000')
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response 