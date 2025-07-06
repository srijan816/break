"""
Calendar API routes for calendar connection and synchronization.
"""
import logging
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.calendar import calendar_bp
from app.models import User, CalendarConnection
from app.services.calendar_service import CalendarService
from app.tasks.calendar_tasks import sync_user_calendar

logger = logging.getLogger(__name__)


@calendar_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect_calendar():
    """
    Connect user's Google Calendar using OAuth tokens.
    Triggers asynchronous calendar sync.
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'access_token' not in data:
            return jsonify({'error': 'Access token required'}), 400
        
        access_token = data['access_token']
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required for calendar access'}), 400
        
        # Connect calendar
        calendar_service = CalendarService()
        connection = calendar_service.connect_calendar(
            user_id=current_user_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        # Trigger async calendar sync
        task = sync_user_calendar.delay(current_user_id)
        
        return jsonify({
            'message': 'Calendar connected successfully',
            'calendar_id': connection.calendar_id,
            'sync_task_id': task.id,
            'status': 'syncing'
        }), 201
        
    except ValueError as e:
        logger.warning(f"Calendar connection failed for user {current_user_id}: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Calendar connection error for user {current_user_id}: {e}")
        return jsonify({'error': 'Calendar connection failed'}), 500


@calendar_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_calendar():
    """
    Manually trigger calendar synchronization.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user has calendar connection
        connection = CalendarConnection.query.filter_by(user_id=current_user_id).first()
        if not connection:
            return jsonify({'error': 'No calendar connection found'}), 404
        
        # Trigger async sync
        task = sync_user_calendar.delay(current_user_id)
        
        return jsonify({
            'message': 'Calendar sync initiated',
            'task_id': task.id,
            'status': 'syncing'
        }), 202
        
    except Exception as e:
        logger.error(f"Calendar sync error for user {current_user_id}: {e}")
        return jsonify({'error': 'Calendar sync failed'}), 500


@calendar_bp.route('/status', methods=['GET'])
@jwt_required()
def calendar_status():
    """
    Get calendar connection status and sync information.
    """
    try:
        current_user_id = get_jwt_identity()
        
        connection = CalendarConnection.query.filter_by(user_id=current_user_id).first()
        
        if not connection:
            return jsonify({
                'connected': False,
                'message': 'No calendar connection'
            }), 200
        
        # Check if sync is needed
        calendar_service = CalendarService()
        needs_sync = calendar_service.is_sync_needed(current_user_id)
        
        return jsonify({
            'connected': True,
            'calendar_id': connection.calendar_id,
            'provider': connection.provider,
            'last_sync': connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            'needs_sync': needs_sync
        }), 200
        
    except Exception as e:
        logger.error(f"Calendar status error for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to get calendar status'}), 500


@calendar_bp.route('/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect_calendar():
    """
    Disconnect calendar and remove stored data.
    """
    try:
        current_user_id = get_jwt_identity()
        
        calendar_service = CalendarService()
        calendar_service.disconnect_calendar(current_user_id)
        
        return jsonify({
            'message': 'Calendar disconnected successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Calendar disconnect error for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to disconnect calendar'}), 500


@calendar_bp.route('/events', methods=['GET'])
@jwt_required()
def get_calendar_events():
    """
    Get user's calendar events (for debugging/admin purposes).
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Optional date range
        days_ahead = request.args.get('days', 7, type=int)
        days_ahead = min(days_ahead, 30)  # Limit to 30 days
        
        calendar_service = CalendarService()
        
        # Check if sync is needed
        if calendar_service.is_sync_needed(current_user_id):
            # Trigger sync but return current data
            sync_user_calendar.delay(current_user_id)
        
        events = calendar_service.fetch_calendar_events(current_user_id, days_ahead)
        
        return jsonify({
            'events': events[:50],  # Limit response size
            'total_count': len(events),
            'days_ahead': days_ahead
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Get events error for user {current_user_id}: {e}")
        return jsonify({'error': 'Failed to fetch calendar events'}), 500