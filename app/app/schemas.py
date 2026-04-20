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


class QuestionPublicOut(BaseModel):
    id: str
    question: str
    categories: list[CategoryRefOut]
    difficulty: Difficulty
    options: list[OptionOut] = Field(default_factory=list)
    hints: list[HintOut] = Field(default_factory=list)
    explanation: str | None = None


class StatsOut(BaseModel):
    question_count: int
    category_count: int


CategoryOut.model_rebuild()
