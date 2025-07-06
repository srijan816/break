from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app import db

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True)
    microsoft_id = Column(String(255), unique=True)
    full_name = Column(String(255))
    avatar_url = Column(String)
    company_domain = Column(String(255), index=True)
    timezone = Column(String(50), default='UTC')
    preferred_break_duration = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Onboarding answers
    biggest_challenge = Column(String(50))  # 'meetings', 'focus', 'energy', 'stress'
    
    # Relationships
    calendar_connections = relationship('CalendarConnection', back_populates='user', cascade='all, delete-orphan')
    calendar_events = relationship('CalendarEvent', back_populates='user', cascade='all, delete-orphan')
    recommendations = relationship('BreakRecommendation', back_populates='user', cascade='all, delete-orphan')
    completed_breaks = relationship('CompletedBreak', back_populates='user', cascade='all, delete-orphan')
    streak = relationship('UserStreak', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'company_domain': self.company_domain,
            'timezone': self.timezone,
            'preferred_break_duration': self.preferred_break_duration,
            'biggest_challenge': self.biggest_challenge,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }