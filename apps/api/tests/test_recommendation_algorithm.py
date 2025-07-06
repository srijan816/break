"""
Comprehensive test suite for the break recommendation algorithm.
Tests the core intelligence engine with various calendar scenarios.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytz

from app import create_app, db
from app.models import User, CalendarEvent, BreakRecommendation
from app.services.recommendation_service import RecommendationService
from app.services.calendar_analyzer import CalendarAnalyzer


@pytest.fixture
def app():
    """Create test app with in-memory database"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            google_id='test_123',
            email='test@company.com',
            full_name='Test User',
            timezone='America/New_York',
            preferred_break_duration=10,
            biggest_challenge='stress'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def recommendation_service():
    """Create recommendation service instance"""
    return RecommendationService()


@pytest.fixture
def calendar_analyzer():
    """Create calendar analyzer instance"""
    return CalendarAnalyzer()


class TestCalendarAnalyzer:
    """Test calendar analysis and meeting classification"""
    
    def test_meeting_intensity_calculation(self, calendar_analyzer):
        """Test meeting intensity scoring"""
        # High-stress meeting
        high_stress = calendar_analyzer.calculate_meeting_intensity(
            title="Quarterly Review - URGENT",
            duration_minutes=60,
            attendee_count=8
        )
        
        # Low-stress meeting
        low_stress = calendar_analyzer.calculate_meeting_intensity(
            title="Team coffee chat",
            duration_minutes=30,
            attendee_count=3
        )
        
        assert high_stress > low_stress
        assert high_stress >= 7  # Should be high intensity
        assert low_stress <= 4   # Should be low intensity
    
    def test_meeting_type_classification(self, calendar_analyzer):
        """Test meeting type detection from titles"""
        test_cases = [
            ("Quarterly Business Review", "high_stress"),
            ("Design Brainstorm Session", "creative"),
            ("1:1 with Sarah", "social"),
            ("Deep Work - Focus Time", "focus"),
            ("Team Standup", "social"),
            ("Code Review", "high_stress"),
            ("Project Planning", "creative")
        ]
        
        for title, expected_type in test_cases:
            result = calendar_analyzer.classify_meeting_type(title)
            assert expected_type in result, f"Failed for: {title}"
    
    def test_workday_boundary_detection(self, calendar_analyzer, test_user):
        """Test workday start/end calculation"""
        today = datetime.now(pytz.timezone(test_user.timezone)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Create meetings from 10 AM to 4 PM
        events = [
            self._create_event(today.replace(hour=10), 60, "Morning Meeting"),
            self._create_event(today.replace(hour=14), 30, "Afternoon Sync"),
            self._create_event(today.replace(hour=16), 60, "Final Review")
        ]
        
        start, end = calendar_analyzer.calculate_workday_boundaries(events, test_user)
        
        # Should be first meeting - 1 hour to last meeting + 30 min
        assert start.hour == 9   # 10 AM - 1 hour
        assert end.hour == 17    # 4 PM + 1 hour
    
    def _create_event(self, start_time, duration_minutes, title):
        """Helper to create calendar event"""
        return CalendarEvent(
            title=title,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            attendee_count=3
        )


class TestRecommendationScenarios:
    """Test algorithm with realistic calendar scenarios"""
    
    def test_back_to_back_meetings_scenario(self, app, test_user, recommendation_service):
        """Test day with 15+ back-to-back meetings"""
        with app.app_context():
            # Create back-to-back schedule from 9 AM to 6 PM
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            
            events = []
            for hour in range(9, 18):  # 9 AM to 6 PM
                for slot in [0, 30]:  # Every 30 minutes
                    if hour == 17 and slot == 30:  # Don't go past 6 PM
                        break
                    start = today.replace(hour=hour, minute=slot)
                    events.append(CalendarEvent(
                        user_id=test_user.id,
                        title=f"Meeting {hour}:{slot:02d}",
                        start_time=start,
                        end_time=start + timedelta(minutes=25),  # 5 min buffer
                        attendee_count=4
                    ))
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            # Generate recommendations
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            
            # Should find micro-break opportunities
            assert len(recommendations) >= 1
            # All recommendations should be short (5-10 minutes)
            for rec in recommendations:
                assert rec.duration_minutes <= 10
    
    def test_large_gaps_scenario(self, app, test_user, recommendation_service):
        """Test day with large open blocks of free time"""
        with app.app_context():
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            
            # Only 3 meetings with large gaps
            events = [
                CalendarEvent(
                    user_id=test_user.id,
                    title="Morning Standup",
                    start_time=today.replace(hour=9),
                    end_time=today.replace(hour=9, minute=30),
                    attendee_count=6
                ),
                CalendarEvent(
                    user_id=test_user.id,
                    title="Lunch Meeting",
                    start_time=today.replace(hour=12),
                    end_time=today.replace(hour=13),
                    attendee_count=3
                ),
                CalendarEvent(
                    user_id=test_user.id,
                    title="End of Day Review",
                    start_time=today.replace(hour=16),
                    end_time=today.replace(hour=17),
                    attendee_count=5
                )
            ]
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            
            # Should suggest longer, more substantial breaks
            assert len(recommendations) >= 1
            # Should include at least one longer break (15+ minutes)
            long_breaks = [r for r in recommendations if r.duration_minutes >= 15]
            assert len(long_breaks) >= 1
    
    def test_completely_empty_day(self, app, test_user, recommendation_service):
        """Test algorithm on a completely empty day"""
        with app.app_context():
            # No meetings scheduled
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            
            # Should suggest 1-2 proactive wellness breaks
            assert len(recommendations) >= 1
            assert len(recommendations) <= 2
            
            # Should be spaced throughout the day
            if len(recommendations) > 1:
                time_diff = abs((recommendations[1].recommended_time - 
                               recommendations[0].recommended_time).total_seconds())
                assert time_diff >= 3600  # At least 1 hour apart
    
    def test_early_start_late_end(self, app, test_user, recommendation_service):
        """Test day that starts very early or ends very late"""
        with app.app_context():
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=6, minute=0, second=0, microsecond=0
            )
            
            # Early morning meeting and late evening meeting
            events = [
                CalendarEvent(
                    user_id=test_user.id,
                    title="Early Client Call",
                    start_time=today.replace(hour=6),
                    end_time=today.replace(hour=7),
                    attendee_count=4
                ),
                CalendarEvent(
                    user_id=test_user.id,
                    title="Late Team Sync",
                    start_time=today.replace(hour=20),
                    end_time=today.replace(hour=21),
                    attendee_count=6
                )
            ]
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            
            # Should account for extended workday
            assert len(recommendations) >= 1
            
            # Should suggest breaks appropriate for long workday
            total_break_time = sum(r.duration_minutes for r in recommendations)
            assert total_break_time >= 20  # More breaks for longer day
    
    def test_stress_context_matching(self, app, test_user, recommendation_service):
        """Test break type matching based on meeting context"""
        with app.app_context():
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=10, minute=0, second=0, microsecond=0
            )
            
            # High-stress meeting followed by gap
            stress_meeting = CalendarEvent(
                user_id=test_user.id,
                title="Quarterly Review - URGENT Deadline",
                start_time=today,
                end_time=today + timedelta(hours=2),
                attendee_count=8
            )
            
            db.session.add(stress_meeting)
            db.session.commit()
            
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            
            # Should suggest calming break after stress
            post_stress_recs = [r for r in recommendations 
                              if r.recommended_time > stress_meeting.end_time 
                              and r.recommended_time < stress_meeting.end_time + timedelta(hours=1)]
            
            assert len(post_stress_recs) >= 1
            # Should be calming/meditation type
            calming_types = ['meditation', 'breathing', 'mindfulness']
            assert any(break_type in post_stress_recs[0].break_type.lower() 
                      for break_type in calming_types)


class TestAlgorithmEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_overlapping_meetings(self, app, test_user, recommendation_service):
        """Test handling of overlapping meetings"""
        with app.app_context():
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=10, minute=0, second=0, microsecond=0
            )
            
            # Create overlapping meetings
            events = [
                CalendarEvent(
                    user_id=test_user.id,
                    title="Meeting A",
                    start_time=today,
                    end_time=today + timedelta(hours=2),
                    attendee_count=3
                ),
                CalendarEvent(
                    user_id=test_user.id,
                    title="Meeting B",
                    start_time=today + timedelta(minutes=90),
                    end_time=today + timedelta(hours=3),
                    attendee_count=4
                )
            ]
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            # Should handle gracefully without errors
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            assert isinstance(recommendations, list)
    
    def test_no_user_preferences(self, app, test_user, recommendation_service):
        """Test algorithm with minimal user preference data"""
        with app.app_context():
            # Remove user preferences
            test_user.preferred_break_duration = None
            test_user.biggest_challenge = None
            db.session.commit()
            
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=10, minute=0, second=0, microsecond=0
            )
            
            # Add one meeting
            event = CalendarEvent(
                user_id=test_user.id,
                title="Team Meeting",
                start_time=today,
                end_time=today + timedelta(hours=1),
                attendee_count=5
            )
            db.session.add(event)
            db.session.commit()
            
            # Should use sensible defaults
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            assert len(recommendations) >= 1
            assert recommendations[0].duration_minutes > 0


class TestPerformanceAndScalability:
    """Test algorithm performance with large datasets"""
    
    def test_large_number_of_events(self, app, test_user, recommendation_service):
        """Test performance with many calendar events"""
        with app.app_context():
            today = datetime.now(pytz.timezone(test_user.timezone)).replace(
                hour=8, minute=0, second=0, microsecond=0
            )
            
            # Create 100 events over 7 days
            events = []
            for day in range(7):
                for hour in range(8, 18):
                    start = today + timedelta(days=day, hours=hour-8)
                    events.append(CalendarEvent(
                        user_id=test_user.id,
                        title=f"Meeting Day {day} Hour {hour}",
                        start_time=start,
                        end_time=start + timedelta(minutes=45),
                        attendee_count=3
                    ))
            
            for event in events:
                db.session.add(event)
            db.session.commit()
            
            # Should complete in reasonable time
            import time
            start_time = time.time()
            recommendations = recommendation_service.generate_recommendations(test_user.id)
            end_time = time.time()
            
            # Should complete within 2 seconds
            assert (end_time - start_time) < 2.0
            assert isinstance(recommendations, list)