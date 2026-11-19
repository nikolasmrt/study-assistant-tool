from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, crud, database, ai_service

models.Base.metadata.create_all(bind=database.engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = database.SessionLocal()
    try:
        crud.ensure_schema_and_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="NeuroStudy AI — Cognitive Study Assistant API",
    description="Plataforma Full-Stack de Aprendizagem Ativa: Repetição Espaçada (SRS Leitner/SM-2), Laboratório Método Feynman, Caderno Cornell e Quizzes com IA.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "API is running",
        "service": "NeuroStudy AI — Cognitive Study Assistant",
        "version": "2.0.0"
    }


@app.get("/analytics/overview", response_model=schemas.GlobalAnalyticsResponse)
def get_analytics_overview(db: Session = Depends(database.get_db)):
    """Retorna métricas globais de retenção cognitiva, distribuição Leitner SRS, Feynman e Quizzes."""
    crud.ensure_schema_and_seed(db)
    return crud.get_global_analytics(db)


@app.get("/subjects/{subject_id}/analytics", response_model=schemas.SubjectCognitiveStats)
def get_subject_analytics(subject_id: int, db: Session = Depends(database.get_db)):
    """Retorna métricas cognitivas detalhadas de uma matéria específica."""
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return crud.get_subject_cognitive_stats(db, subject)


@app.post("/subjects/", response_model=schemas.SubjectResponse)
def create_subject_endpoint(subject: schemas.SubjectCreate, db: Session = Depends(database.get_db)):
    return crud.create_subject(db=db, subject=subject)


@app.get("/subjects/", response_model=List[schemas.SubjectResponse])
def read_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    crud.ensure_schema_and_seed(db)
    return crud.get_subjects(db, skip=skip, limit=limit)


@app.delete("/subjects/{subject_id}")
def delete_subject_endpoint(subject_id: int, db: Session = Depends(database.get_db)):
    """Delete a subject and its related data."""
    db_subject = crud.delete_subject(db, subject_id)
    if db_subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted successfully"}


@app.post("/sessions/", response_model=schemas.SessionResponse)
def log_study_session(session: schemas.SessionCreate, db: Session = Depends(database.get_db)):
    return crud.create_session(db=db, session=session)


@app.get("/subjects/{subject_id}/sessions", response_model=List[schemas.SessionResponse])
def read_subject_sessions(subject_id: int, db: Session = Depends(database.get_db)):
    return crud.get_sessions_by_subject(db, subject_id=subject_id)


@app.post("/flashcards/", response_model=schemas.FlashcardResponse)
def create_flashcard_endpoint(card: schemas.FlashcardCreate, db: Session = Depends(database.get_db)):
    """Create a new SRS flashcard for a subject."""
    return crud.create_flashcard(db=db, flashcard=card)


@app.get("/subjects/{subject_id}/flashcards", response_model=List[schemas.FlashcardResponse])
def read_subject_flashcards(subject_id: int, db: Session = Depends(database.get_db)):
    """Get all flashcards for a specific subject."""
    return crud.get_flashcards_by_subject(db, subject_id=subject_id)


@app.post("/flashcards/{card_id}/review", response_model=schemas.FlashcardResponse)
def review_flashcard_endpoint(
    card_id: int,
    review: schemas.FlashcardReviewRequest,
    db: Session = Depends(database.get_db)
):
    """Updates flashcard Leitner box, ease factor, and next review schedule using SRS."""
    updated = crud.review_flashcard(db, card_id=card_id, rating=review.rating)
    if not updated:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return updated


@app.delete("/flashcards/{card_id}")
def delete_flashcard_endpoint(card_id: int, db: Session = Depends(database.get_db)):
    deleted = crud.delete_flashcard(db, card_id=card_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return {"message": "Flashcard deleted successfully"}


@app.post("/ai/generate_quiz")
def generate_quiz_endpoint(request: schemas.AIQuizRequest):
    """Recebe um texto de estudo e retorna perguntas de revisão ativa com explicações."""
    if len(request.text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Texto muito curto. Escreva pelo menos 50 caracteres para a análise cognitiva."
        )

    quiz_data = ai_service.generate_quiz_from_text(
        request.text,
        num_questions=request.num_questions or 5,
        difficulty=request.difficulty or "Intermediário"
    )
    if not quiz_data:
        raise HTTPException(status_code=500, detail="Falha ao gerar quiz. Tente novamente.")
    return quiz_data


@app.post("/ai/extract_flashcards", response_model=List[schemas.FlashcardResponse])
def extract_flashcards_endpoint(
    request: schemas.AutoFlashcardRequest,
    db: Session = Depends(database.get_db)
):
    """Extrai automaticamente flashcards de revisão ativa a partir de um texto e salva no deck SRS."""
    if len(request.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Forneça um texto com pelo menos 30 caracteres.")

    extracted = ai_service.extract_flashcards_from_text(request.text, max_cards=request.max_cards or 5)
    created_cards = []
    for item in extracted:
        card_in = schemas.FlashcardCreate(
            subject_id=request.subject_id,
            front=item["front"],
            back=item["back"],
            difficulty_tag=item.get("difficulty_tag", "Médio")
        )
        created_cards.append(crud.create_flashcard(db, card_in))
    return created_cards


@app.post("/ai/feynman_evaluate", response_model=schemas.FeynmanResponse)
def evaluate_feynman_endpoint(
    request: schemas.FeynmanEvaluateRequest,
    db: Session = Depends(database.get_db)
):
    """Avalia a explicação de um conceito pelo Método Feynman e salva no histórico da matéria."""
    if len(request.explanation_text.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="A explicação precisa ter pelo menos 20 caracteres para ser avaliada."
        )

    evaluation = ai_service.evaluate_feynman_explanation(
        concept_title=request.concept_title,
        explanation_text=request.explanation_text,
        target_audience=request.target_audience or "Iniciante"
    )

    saved_id = None
    created_at = None
    if request.subject_id:
        saved = crud.create_feynman_explanation(
            db=db,
            subject_id=request.subject_id,
            concept_title=request.concept_title,
            target_audience=request.target_audience or "Iniciante",
            explanation_text=request.explanation_text,
            evaluation=evaluation
        )
        saved_id = saved.id
        created_at = saved.created_at

    return schemas.FeynmanResponse(
        id=saved_id,
        subject_id=request.subject_id,
        concept_title=request.concept_title,
        target_audience=request.target_audience or "Iniciante",
        explanation_text=request.explanation_text,
        clarity_score=evaluation["clarity_score"],
        readability_level=evaluation["readability_level"],
        strengths=evaluation["strengths"],
        blind_spots=evaluation["blind_spots"],
        socratic_questions=evaluation["socratic_questions"],
        suggested_analogy=evaluation["suggested_analogy"],
        created_at=created_at
    )


@app.get("/subjects/{subject_id}/feynman", response_model=List[schemas.FeynmanResponse])
def read_subject_feynman_history(subject_id: int, db: Session = Depends(database.get_db)):
    return crud.get_feynman_by_subject(db, subject_id=subject_id)


@app.post("/cornell/", response_model=schemas.CornellNoteResponse)
def create_cornell_note_endpoint(note: schemas.CornellNoteCreate, db: Session = Depends(database.get_db)):
    return crud.create_cornell_note(db, note=note)


@app.get("/subjects/{subject_id}/cornell", response_model=List[schemas.CornellNoteResponse])
def read_subject_cornell_notes(subject_id: int, db: Session = Depends(database.get_db)):
    return crud.get_cornell_by_subject(db, subject_id=subject_id)


@app.delete("/cornell/{note_id}")
def delete_cornell_note_endpoint(note_id: int, db: Session = Depends(database.get_db)):
    deleted = crud.delete_cornell_note(db, note_id=note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cornell note not found")
    return {"message": "Cornell note deleted"}


@app.post("/cornell/{note_id}/to-flashcards", response_model=List[schemas.FlashcardResponse])
def convert_cornell_to_flashcards(note_id: int, db: Session = Depends(database.get_db)):
    """Converte automaticamente uma ficha do Método Cornell em Flashcards SRS."""
    note = db.query(models.CornellNote).filter(models.CornellNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Cornell note not found")

    combined_text = f"{note.notes}\n{note.summary}"
    extracted = ai_service.extract_flashcards_from_text(combined_text, max_cards=4)
    created_cards = []
    for item in extracted:
        card_in = schemas.FlashcardCreate(
            subject_id=note.subject_id,
            front=item["front"],
            back=item["back"],
            difficulty_tag=item.get("difficulty_tag", "Médio")
        )
        created_cards.append(crud.create_flashcard(db, card_in))
    return created_cards


@app.post("/quizzes/attempts", response_model=schemas.QuizAttemptResponse)
def record_quiz_attempt(attempt: schemas.QuizAttemptCreate, db: Session = Depends(database.get_db)):
    return crud.create_quiz_attempt(db, attempt=attempt)


@app.get("/subjects/{subject_id}/quizzes", response_model=List[schemas.QuizAttemptResponse])
def read_subject_quiz_attempts(subject_id: int, db: Session = Depends(database.get_db)):
    return crud.get_quiz_attempts_by_subject(db, subject_id=subject_id)
