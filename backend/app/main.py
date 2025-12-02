from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <--- Importação Nova
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel 
from . import ai_service 

from . import models, schemas, crud, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Study Assistant Tool API")


origins = [
    "http://localhost:5173",  
    "http://localhost:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)
# -----------------------------------

@app.post("/subjects/", response_model=schemas.SubjectResponse)
def create_subject_endpoint(subject: schemas.SubjectCreate, db: Session = Depends(database.get_db)):
    return crud.create_subject(db=db, subject=subject)

@app.get("/subjects/", response_model=List[schemas.SubjectResponse])
def read_subjects(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_subjects(db, skip=skip, limit=limit)

@app.post("/sessions/", response_model=schemas.SessionResponse)
def log_study_session(session: schemas.SessionCreate, db: Session = Depends(database.get_db)):
    return crud.create_session(db=db, session=session)

@app.get("/subjects/{subject_id}/sessions", response_model=List[schemas.SessionResponse])
def read_subject_sessions(subject_id: int, db: Session = Depends(database.get_db)):
    return crud.get_sessions_by_subject(db, subject_id=subject_id)

@app.post("/flashcards/", response_model=schemas.FlashcardResponse)
def create_flashcard_endpoint(card: schemas.FlashcardCreate, db: Session = Depends(database.get_db)):
    """Create a new flashcard for a subject."""
    return crud.create_flashcard(db=db, flashcard=card)

@app.get("/subjects/{subject_id}/flashcards", response_model=List[schemas.FlashcardResponse])
def read_subject_flashcards(subject_id: int, db: Session = Depends(database.get_db)):
    """Get all flashcards for a specific subject."""
    return crud.get_flashcards_by_subject(db, subject_id=subject_id)

@app.delete("/subjects/{subject_id}")
def delete_subject_endpoint(subject_id: int, db: Session = Depends(database.get_db)):
    """Delete a subject and its related data."""
    db_subject = crud.delete_subject(db, subject_id)
    if db_subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"message": "Subject deleted successfully"}

class AIRequest(BaseModel):
    text: str

@app.post("/ai/generate_quiz")
def generate_quiz_endpoint(request: AIRequest):
    """Recebe um texto e retorna perguntas geradas por IA."""
    if len(request.text) < 50:
        raise HTTPException(status_code=400, detail="Texto muito curto. Escreva pelo menos 50 caracteres para a IA analisar.")
    
    quiz_data = ai_service.generate_quiz_from_text(request.text)
    
    if not quiz_data:
        raise HTTPException(status_code=500, detail="Falha ao gerar quiz. Tente novamente.")
        
    return quiz_data

@app.get("/")
def root():
    return {"message": "API is running"}