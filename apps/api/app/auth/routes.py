from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from . import auth_bp
from .service import AuthService
from app.models.user import User


auth_service = AuthService()


@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """Google OAuth authentication endpoint"""
    try:
        # Get authorization code from request
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'Authorization code is required'}), 400
        
        auth_code = data['code']
        
        # Validate Google token and get user profile
        google_profile = auth_service.validate_google_token(auth_code)
        if not google_profile:
            return jsonify({'error': 'Invalid authorization code'}), 401
        
        # Create or get user
        user = auth_service.create_or_get_user(google_profile)
        
        # Generate JWT tokens
        tokens = auth_service.generate_tokens(user)
        
        # Return authentication response matching API contract
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Google auth error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh JWT token endpoint"""
    try:
        # Get current user from refresh token
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate new tokens
        tokens = auth_service.generate_tokens(user)
        
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint"""
    # For now, we'll implement a simple logout
    # In production, you might want to blacklist tokens in Redis
    return '', 204