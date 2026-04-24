from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import Difficulty


class CategoryOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    children: list["CategoryOut"] = Field(default_factory=list)


class CategoryRefOut(BaseModel):
    id: str
    title: str
    description: str | None = None


class OptionOut(BaseModel):
    text: str
    is_correct: bool
    explanation: bool | None = None


class HintOut(BaseModel):
    text: str


class QuestionOut(BaseModel):
    id: str
    question: str
    categories: list[CategoryRefOut]
    difficulty: Difficulty
    correct_answer: str
    options: list[OptionOut] = Field(default_factory=list)
    hints: list[HintOut] = Field(default_factory=list)
    explanation: str | None = None
    created_on: date | None = None
    created_by: str | None = None
    shuffle_options: bool = True
    sources: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    is_active: bool = True
    allow_multiple_answers: bool = False


class QuestionPublicOut(BaseModel):
    id: str
    question: str
    categories: list[CategoryRefOut]
    difficulty: Difficulty
    options: list[OptionOut] = Field(default_factory=list)
    hints: list[HintOut] = Field(default_factory=list)
    explanation: str | None = None
    created_on: date | None = None
    created_by: str | None = None
    shuffle_options: bool = True
    sources: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    is_active: bool = True
    allow_multiple_answers: bool = False


class StatsOut(BaseModel):
    question_count: int
    category_count: int


class CategoryCreateIn(BaseModel):
    id: str
    title: str
    description: str | None = None
    parent_id: str | None = None


class CategoryUpdateIn(BaseModel):
    title: str
    description: str | None = None


class OptionIn(BaseModel):
    text: str
    is_correct: bool
    explanation: bool | None = None


class QuestionUpsertIn(BaseModel):
    id: str
    question: str
    category_ids: list[str]
    difficulty: Difficulty
    correct_answer: str
    options: list[OptionIn] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    explanation: str | None = None
    is_active: bool = True


class QuestionUpdateIn(BaseModel):
    question: str
    category_ids: list[str]
    difficulty: Difficulty
    correct_answer: str
    options: list[OptionIn] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    explanation: str | None = None
    is_active: bool = True


class ReportCreateIn(BaseModel):
    reason: str
    notes: str | None = None


class ReportOut(BaseModel):
    id: str
    question_id: str
    question_text: str
    reason: str
    notes: str | None = None
    status: str
    created_at: datetime
    resolved_at: datetime | None = None


class ReportStatusUpdateIn(BaseModel):
    status: str


class AdminAnalyticsOut(BaseModel):
    total_questions: int
    total_categories: int
    active_questions: int
    inactive_questions: int
    open_reports: int
    resolved_reports: int
    questions_by_difficulty: dict[str, int]
    questions_per_category: dict[str, int]


CategoryOut.model_rebuild()
