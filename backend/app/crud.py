from sqlalchemy.orm import Session
from . import models, schemas

def create_subject(db: Session, subject: schemas.SubjectCreate) -> models.Subject:
    """Creates a new subject in the database."""
    db_subject = models.Subject(name=subject.name, description=subject.description)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subjects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Subject]:
    """Retrieves a list of subjects."""
    return db.query(models.Subject).offset(skip).limit(limit).all()

def create_session(db: Session, session: schemas.SessionCreate) -> models.StudySession:
    """Creates a new study session entry."""
    db_session = models.StudySession(
        subject_id=session.subject_id,
        duration_minutes=session.duration_minutes,
        notes=session.notes
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_sessions_by_subject(db: Session, subject_id: int) -> list[models.StudySession]:
    """Retrieves all sessions for a specific subject."""
    return db.query(models.StudySession).filter(models.StudySession.subject_id == subject_id).all()


def create_flashcard(db: Session, flashcard: schemas.FlashcardCreate) -> models.Flashcard:
    db_flashcard = models.Flashcard(
        subject_id=flashcard.subject_id,
        front=flashcard.front,
        back=flashcard.back
    )
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)
    return db_flashcard

def delete_subject(db: Session, subject_id: int):
    """Deletes a subject by ID."""
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if db_subject:
        db.delete(db_subject)
        db.commit()
    return db_subject

def get_flashcards_by_subject(db: Session, subject_id: int) -> list[models.Flashcard]:
    return db.query(models.Flashcard).filter(models.Flashcard.subject_id == subject_id).all()