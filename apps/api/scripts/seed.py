#!/usr/bin/env python
"""Seed script for MVP break content"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import BreakSession

def seed_break_sessions():
    """Seed the 5 MVP break sessions"""
    
    sessions = [
        {
            'title': '5-Minute Breathing Exercise',
            'description': 'A guided breathing exercise to reduce stress and increase focus. Perfect between meetings.',
            'category': 'mindfulness',
            'duration_minutes': 5,
            'thumbnail_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',
            'content_url': 'https://example.com/audio/breathing-5min.mp3',
            'content_type': 'audio',
        },
        {
            'title': '10-Minute Guided Meditation',
            'description': 'A calming meditation to reset your mind and restore inner peace during busy workdays.',
            'category': 'mindfulness',
            'duration_minutes': 10,
            'thumbnail_url': 'https://images.unsplash.com/photo-1497294815431-9365093b7331?w=400',
            'content_url': 'https://example.com/audio/meditation-10min.mp3',
            'content_type': 'audio',
        },
        {
            'title': '5-Minute Desk Stretches',
            'description': 'Simple stretches to relieve tension and improve posture without leaving your desk.',
            'category': 'movement',
            'duration_minutes': 5,
            'thumbnail_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
            'content_url': 'https://example.com/video/desk-stretches-5min.mp4',
            'content_type': 'video',
        },
        {
            'title': '2-Minute Eye Rest',
            'description': 'Quick eye exercises to reduce digital eye strain and refresh your vision.',
            'category': 'rest',
            'duration_minutes': 2,
            'thumbnail_url': 'https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=400',
            'content_url': 'https://example.com/audio/eye-rest-2min.mp3',
            'content_type': 'audio',
        },
        {
            'title': '15-Minute Power Nap',
            'description': 'A guided power nap with gentle awakening to boost your afternoon energy.',
            'category': 'rest',
            'duration_minutes': 15,
            'thumbnail_url': 'https://images.unsplash.com/photo-1520350094754-f0fdcac35c1c?w=400',
            'content_url': 'https://example.com/audio/power-nap-15min.mp3',
            'content_type': 'audio',
        },
    ]
    
    # Check if sessions already exist
    existing_count = BreakSession.query.count()
    if existing_count > 0:
        print(f"Break sessions already exist ({existing_count} found). Skipping seed.")
        return
    
    # Create sessions
    for session_data in sessions:
        session = BreakSession(**session_data)
        db.session.add(session)
    
    db.session.commit()
    print(f"Successfully seeded {len(sessions)} break sessions!")

def main():
    """Main function to run seeding"""
    app = create_app()
    
    with app.app_context():
        print("Starting database seeding...")
        seed_break_sessions()
        print("Database seeding completed!")

if __name__ == '__main__':
    main()