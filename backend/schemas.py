from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str = Field(..., max_length=500)
    content: str = Field(..., min_length=1)


class DocumentOut(BaseModel):
    id: int
    title: str
    source_type: str
    created_at: datetime
    quiz_count: int = 0

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentOut):
    content: str


class GenerateRequest(BaseModel):
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    question_count: int = Field(..., ge=5, le=20)


class QuestionPreview(BaseModel):
    id: int
    content: str
    options: list[str]
    order_num: int


class QuizStatus(BaseModel):
    id: int
    status: str
    progress: Optional[str] = None
    questions: list[QuestionPreview] = []
    generated_count: int = 0
    total_count: int = 0


class QuizReady(BaseModel):
    id: int
    status: str
    difficulty: str
    total: int
    submitted: bool = False
    questions: list[QuestionPreview]


class AnswerSubmit(BaseModel):
    question_id: int
    selected_index: int


class SubmitRequest(BaseModel):
    answers: list[AnswerSubmit]


class AnswerResult(BaseModel):
    question_id: int
    content: str
    options: list[str]
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str


class ReviewOut(BaseModel):
    quiz_id: int
    score: int
    total: int
    answers: list[AnswerResult]


class QuizHistoryItem(BaseModel):
    id: int
    document_title: str
    difficulty: str
    total: int
    score: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
