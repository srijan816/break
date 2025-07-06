"""
Break Recommendation Service
Implements the core recommendation algorithm from PRD section 4.7.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from app import db
from app.models import User, CalendarEvent, BreakRecommendation, BreakSession, CompletedBreak
from app.services.calendar_analyzer import CalendarAnalyzer

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Generates intelligent break recommendations based on calendar analysis.
    Implements the suggestBreaks algorithm from PRD section 4.7.
    """
    
    def __init__(self):
        self.analyzer = CalendarAnalyzer()
        
        # Break type mappings based on context
        self.break_type_mapping = {
            'high_stress': ['meditation', 'breathing', 'mindfulness'],
            'creative': ['movement', 'walk', 'stretching'],
            'social': ['solo_activity', 'mindfulness', 'music'],
            'focus': ['movement', 'energizing', 'music'],
            'general': ['meditation', 'movement', 'breathing'],
            'empty_day': ['mindfulness', 'movement'],
            'pre_presentation': ['confidence', 'energizing', 'breathing'],
            'post_meeting': ['reset', 'stretching', 'mindfulness']
        }
    
    def generate_recommendations(self, user_id: int) -> List[BreakRecommendation]:
        """
        Generate break recommendations for a user's current day.
        Implementation of the complete suggestBreaks algorithm from PRD.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get today's calendar events
            user_tz = pytz.timezone(user.timezone)
            today = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            events = CalendarEvent.query.filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= today,
                CalendarEvent.start_time < tomorrow
            ).order_by(CalendarEvent.start_time).all()
            
            # Step 1: Define work boundaries
            workday_start, workday_end = self.analyzer.calculate_workday_boundaries(events, user)
            
            # Step 2: Analyze meeting density and context
            meeting_analysis = self._analyze_meetings(events)
            
            # Step 3: Find break opportunities
            opportunities = self.analyzer.find_break_opportunities(events, workday_start, workday_end)
            
            # Get recent breaks for scoring
            recent_breaks = self._get_recent_break_times(user_id, today)
            
            # Step 4: Score opportunities
            scored_opportunities = []
            for opportunity in opportunities:
                score = self.analyzer.calculate_opportunity_score(opportunity, user, recent_breaks)
                scored_opportunities.append({
                    **opportunity,
                    'score': score,
                    'meeting_context': self._get_opportunity_context(opportunity, meeting_analysis)
                })
            
            # Step 5: Select optimal breaks (top 1 for MVP)
            selected_opportunities = sorted(scored_opportunities, key=lambda x: x['score'], reverse=True)[:1]
            
            # Step 6: Match break types and create recommendations
            recommendations = []
            for opportunity in selected_opportunities:
                break_type = self._select_break_type(opportunity, user)
                break_session = self._select_break_session(break_type, opportunity['duration_minutes'])
                
                # Calculate expiration time (end of day)
                expires_at = opportunity['start_time'].replace(hour=23, minute=59, second=59)
                
                recommendation = BreakRecommendation(
                    user_id=user_id,
                    session_id=break_session.id if break_session else None,
                    recommended_time=opportunity['start_time'],
                    reason=self._generate_context_reason(opportunity),
                    score=min(opportunity['score'] / 10, 1.0),  # Normalize to 0-1
                    expires_at=expires_at,
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
            raise
    
    def generate_and_store_recommendations(self, user_id: int) -> List[BreakRecommendation]:
        """
        Generate recommendations and store them in the database.
        Replaces any existing recommendations for today.
        """
        try:
            # Clear existing recommendations for today
            user = User.query.get(user_id)
            user_tz = pytz.timezone(user.timezone)
            today = datetime.now(user_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            BreakRecommendation.query.filter(
                BreakRecommendation.user_id == user_id,
                BreakRecommendation.recommended_time >= today,
                BreakRecommendation.recommended_time < tomorrow
            ).delete()
            
            # Generate new recommendations
            recommendations = self.generate_recommendations(user_id)
            
            # Store in database
            for rec in recommendations:
                db.session.add(rec)
            
            db.session.commit()
            
            logger.info(f"Stored {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to store recommendations for user {user_id}: {e}")
            db.session.rollback()
            raise
    
    def get_today_recommendation(self, user_id: int) -> Optional[BreakRecommendation]:
        """
        Get the single best recommendation for today.
        If none exists or is stale, generate new ones.
        """
        try:
            user = User.query.get(user_id)
            user_tz = pytz.timezone(user.timezone)
            now = datetime.now(user_tz)
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Look for valid recommendation for today
            recommendation = BreakRecommendation.query.filter(
                BreakRecommendation.user_id == user_id,
                BreakRecommendation.recommended_time >= now,  # Future or current
                BreakRecommendation.recommended_time < tomorrow,
                BreakRecommendation.status == 'pending'
            ).order_by(BreakRecommendation.score.desc()).first()
            
            # If no valid recommendation exists, generate new ones
            if not recommendation:
                recommendations = self.generate_and_store_recommendations(user_id)
                recommendation = recommendations[0] if recommendations else None
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to get today's recommendation for user {user_id}: {e}")
            raise
    
    def _analyze_meetings(self, events: List[CalendarEvent]) -> Dict:
        """
        Analyze meetings for context and intensity patterns.
        """
        total_intensity = 0
        meeting_types = {}
        meeting_contexts = []
        
        for event in events:
            intensity = self.analyzer.calculate_meeting_intensity(
                event.title,
                (event.end_time - event.start_time).total_seconds() / 60,
                event.attendee_count or 3
            )
            total_intensity += intensity
            
            types = self.analyzer.classify_meeting_type(event.title)
            for meeting_type in types:
                meeting_types[meeting_type] = meeting_types.get(meeting_type, 0) + 1
            
            meeting_contexts.append({
                'event': event,
                'intensity': intensity,
                'types': types
            })
        
        return {
            'total_intensity': total_intensity,
            'average_intensity': total_intensity / len(events) if events else 0,
            'meeting_types': meeting_types,
            'contexts': meeting_contexts,
            'meeting_count': len(events)
        }
    
    def _get_recent_break_times(self, user_id: int, since_date: datetime) -> List[datetime]:
        """
        Get timestamps of recent breaks for scoring.
        """
        completed_breaks = CompletedBreak.query.filter(
            CompletedBreak.user_id == user_id,
            CompletedBreak.completed_at >= since_date
        ).order_by(CompletedBreak.completed_at).all()
        
        return [cb.completed_at for cb in completed_breaks]
    
    def _get_opportunity_context(self, opportunity: Dict, meeting_analysis: Dict) -> Dict:
        """
        Get contextual information about a break opportunity.
        """
        context = {
            'gap_type': opportunity['gap_type'],
            'preceding_meeting': None,
            'following_meeting': None
        }
        
        if opportunity['preceding_meeting']:
            context['preceding_meeting'] = self.analyzer.get_meeting_context(
                opportunity['preceding_meeting']
            )
        
        if opportunity['following_meeting']:
            context['following_meeting'] = self.analyzer.get_meeting_context(
                opportunity['following_meeting']
            )
        
        return context
    
    def _select_break_type(self, opportunity: Dict, user: User) -> str:
        """
        Select appropriate break type based on context and user preferences.
        Implementation of PRD Step 5 - Match break types.
        """
        context = opportunity['meeting_context']
        
        # Default to user's challenge area
        default_types = ['meditation', 'movement', 'breathing']
        if user.biggest_challenge:
            if user.biggest_challenge in ['stress', 'anxiety']:
                default_types = ['meditation', 'breathing', 'mindfulness']
            elif user.biggest_challenge in ['energy', 'focus']:
                default_types = ['movement', 'energizing', 'music']
        
        # Context-based selection
        if context['preceding_meeting']:
            preceding_context = context['preceding_meeting']
            
            if 'high_stress' in preceding_context['context']:
                return 'meditation'
            elif 'creative' in preceding_context['context']:
                return 'movement'
            elif preceding_context['intensity'] >= 7:
                return 'breathing'
        
        if context['following_meeting']:
            following_context = context['following_meeting']
            
            if 'high_stress' in following_context['context']:
                return 'breathing'  # Prep for stressful meeting
            elif 'presentation' in following_context['title'].lower():
                return 'confidence'
        
        # Time-based selection
        hour = opportunity['start_time'].hour
        if 14 <= hour <= 16:  # Afternoon energy dip
            return 'energizing'
        elif hour >= 17:  # End of day
            return 'mindfulness'
        
        return default_types[0]
    
    def _select_break_session(self, break_type: str, duration_minutes: int) -> Optional[BreakSession]:
        """
        Select appropriate break session content based on type and duration.
        """
        # Find sessions that match type and duration
        sessions = BreakSession.query.filter(
            BreakSession.category.ilike(f'%{break_type}%'),
            BreakSession.duration_minutes <= duration_minutes + 2,  # 2 min buffer
            BreakSession.duration_minutes >= max(duration_minutes - 5, 5)  # Minimum 5 min
        ).first()
        
        if not sessions:
            # Fallback to any session within duration
            sessions = BreakSession.query.filter(
                BreakSession.duration_minutes <= duration_minutes + 2
            ).first()
        
        return sessions
    
    def _generate_context_reason(self, opportunity: Dict) -> str:
        """
        Generate human-readable explanation for why this break was recommended.
        """
        context = opportunity['meeting_context']
        
        if context['preceding_meeting']:
            preceding = context['preceding_meeting']
            if preceding['intensity'] >= 7:
                return f"After your {preceding['title'].lower()}, a break can help you reset and recharge."
        
        if context['following_meeting']:
            following = context['following_meeting']
            if following['intensity'] >= 7:
                return f"Before your {following['title'].lower()}, a break can help you prepare and focus."
        
        hour = opportunity['start_time'].hour
        if 14 <= hour <= 16:
            return "Mid-afternoon is a perfect time to recharge your energy levels."
        elif hour <= 11:
            return "A morning break can set a positive tone for your day."
        elif hour >= 17:
            return "An end-of-day break can help you transition and unwind."
        
        return "This gap in your schedule is a perfect opportunity for a mindful break."