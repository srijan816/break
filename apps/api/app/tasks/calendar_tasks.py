"""
Celery tasks for calendar synchronization and background processing.
"""
import logging
from datetime import datetime, timedelta
from celery_app import celery

from app import create_app, db
from app.models import User, CalendarConnection
from app.services.calendar_service import CalendarService
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def sync_user_calendar(self, user_id: int, days_ahead: int = 7):
    """
    Sync a user's calendar events from Google Calendar.
    This is the main async task triggered by calendar connection.
    """
    app = create_app()
    
    with app.app_context():
        try:
            logger.info(f"Starting calendar sync for user {user_id}")
            
            # Check if user exists and has calendar connection
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return {'status': 'error', 'message': 'User not found'}
            
            connection = CalendarConnection.query.filter_by(user_id=user_id).first()
            if not connection:
                logger.error(f"No calendar connection for user {user_id}")
                return {'status': 'error', 'message': 'No calendar connection'}
            
            # Perform calendar sync
            calendar_service = CalendarService()
            synced_count = calendar_service.sync_calendar_events(user_id, days_ahead)
            
            # Generate recommendations after sync
            try:
                recommendation_service = RecommendationService()
                recommendation_service.generate_and_store_recommendations(user_id)
                logger.info(f"Generated recommendations after sync for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to generate recommendations for user {user_id}: {e}")
                # Don't fail the sync task if recommendations fail
            
            result = {
                'status': 'success',
                'user_id': user_id,
                'events_synced': synced_count,
                'sync_time': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Calendar sync completed for user {user_id}: {synced_count} events")
            return result
            
        except Exception as e:
            logger.error(f"Calendar sync failed for user {user_id}: {e}")
            
            # Retry logic
            if self.request.retries < self.max_retries:
                # Exponential backoff: 30s, 2m, 8m
                delay = 30 * (4 ** self.request.retries)
                logger.info(f"Retrying calendar sync for user {user_id} in {delay} seconds")
                raise self.retry(countdown=delay, exc=e)
            
            return {
                'status': 'error',
                'user_id': user_id,
                'message': str(e),
                'retries': self.request.retries
            }


@celery.task
def sync_all_users_calendars():
    """
    Periodic task to sync calendars for all connected users.
    Should be scheduled to run every hour.
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Find users who need calendar sync (last sync > 1 hour ago)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            connections = CalendarConnection.query.filter(
                db.or_(
                    CalendarConnection.last_sync_at.is_(None),
                    CalendarConnection.last_sync_at < cutoff_time
                )
            ).all()
            
            synced_users = []
            for connection in connections:
                try:
                    # Trigger async sync for each user
                    sync_user_calendar.delay(connection.user_id)
                    synced_users.append(connection.user_id)
                except Exception as e:
                    logger.error(f"Failed to queue sync for user {connection.user_id}: {e}")
            
            logger.info(f"Queued calendar sync for {len(synced_users)} users")
            return {
                'status': 'success',
                'users_queued': len(synced_users),
                'user_ids': synced_users
            }
            
        except Exception as e:
            logger.error(f"Failed to queue calendar syncs: {e}")
            return {'status': 'error', 'message': str(e)}


@celery.task
def generate_daily_recommendations():
    """
    Periodic task to generate daily break recommendations for all users.
    Should be scheduled to run every morning.
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Find all users with calendar connections
            users_with_calendars = db.session.query(User.id).join(
                CalendarConnection, User.id == CalendarConnection.user_id
            ).all()
            
            recommendation_service = RecommendationService()
            generated_count = 0
            
            for (user_id,) in users_with_calendars:
                try:
                    recommendation_service.generate_and_store_recommendations(user_id)
                    generated_count += 1
                except Exception as e:
                    logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
            
            logger.info(f"Generated recommendations for {generated_count} users")
            return {
                'status': 'success',
                'recommendations_generated': generated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to generate daily recommendations: {e}")
            return {'status': 'error', 'message': str(e)}


@celery.task
def cleanup_old_calendar_events():
    """
    Periodic task to clean up old calendar events.
    Should be scheduled to run daily.
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Delete events older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            from app.models import CalendarEvent
            deleted_count = CalendarEvent.query.filter(
                CalendarEvent.start_time < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted_count} old calendar events")
            return {
                'status': 'success',
                'events_deleted': deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}


@celery.task
def refresh_expired_tokens():
    """
    Periodic task to refresh expired calendar access tokens.
    Should be scheduled to run every 30 minutes.
    """
    app = create_app()
    
    with app.app_context():
        try:
            calendar_service = CalendarService()
            refreshed_count = 0
            
            # Find connections that might have expired tokens
            # Google tokens typically expire after 1 hour
            connections = CalendarConnection.query.all()
            
            for connection in connections:
                try:
                    # Test current token
                    headers = {'Authorization': f'Bearer {connection.access_token}'}
                    import requests
                    response = requests.get(
                        'https://www.googleapis.com/calendar/v3/users/me/settings/timezone',
                        headers=headers,
                        timeout=5
                    )
                    
                    # If token is invalid (401), refresh it
                    if response.status_code == 401 and connection.refresh_token:
                        calendar_service.refresh_access_token(connection)
                        refreshed_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to check/refresh token for user {connection.user_id}: {e}")
            
            logger.info(f"Refreshed {refreshed_count} access tokens")
            return {
                'status': 'success',
                'tokens_refreshed': refreshed_count
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh tokens: {e}")
            return {'status': 'error', 'message': str(e)}