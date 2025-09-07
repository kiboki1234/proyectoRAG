from pydantic import BaseModel
from typing import List, Optional

class AskRequest(BaseModel):
    question: str
    source: Optional[str] = None  # nombre (o parte) del archivo a filtrar

class Citation(BaseModel):
    id: int
    score: float
    text: str
    page: Optional[int] = None  # número de página (base 1) si existe
    source: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
