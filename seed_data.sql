-- Seed MVP break sessions
INSERT INTO break_sessions (title, description, category, duration_minutes, thumbnail_url, content_url, content_type) VALUES
(
    '5-Minute Breathing Exercise',
    'A guided breathing exercise to reduce stress and increase focus. Perfect between meetings.',
    'mindfulness',
    5,
    'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',
    'https://example.com/audio/breathing-5min.mp3',
    'audio'
),
(
    '10-Minute Guided Meditation',
    'A calming meditation to reset your mind and restore inner peace during busy workdays.',
    'mindfulness',
    10,
    'https://images.unsplash.com/photo-1497294815431-9365093b7331?w=400',
    'https://example.com/audio/meditation-10min.mp3',
    'audio'
),
(
    '5-Minute Desk Stretches',
    'Simple stretches to relieve tension and improve posture without leaving your desk.',
    'movement',
    5,
    'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400',
    'https://example.com/video/desk-stretches-5min.mp4',
    'video'
),
(
    '2-Minute Eye Rest',
    'Quick eye exercises to reduce digital eye strain and refresh your vision.',
    'rest',
    2,
    'https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=400',
    'https://example.com/audio/eye-rest-2min.mp3',
    'audio'
),
(
    '15-Minute Power Nap',
    'A guided power nap with gentle awakening to boost your afternoon energy.',
    'rest',
    15,
    'https://images.unsplash.com/photo-1520350094754-f0fdcac35c1c?w=400',
    'https://example.com/audio/power-nap-15min.mp3',
    'audio'
) ON CONFLICT DO NOTHING;