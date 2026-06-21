from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"


class GroupType(str, Enum):
    chapter = "chapter"
    section = "section"
    part = "part"
    topic = "topic"
    none = "none"


class ExtractionMethod(str, Enum):
    rule_based = "rule_based"
    llm = "llm"


# --- Request bodies ---

class StartAttemptRequest(BaseModel):
    group_id: str


class ResponseItem(BaseModel):
    question_id: str
    selected: str  # "a" | "b" | "c" | "d"


class SubmitAttemptRequest(BaseModel):
    responses: list[ResponseItem]


# --- Response models ---

class DocumentOut(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime
    status: DocumentStatus
    total_questions: int = 0
    failed_questions: int = 0


class GroupOut(BaseModel):
    id: str
    document_id: str
    display_name: str
    group_type: GroupType
    order_index: int
    question_count: int


class OptionsOut(BaseModel):
    a: str
    b: str
    c: str
    d: str


class QuestionOut(BaseModel):
    id: str
    group_id: str
    order_index: int
    question_text: str
    options: OptionsOut
    extraction_method: ExtractionMethod


class BreakdownItem(BaseModel):
    question_id: str
    question_text: str
    options: OptionsOut
    selected: str
    correct_answer: str
    is_correct: bool
    explanation: Optional[str]


class AttemptOut(BaseModel):
    id: str
    group_id: str
    score: int
    total: int
    breakdown: list[BreakdownItem]
