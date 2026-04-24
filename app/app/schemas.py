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


CategoryOut.model_rebuild()
