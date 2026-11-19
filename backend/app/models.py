from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Subject(Base):
    """Represents a subject or knowledge domain to master."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, default="Geral")
    target_retention = Column(Integer, default=85)

    sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="subject", cascade="all, delete-orphan")
    feynman_notes = relationship("FeynmanExplanation", back_populates="subject", cascade="all, delete-orphan")
    cornell_notes = relationship("CornellNote", back_populates="subject", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="subject", cascade="all, delete-orphan")


class StudySession(Base):
    """Records a specific active study or review session for a subject."""
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    subject = relationship("Subject", back_populates="sessions")


class Flashcard(Base):
    """Represents an Active Recall Flashcard with Spaced Repetition (SRS - Leitner/SM-2)."""
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    box_level = Column(Integer, default=1)  # 1 (Novo/Diário) a 5 (Dominado)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    difficulty_tag = Column(String, default="Médio")
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="flashcards")


class FeynmanExplanation(Base):
    """Stores a Feynman Technique explanation and its AI/Cognitive clarity evaluation."""
    __tablename__ = "feynman_explanations"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    concept_title = Column(String, nullable=False)
    target_audience = Column(String, default="Iniciante")
    explanation_text = Column(Text, nullable=False)
    clarity_score = Column(Integer, default=0)
    strengths_json = Column(Text, default="[]")
    blind_spots_json = Column(Text, default="[]")
    socratic_questions_json = Column(Text, default="[]")
    suggested_analogy = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="feynman_notes")


class CornellNote(Base):
    """Represents a structured Cornell Note (Cues, Detailed Notes, and Synthesis Summary)."""
    __tablename__ = "cornell_notes"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String, nullable=False)
    cues = Column(Text, nullable=False)      # Palavras-chave / Perguntas-guia
    notes = Column(Text, nullable=False)     # Anotações principais
    summary = Column(Text, nullable=False)   # Síntese final com as próprias palavras
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="cornell_notes")


class QuizAttempt(Base):
    """Records a completed AI Active Recall Quiz attempt for retention tracking."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    topic_summary = Column(String, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percent = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="quiz_attempts")
