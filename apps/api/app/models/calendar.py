from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app import db

class CalendarConnection(db.Model):
    """Calendar OAuth connection model"""
    __tablename__ = 'calendar_connections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(20), nullable=False)  # 'google' or 'microsoft'
    access_token = Column(String, nullable=False)  # Should be encrypted in production
    refresh_token = Column(String, nullable=False)  # Should be encrypted in production
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    calendar_id = Column(String(255))
    last_sync_at = Column(DateTime(timezone=True))
    sync_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='calendar_connections')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='_user_provider_uc'),
    )
    
    def __repr__(self):
        return f'<CalendarConnection {self.provider} for user {self.user_id}>'


class CalendarEvent(db.Model):
    """Cached calendar events model"""
    __tablename__ = 'calendar_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    external_id = Column(String(255), nullable=False)
    title = Column(String(500))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    attendee_count = Column(Integer, default=1)
    is_recurring = Column(Boolean, default=False)
    
    # Meeting classification
    meeting_type = Column(String(50))  # 'focus', 'creative', 'review', 'social'
    intensity_score = Column(Integer, default=5)  # 1-10 scale
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='calendar_events')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'external_id', name='_user_event_uc'),
    )
    
    def __repr__(self):
        return f'<CalendarEvent {self.title} at {self.start_time}>'
    
    @property
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)