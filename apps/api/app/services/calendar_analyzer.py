"""
Calendar Analysis Service
Analyzes calendar events and meeting patterns to inform break recommendations.
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pytz

from app.models import CalendarEvent, User


class CalendarAnalyzer:
    """
    Analyzes calendar events to extract insights for break recommendations.
    Based on PRD section 4.7 - The Break Scheduling Algorithm.
    """
    
    # Meeting type keywords from PRD
    STRESS_KEYWORDS = [
        'review', 'deadline', 'urgent', 'presentation', 'demo', 'pitch',
        'interview', 'performance', 'quarterly', 'annual', 'board',
        'crisis', 'escalation', 'critical', 'emergency'
    ]
    
    CREATIVE_KEYWORDS = [
        'brainstorm', 'ideation', 'design', 'planning', 'strategy',
        'workshop', 'creative', 'innovation', 'concept', 'roadmap'
    ]
    
    SOCIAL_KEYWORDS = [
        '1:1', 'one-on-one', 'team', 'all-hands', 'standup', 'social',
        'coffee', 'lunch', 'networking', 'meet', 'sync', 'check-in'
    ]
    
    FOCUS_KEYWORDS = [
        'blocked', 'focus time', 'deep work', 'coding', 'writing',
        'analysis', 'research', 'documentation', 'study'
    ]
    
    def calculate_meeting_intensity(self, title: str, duration_minutes: int, 
                                  attendee_count: int) -> int:
        """
        Calculate meeting intensity score (1-10) based on title, duration, and attendees.
        Higher scores indicate more intense/draining meetings.
        """
        score = 1
        title_lower = title.lower()
        
        # Title-based scoring
        if any(keyword in title_lower for keyword in self.STRESS_KEYWORDS):
            score += 4
        elif any(keyword in title_lower for keyword in self.CREATIVE_KEYWORDS):
            score += 2
        elif any(keyword in title_lower for keyword in self.SOCIAL_KEYWORDS):
            score += 1
        
        # Duration-based scoring
        if duration_minutes >= 120:  # 2+ hours
            score += 3
        elif duration_minutes >= 60:  # 1+ hour
            score += 2
        elif duration_minutes >= 30:  # 30+ minutes
            score += 1
        
        # Attendee-based scoring
        if attendee_count >= 10:
            score += 3
        elif attendee_count >= 6:
            score += 2
        elif attendee_count >= 3:
            score += 1
        
        return min(score, 10)  # Cap at 10
    
    def classify_meeting_type(self, title: str) -> List[str]:
        """
        Classify meeting type based on title keywords.
        Returns list of types that apply.
        """
        types = []
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in self.STRESS_KEYWORDS):
            types.append('high_stress')
        
        if any(keyword in title_lower for keyword in self.CREATIVE_KEYWORDS):
            types.append('creative')
        
        if any(keyword in title_lower for keyword in self.SOCIAL_KEYWORDS):
            types.append('social')
        
        if any(keyword in title_lower for keyword in self.FOCUS_KEYWORDS):
            types.append('focus')
        
        return types if types else ['general']
    
    def calculate_workday_boundaries(self, events: List[CalendarEvent], 
                                   user: User) -> Tuple[datetime, datetime]:
        """
        Calculate workday start and end times based on meetings and user preferences.
        Implementation of PRD algorithm Step 1.
        """
        if not events:
            # Default to 9 AM - 6 PM in user's timezone
            tz = pytz.timezone(user.timezone)
            today = datetime.now(tz).replace(hour=9, minute=0, second=0, microsecond=0)
            return today, today.replace(hour=18)
        
        # Find first and last meetings
        first_meeting = min(events, key=lambda e: e.start_time)
        last_meeting = max(events, key=lambda e: e.end_time)
        
        # Apply algorithm: first meeting - 1 hour, last meeting + 30 min
        workday_start = first_meeting.start_time - timedelta(hours=1)
        workday_end = last_meeting.end_time + timedelta(minutes=30)
        
        # Ensure reasonable boundaries (not before 6 AM or after 10 PM)
        min_start = workday_start.replace(hour=6, minute=0, second=0, microsecond=0)
        max_end = workday_start.replace(hour=22, minute=0, second=0, microsecond=0)
        
        workday_start = max(workday_start, min_start)
        workday_end = min(workday_end, max_end)
        
        return workday_start, workday_end
    
    def find_break_opportunities(self, events: List[CalendarEvent], 
                               workday_start: datetime, workday_end: datetime) -> List[Dict]:
        """
        Find gaps between meetings that could accommodate breaks.
        Implementation of PRD algorithm Step 3.
        """
        if not events:
            # Empty day - suggest breaks at strategic times
            morning_break = workday_start + timedelta(hours=2)
            afternoon_break = workday_start + timedelta(hours=5)
            return [
                {
                    'start_time': morning_break,
                    'duration_minutes': 15,
                    'gap_type': 'empty_day',
                    'preceding_meeting': None,
                    'following_meeting': None
                },
                {
                    'start_time': afternoon_break,
                    'duration_minutes': 15,
                    'gap_type': 'empty_day',
                    'preceding_meeting': None,
                    'following_meeting': None
                }
            ]
        
        # Sort events by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)
        opportunities = []
        
        # Check gap before first meeting
        if sorted_events[0].start_time - workday_start >= timedelta(minutes=15):
            gap_duration = (sorted_events[0].start_time - workday_start).total_seconds() / 60
            opportunities.append({
                'start_time': workday_start,
                'duration_minutes': min(gap_duration - 5, 30),  # 5 min buffer
                'gap_type': 'before_first',
                'preceding_meeting': None,
                'following_meeting': sorted_events[0]
            })
        
        # Check gaps between meetings
        for i in range(len(sorted_events) - 1):
            current_meeting = sorted_events[i]
            next_meeting = sorted_events[i + 1]
            
            gap_start = current_meeting.end_time
            gap_end = next_meeting.start_time
            gap_duration = (gap_end - gap_start).total_seconds() / 60
            
            if gap_duration >= 15:  # Minimum 15-minute gap
                break_duration = min(gap_duration - 5, 30)  # 5 min buffer, max 30 min
                opportunities.append({
                    'start_time': gap_start + timedelta(minutes=2),  # Small buffer
                    'duration_minutes': break_duration,
                    'gap_type': 'between_meetings',
                    'preceding_meeting': current_meeting,
                    'following_meeting': next_meeting
                })
        
        # Check gap after last meeting
        if workday_end - sorted_events[-1].end_time >= timedelta(minutes=15):
            gap_duration = (workday_end - sorted_events[-1].end_time).total_seconds() / 60
            opportunities.append({
                'start_time': sorted_events[-1].end_time + timedelta(minutes=2),
                'duration_minutes': min(gap_duration - 5, 30),
                'gap_type': 'after_last',
                'preceding_meeting': sorted_events[-1],
                'following_meeting': None
            })
        
        return opportunities
    
    def calculate_opportunity_score(self, opportunity: Dict, user: User, 
                                  recent_breaks: List[datetime]) -> float:
        """
        Calculate score for a break opportunity.
        Implementation of PRD algorithm Step 3 scoring logic.
        """
        score = 1.0
        
        # Gap duration scoring (longer gaps = higher score)
        duration = opportunity['duration_minutes']
        if duration >= 30:
            score += 3.0
        elif duration >= 20:
            score += 2.0
        elif duration >= 15:
            score += 1.0
        
        # Time since last break
        if recent_breaks:
            time_since_last = (opportunity['start_time'] - max(recent_breaks)).total_seconds() / 3600
            if time_since_last >= 3:  # 3+ hours since last break
                score += 3.0
            elif time_since_last >= 2:  # 2+ hours
                score += 2.0
            elif time_since_last >= 1:  # 1+ hour
                score += 1.0
        else:
            score += 2.0  # No recent breaks
        
        # Preceding meeting intensity
        if opportunity['preceding_meeting']:
            intensity = self.calculate_meeting_intensity(
                opportunity['preceding_meeting'].title,
                (opportunity['preceding_meeting'].end_time - 
                 opportunity['preceding_meeting'].start_time).total_seconds() / 60,
                opportunity['preceding_meeting'].attendee_count or 3
            )
            score += intensity * 0.3  # Higher intensity = more need for break
        
        # Following meeting intensity (prep time for intense meetings)
        if opportunity['following_meeting']:
            intensity = self.calculate_meeting_intensity(
                opportunity['following_meeting'].title,
                (opportunity['following_meeting'].end_time - 
                 opportunity['following_meeting'].start_time).total_seconds() / 60,
                opportunity['following_meeting'].attendee_count or 3
            )
            score += intensity * 0.2  # Prep for intense meetings
        
        # Time of day preferences
        hour = opportunity['start_time'].hour
        if 10 <= hour <= 11:  # Mid-morning sweet spot
            score += 1.5
        elif 14 <= hour <= 15:  # Post-lunch energy dip
            score += 2.0
        elif 16 <= hour <= 17:  # Late afternoon recharge
            score += 1.5
        
        return score
    
    def get_meeting_context(self, meeting: Optional[CalendarEvent]) -> Dict:
        """
        Extract contextual information from a meeting for break type selection.
        """
        if not meeting:
            return {'type': 'none', 'intensity': 1, 'context': []}
        
        types = self.classify_meeting_type(meeting.title)
        intensity = self.calculate_meeting_intensity(
            meeting.title,
            (meeting.end_time - meeting.start_time).total_seconds() / 60,
            meeting.attendee_count or 3
        )
        
        return {
            'type': types[0] if types else 'general',
            'intensity': intensity,
            'context': types,
            'title': meeting.title
        }