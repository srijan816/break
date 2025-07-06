"""
Unit tests for authentication service logic
Following TDD principles - write tests first, then implement
"""
import pytest
from unittest.mock import Mock, patch
from app.auth.service import AuthService
from app.models.user import User


class TestAuthService:
    """Test authentication service business logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auth_service = AuthService()
        
    def test_validate_google_token_success(self):
        """Test successful Google token validation"""
        # Arrange
        mock_google_response = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'sub': 'google_user_id_123'
        }
        
        # Act & Assert
        with patch('app.auth.service.verify_google_token') as mock_verify:
            mock_verify.return_value = mock_google_response
            result = self.auth_service.validate_google_token('valid_token')
            
            assert result == mock_google_response
            mock_verify.assert_called_once_with('valid_token')
    
    def test_validate_google_token_invalid(self):
        """Test Google token validation with invalid token"""
        # Act & Assert
        with patch('app.auth.service.verify_google_token') as mock_verify:
            mock_verify.return_value = None
            result = self.auth_service.validate_google_token('invalid_token')
            
            assert result is None
    
    def test_create_or_get_user_new_user(self):
        """Test creating a new user from Google profile"""
        # Arrange
        google_profile = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'picture': 'https://example.com/avatar.jpg',
            'sub': 'google_user_id_456'
        }
        
        # Act & Assert
        with patch('app.models.user.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            with patch('app.models.user.User') as mock_user_class:
                mock_user = Mock()
                mock_user.id = 'user_123'
                mock_user_class.return_value = mock_user
                
                result = self.auth_service.create_or_get_user(google_profile)
                
                assert result == mock_user
                mock_user_class.assert_called_once()
    
    def test_create_or_get_user_existing_user(self):
        """Test getting existing user by email"""
        # Arrange
        google_profile = {
            'email': 'existing@example.com',
            'name': 'Existing User',
            'picture': 'https://example.com/avatar.jpg',
            'sub': 'google_user_id_789'
        }
        existing_user = Mock()
        existing_user.id = 'existing_user_123'
        
        # Act & Assert
        with patch('app.models.user.User.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = existing_user
            
            result = self.auth_service.create_or_get_user(google_profile)
            
            assert result == existing_user
    
    def test_generate_tokens(self):
        """Test JWT token generation"""
        # Arrange
        user = Mock()
        user.id = 'user_123'
        user.email = 'test@example.com'
        
        # Act & Assert
        with patch('app.auth.service.create_access_token') as mock_access, \
             patch('app.auth.service.create_refresh_token') as mock_refresh:
            
            mock_access.return_value = 'access_token_123'
            mock_refresh.return_value = 'refresh_token_123'
            
            tokens = self.auth_service.generate_tokens(user)
            
            assert tokens['access_token'] == 'access_token_123'
            assert tokens['refresh_token'] == 'refresh_token_123'
            assert tokens['expires_in'] == 900  # 15 minutes
            
            mock_access.assert_called_once_with(
                identity=user.id,
                additional_claims={'email': user.email}
            )
            mock_refresh.assert_called_once_with(identity=user.id)
    
    def test_extract_company_domain(self):
        """Test company domain extraction from email"""
        # Test cases
        test_cases = [
            ('user@company.com', 'company.com'),
            ('test@example.org', 'example.org'),
            ('admin@sub.domain.co.uk', 'sub.domain.co.uk'),
            ('invalid-email', None),
            ('', None)
        ]
        
        for email, expected in test_cases:
            result = self.auth_service.extract_company_domain(email)
            assert result == expected