-- takeabreak.life MVP Database Schema
-- PostgreSQL with Row Level Security (RLS)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (core authentication and profile)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    company_domain VARCHAR(255), -- Extracted from email
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferred_break_duration INTEGER DEFAULT 10, -- minutes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    
    -- MVP onboarding answers
    biggest_challenge VARCHAR(50) -- 'meetings', 'focus', 'energy', 'stress'
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_company ON users (company_domain);

-- Calendar connections (OAuth tokens)
CREATE TABLE calendar_connections (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL, -- 'google' or 'microsoft'
    access_token TEXT NOT NULL, -- Encrypted
    refresh_token TEXT NOT NULL, -- Encrypted
    token_expires_at TIMESTAMPTZ NOT NULL,
    calendar_id VARCHAR(255), -- Primary calendar ID
    last_sync_at TIMESTAMPTZ,
    sync_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, provider)
);

CREATE INDEX idx_calendar_user ON calendar_connections (user_id);

-- Break content library (seeded data for MVP)
CREATE TABLE break_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'mindfulness', 'movement', 'rest'
    duration_minutes INTEGER NOT NULL,
    thumbnail_url TEXT,
    content_url TEXT NOT NULL, -- S3/CDN URL
    content_type VARCHAR(50), -- 'audio', 'video', 'mixed'
    
    -- MVP: Simple content, no complex metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for break_sessions
CREATE INDEX idx_sessions_category ON break_sessions (category);
CREATE INDEX idx_sessions_duration ON break_sessions (duration_minutes);

-- User's calendar events (cached for analysis)
CREATE TABLE calendar_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL, -- Google/MS event ID
    title VARCHAR(500),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    attendee_count INTEGER DEFAULT 1,
    is_recurring BOOLEAN DEFAULT false,
    
    -- Meeting classification for break recommendations
    meeting_type VARCHAR(50), -- 'focus', 'creative', 'review', 'social'
    intensity_score INTEGER DEFAULT 5, -- 1-10 scale
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, external_id)
);

CREATE INDEX idx_events_user_time ON calendar_events (user_id, start_time, end_time);

-- Break recommendations (AI suggestions)
CREATE TABLE break_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES break_sessions(id),
    recommended_time TIMESTAMPTZ NOT NULL,
    reason TEXT, -- "After your 2-hour meeting block"
    score FLOAT NOT NULL, -- Algorithm confidence score
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'dismissed', 'completed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL -- End of workday
);

-- Indexes for break_recommendations
CREATE INDEX idx_recommendations_user_time ON break_recommendations (user_id, recommended_time);
CREATE INDEX idx_recommendations_status ON break_recommendations (user_id, status);

-- Completed breaks (user activity)
CREATE TABLE completed_breaks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES break_sessions(id),
    recommendation_id UUID REFERENCES break_recommendations(id),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER, -- Actual time spent
    completion_percentage INTEGER DEFAULT 0, -- 0-100
    
    -- Simple MVP feedback
    felt_better BOOLEAN, -- Post-session quick feedback
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for completed_breaks
CREATE INDEX idx_completed_user_date ON completed_breaks (user_id, started_at);
CREATE INDEX idx_completed_session ON completed_breaks (session_id);

-- User streaks (motivation feature)
CREATE TABLE user_streaks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_break_date DATE,
    streak_started_at DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for user_streaks
CREATE INDEX idx_streaks_user ON user_streaks (user_id);

-- Company aggregates (privacy-preserving analytics)
CREATE TABLE company_analytics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    company_domain VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0, -- Took at least one break
    total_breaks INTEGER DEFAULT 0,
    avg_breaks_per_user FLOAT DEFAULT 0,
    popular_category VARCHAR(50),
    popular_time_slot VARCHAR(20), -- 'morning', 'afternoon', etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(company_domain, date)
);

CREATE INDEX idx_analytics_company_date ON company_analytics (company_domain, date);

-- Additional performance indexes
CREATE INDEX idx_completed_breaks_date ON completed_breaks(started_at);
CREATE INDEX idx_recommendations_expired ON break_recommendations(expires_at) WHERE status = 'pending';

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_calendar_connections_updated_at BEFORE UPDATE ON calendar_connections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_calendar_events_updated_at BEFORE UPDATE ON calendar_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update streak (called after each completed break)
CREATE OR REPLACE FUNCTION update_user_streak(p_user_id UUID)
RETURNS void AS $$
DECLARE
    v_last_break_date DATE;
    v_today DATE := CURRENT_DATE;
    v_current_streak INTEGER;
BEGIN
    SELECT last_break_date, current_streak 
    INTO v_last_break_date, v_current_streak
    FROM user_streaks 
    WHERE user_id = p_user_id;
    
    IF NOT FOUND THEN
        -- First break ever
        INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_break_date, streak_started_at)
        VALUES (p_user_id, 1, 1, v_today, v_today);
    ELSIF v_last_break_date = v_today THEN
        -- Already took a break today, no change
        RETURN;
    ELSIF v_last_break_date = v_today - INTERVAL '1 day' OR 
          (EXTRACT(DOW FROM v_last_break_date) = 5 AND EXTRACT(DOW FROM v_today) = 1) THEN
        -- Streak continues (including weekend skip)
        UPDATE user_streaks 
        SET current_streak = current_streak + 1,
            longest_streak = GREATEST(longest_streak, current_streak + 1),
            last_break_date = v_today
        WHERE user_id = p_user_id;
    ELSE
        -- Streak broken
        UPDATE user_streaks 
        SET current_streak = 1,
            last_break_date = v_today,
            streak_started_at = v_today
        WHERE user_id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create alembic version table for migration tracking
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Mark initial migration as applied
INSERT INTO alembic_version (version_num) VALUES ('001') ON CONFLICT DO NOTHING;