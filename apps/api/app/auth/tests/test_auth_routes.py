"""
Integration tests for authentication routes
Following TDD principles - write tests first, then implement
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    """Create test Flask application"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_user():
    """Create sample user for testing"""
    user = User(
        email='test@example.com',
        full_name='Test User',
        google_id='google_123',
        avatar_url='https://example.com/avatar.jpg',
        company_domain='example.com'
    )
    db.session.add(user)
    db.session.commit()
    return user


class TestAuthRoutes:
    """Test authentication route endpoints"""
    
    def test_google_auth_success(self, client):
        """Test successful Google OAuth authentication"""
        # Arrange
        mock_google_profile = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/avatar.jpg',
            'sub': 'google_user_id_123'
        }
        
        # Act
        with patch('app.auth.service.AuthService.validate_google_token') as mock_validate, \
             patch('app.auth.service.AuthService.create_or_get_user') as mock_create_user, \
             patch('app.auth.service.AuthService.generate_tokens') as mock_generate:
            
            mock_validate.return_value = mock_google_profile
            mock_user = Mock()
            mock_user.to_dict.return_value = {'id': 'user_123', 'email': 'test@example.com'}
            mock_create_user.return_value = mock_user
            mock_generate.return_value = {
                'access_token': 'access_123',
                'refresh_token': 'refresh_123',
                'expires_in': 900
            }
            
            response = client.post('/api/v1/auth/google',
                                 data=json.dumps({'code': 'valid_auth_code'}),
                                 content_type='application/json')
            
            # Assert
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert 'user' in data
            assert data['expires_in'] == 900
    
    def test_google_auth_invalid_code(self, client):
        """Test Google OAuth with invalid authorization code"""
        # Act
        with patch('app.auth.service.AuthService.validate_google_token') as mock_validate:
            mock_validate.return_value = None
            
            response = client.post('/api/v1/auth/google',
                                 data=json.dumps({'code': 'invalid_code'}),
                                 content_type='application/json')
            
            # Assert
            assert response.status_code == 401
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_google_auth_missing_code(self, client):
        """Test Google OAuth with missing authorization code"""
        # Act
        response = client.post('/api/v1/auth/google',
                             data=json.dumps({}),
                             content_type='application/json')
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_refresh_token_success(self, client, sample_user):
        """Test successful token refresh"""
        # Act
        with patch('flask_jwt_extended.get_jwt_identity') as mock_identity, \
             patch('flask_jwt_extended.jwt_required') as mock_required, \
             patch('app.auth.service.AuthService.generate_tokens') as mock_generate:
            
            mock_identity.return_value = sample_user.id
            mock_required.return_value = True
            mock_generate.return_value = {
                'access_token': 'new_access_123',
                'refresh_token': 'new_refresh_123',
                'expires_in': 900
            }
            
            response = client.post('/api/v1/auth/refresh',
                                 headers={'Authorization': 'Bearer valid_refresh_token'})
            
            # Assert
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'access_token' in data
            assert 'refresh_token' in data
    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        # Act
        response = client.post('/api/v1/auth/refresh',
                             headers={'Authorization': 'Bearer invalid_token'})
        
        # Assert
        assert response.status_code == 401
    
    def test_get_current_user_success(self, client, sample_user):
        """Test getting current user profile"""
        # Act
        with patch('flask_jwt_extended.get_jwt_identity') as mock_identity, \
             patch('flask_jwt_extended.jwt_required') as mock_required:
            
            mock_identity.return_value = sample_user.id
            mock_required.return_value = True
            
            response = client.get('/api/v1/users/me',
                                headers={'Authorization': 'Bearer valid_access_token'})
            
            # Assert
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['email'] == sample_user.email
            assert data['full_name'] == sample_user.full_name
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without valid token"""
        # Act
        response = client.get('/api/v1/users/me')
        
        # Assert
        assert response.status_code == 401
    
    def test_logout_success(self, client):
        """Test successful logout"""
        # Act
        with patch('flask_jwt_extended.jwt_required') as mock_required:
            mock_required.return_value = True
            
            response = client.post('/api/v1/auth/logout',
                                 headers={'Authorization': 'Bearer valid_access_token'})
            
            # Assert
            assert response.status_code == 204