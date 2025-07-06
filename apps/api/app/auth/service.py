"""
Authentication service for handling Google OAuth and JWT tokens
"""
import re
from typing import Dict, Optional
from google.auth.transport import requests
from google.oauth2 import id_token
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models.user import User
from app import db


class AuthService:
    """Service class for authentication operations"""
    
    def validate_google_token(self, auth_code: str) -> Optional[Dict]:
        """
        Validate Google OAuth authorization code and return user profile
        
        Args:
            auth_code: Authorization code from Google OAuth
            
        Returns:
            Dict with user profile data or None if invalid
        """
        try:
            # Exchange authorization code for tokens using Google OAuth2 flow
            from google_auth_oauthlib.flow import Flow
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                        "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
                    }
                },
                scopes=['openid', 'email', 'profile']
            )
            flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
            
            # Fetch token using the authorization code
            token = flow.fetch_token(code=auth_code)
            
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(
                token['id_token'], 
                requests.Request(), 
                current_app.config['GOOGLE_CLIENT_ID']
            )
            
            return {
                'email': idinfo.get('email'),
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture'),
                'sub': idinfo.get('sub')
            }
            
        except Exception as e:
            current_app.logger.error(f"Google token validation failed: {str(e)}")
            return None
    
    def create_or_get_user(self, google_profile: Dict) -> User:
        """
        Create new user or get existing user from Google profile
        
        Args:
            google_profile: User profile data from Google
            
        Returns:
            User instance
        """
        # First try to find user by email
        user = User.query.filter_by(email=google_profile['email']).first()
        
        if not user:
            # Extract company domain from email
            company_domain = self.extract_company_domain(google_profile['email'])
            
            # Create new user
            user = User(
                email=google_profile['email'],
                full_name=google_profile['name'],
                google_id=google_profile['sub'],
                avatar_url=google_profile.get('picture'),
                company_domain=company_domain
            )
            
            db.session.add(user)
            db.session.commit()
        else:
            # Update existing user with latest Google data
            user.google_id = google_profile['sub']
            user.avatar_url = google_profile.get('picture')
            user.full_name = google_profile['name']
            db.session.commit()
        
        return user
    
    def generate_tokens(self, user: User) -> Dict[str, any]:
        """
        Generate JWT access and refresh tokens for user
        
        Args:
            user: User instance
            
        Returns:
            Dict with access_token, refresh_token, and expires_in
        """
        # Create tokens with user ID as identity
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'email': user.email}
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900  # 15 minutes
        }
    
    def extract_company_domain(self, email: str) -> Optional[str]:
        """
        Extract company domain from email address
        
        Args:
            email: Email address
            
        Returns:
            Company domain or None if invalid email
        """
        if not email or '@' not in email:
            return None
            
        try:
            domain = email.split('@')[1]
            # Basic email domain validation
            if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,})+$', domain):
                return domain
            return None
        except (IndexError, AttributeError):
            return None


def verify_google_token(token: str) -> Optional[Dict]:
    """
    Standalone function to verify Google ID token
    Used for easier mocking in tests
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), current_app.config['GOOGLE_CLIENT_ID']
        )
        return idinfo
    except ValueError:
        return None