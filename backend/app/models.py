from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Subject(Base):
    """Represents a subject to study (e.g., Math, History)."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")

class StudySession(Base):
    """Records a specific study session for a subject."""
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=False)  
    notes = Column(Text, nullable=True)  

    subject = relationship("Subject", back_populates="sessions")

class Flashcard(Base):
    """Represents a study flashcard (Question/Answer)."""
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    front = Column(String, nullable=False)  
    back = Column(String, nullable=False)   

    subject = relationship("Subject")
