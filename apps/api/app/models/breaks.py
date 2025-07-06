from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app import db

class BreakSession(db.Model):
    """Break content library model"""
    __tablename__ = 'break_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # 'mindfulness', 'movement', 'rest'
    duration_minutes = Column(Integer, nullable=False)
    thumbnail_url = Column(String)
    content_url = Column(String, nullable=False)
    content_type = Column(String(50))  # 'audio', 'video', 'mixed'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    recommendations = relationship('BreakRecommendation', back_populates='session')
    completed_breaks = relationship('CompletedBreak', back_populates='session')
    
    def __repr__(self):
        return f'<BreakSession {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'duration_minutes': self.duration_minutes,
            'thumbnail_url': self.thumbnail_url,
            'content_url': self.content_url,
            'content_type': self.content_type,
        }


class BreakRecommendation(db.Model):
    """AI-generated break recommendations model"""
    __tablename__ = 'break_recommendations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('break_sessions.id'), nullable=False)
    recommended_time = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text)  # "After your 2-hour meeting block"
    score = Column(Float, nullable=False)  # Algorithm confidence score
    status = Column(String(20), default='pending')  # 'pending', 'accepted', 'dismissed', 'completed'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='recommendations')
    session = relationship('BreakSession', back_populates='recommendations')
    completed_break = relationship('CompletedBreak', back_populates='recommendation', uselist=False)
    
    def __repr__(self):
        return f'<BreakRecommendation for {self.user_id} at {self.recommended_time}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'session': self.session.to_dict() if self.session else None,
            'recommended_time': self.recommended_time.isoformat(),
            'reason': self.reason,
            'status': self.status,
        }


class CompletedBreak(db.Model):
    """User's completed break sessions model"""
    __tablename__ = 'completed_breaks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('break_sessions.id'), nullable=False)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey('break_recommendations.id'), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)  # Actual time spent
    completion_percentage = Column(Integer, default=0)  # 0-100
    felt_better = Column(Boolean)  # Quick feedback
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='completed_breaks')
    session = relationship('BreakSession', back_populates='completed_breaks')
    recommendation = relationship('BreakRecommendation', back_populates='completed_break')
    
    def __repr__(self):
        return f'<CompletedBreak {self.session_id} by {self.user_id}>']