"""
Recommendations API routes for break recommendations.
"""
import logging
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.recommendations import recommendations_bp
from app.models import BreakRecommendation, BreakSession
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


@recommendations_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_recommendation():
    """
    Get the single best break recommendation for today.
    Main endpoint for the MVP - returns one optimal recommendation.
    """
    try:
        current_user_id = get_jwt_identity()
        
        recommendation_service = RecommendationService()
        recommendation = recommendation_service.get_today_recommendation(current_user_id)
        
        if not recommendation:
            return jsonify({
                'message': 'No recommendations available for today',
                'recommendation': None
            }), 200
        
        # Include break session details
        break_session = BreakSession.query.get(recommendation.session_id)
        
        response_data = {
            'recommendation': {
                'id': recommendation.id,
                'recommended_time': recommendation.recommended_time.isoformat(),
                'reason': recommendation.reason,
                'score': recommendation.score,
                'status': recommendation.status,
                'break_session': {
                    'id': break_session.id,
                    'title': break_session.title,
                    'description': break_session.description,
                    'category': break_session.category,
                    'duration_minutes': break_session.duration_minutes
                } if break_session else None
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to get recommendation for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to get recommendation'}), 500


@recommendations_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_recommendations():
    """
    Manually trigger recommendation generation for today.
    Useful for testing and when user wants fresh recommendations.
    """
    try:
        current_user_id = get_jwt_identity()
        
        recommendation_service = RecommendationService()
        recommendations = recommendation_service.generate_and_store_recommendations(current_user_id)
        
        if not recommendations:
            return jsonify({
                'message': 'No recommendations could be generated',
                'count': 0
            }), 200
        
        # Return the best recommendation
        best_recommendation = recommendations[0]
        break_session = BreakSession.query.get(best_recommendation.session_id)
        
        response_data = {
            'message': 'Recommendations generated successfully',
            'count': len(recommendations),
            'recommendation': {
                'id': best_recommendation.id,
                'recommended_time': best_recommendation.recommended_time.isoformat(),
                'reason': best_recommendation.reason,
                'score': best_recommendation.score,
                'status': best_recommendation.status,
                'break_session': {
                    'id': break_session.id,
                    'title': break_session.title,
                    'description': break_session.description,
                    'category': break_session.category,
                    'duration_minutes': break_session.duration_minutes
                } if break_session else None
            }
        }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to generate recommendations'}), 500


@recommendations_bp.route('/<int:recommendation_id>/dismiss', methods=['POST'])
@jwt_required()
def dismiss_recommendation(recommendation_id: int):
    """
    Dismiss a recommendation (user doesn't want this break).
    """
    try:
        current_user_id = get_jwt_identity()
        
        recommendation = BreakRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=current_user_id
        ).first()
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        recommendation.status = 'dismissed'
        
        # Generate a new recommendation to replace the dismissed one
        recommendation_service = RecommendationService()
        new_recommendations = recommendation_service.generate_and_store_recommendations(current_user_id)
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'message': 'Recommendation dismissed',
            'new_recommendations_generated': len(new_recommendations)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to dismiss recommendation {recommendation_id} for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to dismiss recommendation'}), 500


@recommendations_bp.route('/history', methods=['GET'])
@jwt_required()
def get_recommendation_history():
    """
    Get user's recommendation history.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50
        offset = request.args.get('offset', 0, type=int)
        
        recommendations = BreakRecommendation.query.filter_by(
            user_id=current_user_id
        ).order_by(
            BreakRecommendation.recommended_time.desc()
        ).offset(offset).limit(limit).all()
        
        response_data = {
            'recommendations': []
        }
        
        for rec in recommendations:
            break_session = BreakSession.query.get(rec.session_id)
            
            response_data['recommendations'].append({
                'id': rec.id,
                'recommended_time': rec.recommended_time.isoformat(),
                'reason': rec.reason,
                'score': rec.score,
                'status': rec.status,
                'created_at': rec.created_at.isoformat(),
                'break_session': {
                    'id': break_session.id,
                    'title': break_session.title,
                    'category': break_session.category,
                    'duration_minutes': break_session.duration_minutes
                } if break_session else None
            })
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to get recommendation history for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to get recommendation history'}), 500