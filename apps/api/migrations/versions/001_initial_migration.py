"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-12-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('google_id', sa.String(255), unique=True),
        sa.Column('microsoft_id', sa.String(255), unique=True),
        sa.Column('full_name', sa.String(255)),
        sa.Column('avatar_url', sa.Text()),
        sa.Column('company_domain', sa.String(255)),
        sa.Column('timezone', sa.String(50), server_default='UTC'),
        sa.Column('preferred_break_duration', sa.Integer(), server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('biggest_challenge', sa.String(50)),
    )
    
    # Create indexes for users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_company', 'users', ['company_domain'])
    
    # Calendar connections table
    op.create_table('calendar_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('calendar_id', sa.String(255)),
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.Column('sync_enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create unique constraint and index
    op.create_unique_constraint('_user_provider_uc', 'calendar_connections', ['user_id', 'provider'])
    op.create_index('idx_calendar_user', 'calendar_connections', ['user_id'])
    
    # Break sessions table
    op.create_table('break_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('thumbnail_url', sa.Text()),
        sa.Column('content_url', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(50)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create indexes for break sessions
    op.create_index('idx_sessions_category', 'break_sessions', ['category'])
    op.create_index('idx_sessions_duration', 'break_sessions', ['duration_minutes'])
    
    # Calendar events table
    op.create_table('calendar_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attendee_count', sa.Integer(), server_default='1'),
        sa.Column('is_recurring', sa.Boolean(), server_default='false'),
        sa.Column('meeting_type', sa.String(50)),
        sa.Column('intensity_score', sa.Integer(), server_default='5'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create constraints and indexes
    op.create_unique_constraint('_user_event_uc', 'calendar_events', ['user_id', 'external_id'])
    op.create_index('idx_events_user_time', 'calendar_events', ['user_id', 'start_time', 'end_time'])
    
    # Break recommendations table
    op.create_table('break_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('break_sessions.id'), nullable=False),
        sa.Column('recommended_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_recommendations_user_time', 'break_recommendations', ['user_id', 'recommended_time'])
    op.create_index('idx_recommendations_status', 'break_recommendations', ['user_id', 'status'])
    
    # Completed breaks table
    op.create_table('completed_breaks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('break_sessions.id'), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('break_recommendations.id')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_seconds', sa.Integer()),
        sa.Column('completion_percentage', sa.Integer(), server_default='0'),
        sa.Column('felt_better', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_completed_user_date', 'completed_breaks', ['user_id', 'started_at'])
    op.create_index('idx_completed_session', 'completed_breaks', ['session_id'])
    op.create_index('idx_completed_breaks_date', 'completed_breaks', ['started_at'])
    
    # User streaks table
    op.create_table('user_streaks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('current_streak', sa.Integer(), server_default='0'),
        sa.Column('longest_streak', sa.Integer(), server_default='0'),
        sa.Column('last_break_date', sa.Date()),
        sa.Column('streak_started_at', sa.Date()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create index
    op.create_index('idx_streaks_user', 'user_streaks', ['user_id'])
    
    # Company analytics table
    op.create_table('company_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_domain', sa.String(255), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_users', sa.Integer(), server_default='0'),
        sa.Column('active_users', sa.Integer(), server_default='0'),
        sa.Column('total_breaks', sa.Integer(), server_default='0'),
        sa.Column('avg_breaks_per_user', sa.Float(), server_default='0'),
        sa.Column('popular_category', sa.String(50)),
        sa.Column('popular_time_slot', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create constraints and indexes
    op.create_unique_constraint('_company_date_uc', 'company_analytics', ['company_domain', 'date'])
    op.create_index('idx_analytics_company_date', 'company_analytics', ['company_domain', 'date'])
    op.create_index('idx_recommendations_expired', 'break_recommendations', ['expires_at'], postgresql_where=sa.text("status = 'pending'"))


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('company_analytics')
    op.drop_table('user_streaks')
    op.drop_table('completed_breaks')
    op.drop_table('break_recommendations')
    op.drop_table('calendar_events')
    op.drop_table('break_sessions')
    op.drop_table('calendar_connections')
    op.drop_table('users')
    
    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')