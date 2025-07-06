-- takeabreak.life Database Setup
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    company_domain VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferred_break_duration INTEGER DEFAULT 10,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    biggest_challenge VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_company ON users (company_domain);

-- Calendar connections table
CREATE TABLE IF NOT EXISTS calendar_connections (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    calendar_id VARCHAR(255),
    last_sync_at TIMESTAMPTZ,
    sync_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_calendar_user ON calendar_connections (user_id);

-- Break sessions table
CREATE TABLE IF NOT EXISTS break_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    thumbnail_url TEXT,
    content_url TEXT NOT NULL,
    content_type VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_category ON break_sessions (category);
CREATE INDEX IF NOT EXISTS idx_sessions_duration ON break_sessions (duration_minutes);

-- Calendar events table
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    external_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    attendee_count INTEGER DEFAULT 1,
    is_recurring BOOLEAN DEFAULT false,
    meeting_type VARCHAR(50),
    intensity_score INTEGER DEFAULT 5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_events_user_time ON calendar_events (user_id, start_time, end_time);

-- Break recommendations table
CREATE TABLE IF NOT EXISTS break_recommendations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES break_sessions(id),
    recommended_time TIMESTAMPTZ NOT NULL,
    reason TEXT,
    score FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_time ON break_recommendations (user_id, recommended_time);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON break_recommendations (user_id, status);

-- Completed breaks table
CREATE TABLE IF NOT EXISTS completed_breaks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES break_sessions(id),
    recommendation_id UUID REFERENCES break_recommendations(id),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    completion_percentage INTEGER DEFAULT 0,
    felt_better BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_completed_user_date ON completed_breaks (user_id, started_at);
CREATE INDEX IF NOT EXISTS idx_completed_session ON completed_breaks (session_id);

-- User streaks table
CREATE TABLE IF NOT EXISTS user_streaks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_break_date DATE,
    streak_started_at DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_streaks_user ON user_streaks (user_id);

-- Company analytics table
CREATE TABLE IF NOT EXISTS company_analytics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    company_domain VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    total_breaks INTEGER DEFAULT 0,
    avg_breaks_per_user FLOAT DEFAULT 0,
    popular_category VARCHAR(50),
    popular_time_slot VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_domain, date)
);

CREATE INDEX IF NOT EXISTS idx_analytics_company_date ON company_analytics (company_domain, date);

-- Create alembic version table
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Mark migration as applied
INSERT INTO alembic_version (version_num) VALUES ('001') ON CONFLICT DO NOTHING;