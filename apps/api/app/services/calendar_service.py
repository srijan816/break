"""
Google Calendar Integration Service
Handles OAuth, calendar sync, and event fetching from Google Calendar API.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app import db
from app.models import User, CalendarEvent, CalendarConnection
from config import get_config

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Manages Google Calendar API integration and calendar data synchronization.
    """
    
    def __init__(self):
        self.config = get_config()
        self.base_url = 'https://www.googleapis.com/calendar/v3'
        
        # Configure retry strategy for API calls
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
    
    def connect_calendar(self, user_id: int, access_token: str, 
                        refresh_token: str) -> CalendarConnection:
        """
        Create or update calendar connection for a user.
        Stores OAuth tokens for future calendar access.
        """
        try:
            # Validate token by making a test API call
            headers = {'Authorization': f'Bearer {access_token}'}
            response = self.session.get(
                f'{self.base_url}/users/me/calendarList/primary',
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise ValueError(f"Invalid access token: {response.status_code}")
            
            calendar_info = response.json()
            
            # Create or update calendar connection
            connection = CalendarConnection.query.filter_by(user_id=user_id).first()
            
            if connection:
                connection.access_token = access_token
                connection.refresh_token = refresh_token
                connection.calendar_id = calendar_info.get('id', 'primary')
                connection.last_sync_at = None  # Reset sync status
            else:
                connection = CalendarConnection(
                    user_id=user_id,
                    provider='google',
                    access_token=access_token,
                    refresh_token=refresh_token,
                    calendar_id=calendar_info.get('id', 'primary')
                )
                db.session.add(connection)
            
            db.session.commit()
            logger.info(f"Calendar connected successfully for user {user_id}")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect calendar for user {user_id}: {e}")
            db.session.rollback()
            raise
    
    def refresh_access_token(self, connection: CalendarConnection) -> str:
        """
        Refresh the access token using the refresh token.
        """
        try:
            data = {
                'client_id': self.config.GOOGLE_CLIENT_ID,
                'client_secret': self.config.GOOGLE_CLIENT_SECRET,
                'refresh_token': connection.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = self.session.post(
                'https://oauth2.googleapis.com/token',
                data=data,
                timeout=10
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token refresh failed: {response.status_code}")
            
            token_data = response.json()
            new_access_token = token_data['access_token']
            
            # Update stored token
            connection.access_token = new_access_token
            db.session.commit()
            
            logger.info(f"Access token refreshed for user {connection.user_id}")
            return new_access_token
            
        except Exception as e:
            logger.error(f"Failed to refresh token for user {connection.user_id}: {e}")
            raise
    
    def get_valid_access_token(self, connection: CalendarConnection) -> str:
        """
        Get a valid access token, refreshing if necessary.
        """
        # Try the current token first
        headers = {'Authorization': f'Bearer {connection.access_token}'}
        response = self.session.get(
            f'{self.base_url}/users/me/settings/timezone',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return connection.access_token
        
        # Token is invalid, try to refresh
        if response.status_code == 401 and connection.refresh_token:
            return self.refresh_access_token(connection)
        
        raise ValueError("Unable to obtain valid access token")
    
    def fetch_calendar_events(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """
        Fetch calendar events for the next N days from Google Calendar.
        """
        try:
            connection = CalendarConnection.query.filter_by(user_id=user_id).first()
            if not connection:
                raise ValueError(f"No calendar connection found for user {user_id}")
            
            access_token = self.get_valid_access_token(connection)
            
            # Calculate time range
            user = User.query.get(user_id)
            user_tz = pytz.timezone(user.timezone)
            now = datetime.now(user_tz)
            time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
            time_max = time_min + timedelta(days=days_ahead)
            
            # API parameters
            params = {
                'calendarId': connection.calendar_id or 'primary',
                'timeMin': time_min.isoformat(),
                'timeMax': time_max.isoformat(),
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': 500  # Google's max limit
            }
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = self.session.get(
                f'{self.base_url}/calendars/{params["calendarId"]}/events',
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValueError(f"Calendar API error: {response.status_code}")
            
            events_data = response.json()
            events = events_data.get('items', [])
            
            logger.info(f"Fetched {len(events)} events for user {user_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to fetch calendar events for user {user_id}: {e}")
            raise
    
    def sync_calendar_events(self, user_id: int, days_ahead: int = 7) -> int:
        """
        Sync calendar events from Google Calendar to local database.
        Returns number of events synced.
        """
        try:
            # Fetch events from Google Calendar
            google_events = self.fetch_calendar_events(user_id, days_ahead)
            
            # Parse and store events
            synced_count = 0
            user = User.query.get(user_id)
            user_tz = pytz.timezone(user.timezone)
            
            # Clear existing events for the sync period
            sync_start = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            sync_end = sync_start + timedelta(days=days_ahead)
            
            CalendarEvent.query.filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= sync_start,
                CalendarEvent.start_time < sync_end
            ).delete()
            
            for event_data in google_events:
                try:
                    event = self._parse_google_event(event_data, user_id, user_tz)
                    if event:
                        db.session.add(event)
                        synced_count += 1
                except Exception as e:
                    logger.warning(f"Failed to parse event {event_data.get('id', 'unknown')}: {e}")
                    continue
            
            # Update sync timestamp
            connection = CalendarConnection.query.filter_by(user_id=user_id).first()
            if connection:
                connection.last_sync_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Synced {synced_count} events for user {user_id}")
            return synced_count
            
        except Exception as e:
            logger.error(f"Calendar sync failed for user {user_id}: {e}")
            db.session.rollback()
            raise
    
    def _parse_google_event(self, event_data: Dict, user_id: int, 
                           user_tz: pytz.timezone) -> Optional[CalendarEvent]:
        """
        Parse a Google Calendar event into our CalendarEvent model.
        """
        try:
            # Skip events without start/end times (all-day events handled separately)
            start_data = event_data.get('start', {})
            end_data = event_data.get('end', {})
            
            # Handle different time formats
            if 'dateTime' in start_data:
                start_time = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
                
                # Convert to user's timezone
                start_time = start_time.astimezone(user_tz)
                end_time = end_time.astimezone(user_tz)
                
            elif 'date' in start_data:
                # All-day event - skip for break recommendations
                return None
            else:
                return None
            
            # Extract attendee count
            attendees = event_data.get('attendees', [])
            attendee_count = len([a for a in attendees if a.get('responseStatus') != 'declined'])
            
            # Skip declined events
            if event_data.get('status') == 'cancelled':
                return None
            
            # Skip very short events (< 5 minutes)
            duration = (end_time - start_time).total_seconds() / 60
            if duration < 5:
                return None
            
            return CalendarEvent(
                user_id=user_id,
                external_id=event_data.get('id'),
                title=event_data.get('summary', 'Untitled Event'),
                start_time=start_time,
                end_time=end_time,
                attendee_count=max(attendee_count, 1),  # At least 1 (the user)
                is_recurring=bool(event_data.get('recurringEventId'))
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse event: {e}")
            return None
    
    def is_sync_needed(self, user_id: int, max_age_hours: int = 1) -> bool:
        """
        Check if calendar sync is needed based on last sync time.
        """
        connection = CalendarConnection.query.filter_by(user_id=user_id).first()
        if not connection or not connection.last_sync_at:
            return True
        
        age = datetime.utcnow() - connection.last_sync_at
        return age > timedelta(hours=max_age_hours)
    
    def disconnect_calendar(self, user_id: int) -> None:
        """
        Disconnect calendar and clean up stored data.
        """
        try:
            # Remove calendar connection
            connection = CalendarConnection.query.filter_by(user_id=user_id).first()
            if connection:
                db.session.delete(connection)
            
            # Remove stored events
            CalendarEvent.query.filter_by(user_id=user_id).delete()
            
            db.session.commit()
            logger.info(f"Calendar disconnected for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to disconnect calendar for user {user_id}: {e}")
            db.session.rollback()
            raise