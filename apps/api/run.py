#!/usr/bin/env python
"""Flask application entry point"""
import os
from app import create_app, db

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Add models to flask shell context"""
    from app.models import (
        User, CalendarConnection, CalendarEvent,
        BreakSession, BreakRecommendation, CompletedBreak,
        UserStreak, CompanyAnalytics
    )
    return {
        'db': db,
        'User': User,
        'CalendarConnection': CalendarConnection,
        'CalendarEvent': CalendarEvent,
        'BreakSession': BreakSession,
        'BreakRecommendation': BreakRecommendation,
        'CompletedBreak': CompletedBreak,
        'UserStreak': UserStreak,
        'CompanyAnalytics': CompanyAnalytics,
    }

if __name__ == '__main__':
    # Run the development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )