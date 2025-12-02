from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: int
    class Config:
        from_attributes = True 

class SessionBase(BaseModel):
    duration_minutes: int
    notes: Optional[str] = None

class SessionCreate(SessionBase):
    subject_id: int

class SessionResponse(SessionBase):
    id: int
    start_time: datetime
    subject_id: int
    class Config:
        from_attributes = True

class FlashcardBase(BaseModel):
    front: str
    back: str

class FlashcardCreate(FlashcardBase):
    subject_id: int

class FlashcardResponse(FlashcardBase):
    id: int
    subject_id: int
    class Config:
        from_attributes = True