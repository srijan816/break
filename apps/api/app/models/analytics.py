from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app import db

class UserStreak(db.Model):
    """User streak tracking model"""
    __tablename__ = 'user_streaks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_break_date = Column(Date)
    streak_started_at = Column(Date)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='streak')
    
    def __repr__(self):
        return f'<UserStreak {self.user_id}: {self.current_streak} days>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_break_date': self.last_break_date.isoformat() if self.last_break_date else None,
        }


class CompanyAnalytics(db.Model):
    """Aggregated company-level analytics model"""
    __tablename__ = 'company_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_domain = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Took at least one break
    total_breaks = Column(Integer, default=0)
    avg_breaks_per_user = Column(Float, default=0)
    popular_category = Column(String(50))
    popular_time_slot = Column(String(20))  # 'morning', 'afternoon', etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('company_domain', 'date', name='_company_date_uc'),
    )
    
    def __repr__(self):
        return f'<CompanyAnalytics {self.company_domain} on {self.date}>'