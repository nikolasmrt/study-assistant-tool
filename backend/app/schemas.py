from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime


class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = "Geral"
    target_retention: Optional[int] = 85


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SessionBase(BaseModel):
    duration_minutes: int
    notes: Optional[str] = None


class SessionCreate(SessionBase):
    subject_id: int


class SessionResponse(SessionBase):
    id: int
    start_time: datetime
    subject_id: int
    model_config = ConfigDict(from_attributes=True)


class FlashcardBase(BaseModel):
    front: str
    back: str
    difficulty_tag: Optional[str] = "Médio"


class FlashcardCreate(FlashcardBase):
    subject_id: int


class FlashcardReviewRequest(BaseModel):
    rating: str  # "again" | "hard" | "good" | "easy"


class FlashcardResponse(FlashcardBase):
    id: int
    subject_id: int
    box_level: int = 1
    ease_factor: float = 2.5
    interval_days: int = 0
    review_count: int = 0
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class FeynmanEvaluateRequest(BaseModel):
    subject_id: Optional[int] = None
    concept_title: str
    target_audience: Optional[str] = "Iniciante"
    explanation_text: str


class FeynmanResponse(BaseModel):
    id: Optional[int] = None
    subject_id: Optional[int] = None
    concept_title: str
    target_audience: str
    explanation_text: str
    clarity_score: int
    readability_level: str
    strengths: List[str]
    blind_spots: List[str]
    socratic_questions: List[str]
    suggested_analogy: str
    created_at: Optional[datetime] = None


class CornellNoteBase(BaseModel):
    title: str
    cues: str
    notes: str
    summary: str


class CornellNoteCreate(CornellNoteBase):
    subject_id: int


class CornellNoteResponse(CornellNoteBase):
    id: int
    subject_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class QuizAttemptCreate(BaseModel):
    subject_id: int
    topic_summary: str
    total_questions: int
    correct_answers: int


class QuizAttemptResponse(BaseModel):
    id: int
    subject_id: int
    topic_summary: str
    total_questions: int
    correct_answers: int
    score_percent: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AIQuizRequest(BaseModel):
    text: str
    num_questions: Optional[int] = 5
    difficulty: Optional[str] = "Intermediário"


class AutoFlashcardRequest(BaseModel):
    subject_id: int
    text: str
    max_cards: Optional[int] = 5


class SubjectCognitiveStats(BaseModel):
    subject_id: int
    subject_name: str
    category: str
    total_cards: int
    due_cards: int
    mastered_cards: int
    retention_index: float
    box_distribution: Dict[str, int]
    feynman_count: int
    avg_feynman_score: float
    cornell_count: int
    quiz_count: int
    avg_quiz_score: float
    total_study_minutes: int


class GlobalAnalyticsResponse(BaseModel):
    total_subjects: int
    total_flashcards: int
    due_flashcards_today: int
    mastered_flashcards: int
    global_retention_index: float
    box_distribution: Dict[str, int]
    total_feynman_evaluations: int
    avg_feynman_clarity: float
    total_cornell_notes: int
    total_quizzes_taken: int
    avg_quiz_accuracy: float
    total_study_minutes: int
    subjects_breakdown: List[SubjectCognitiveStats]
