from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @staticmethod
    def parse(x: Any) -> "Difficulty":
        if not isinstance(x, str):
            raise TypeError("difficulty must be a string")
        try:
            return Difficulty(x)
        except ValueError:
            raise ValueError(f"invalid difficulty: {x}")


@dataclass
class Category:
    id: str
    title: str
    description: Optional[str] = None
    children: list["Category"] = field(default_factory=list)


@dataclass
class Option:
    text: str
    is_correct: bool
    explanation: Optional[bool] = None


@dataclass
class Hint:
    text: str


@dataclass
class Question:
    id: str
    question: str
    categories: list[Category]
    difficulty: Difficulty
    correct_answer: str
    options: list[Option] = field(default_factory=list)
    hints: list[Hint] = field(default_factory=list)
    explanation: Optional[str] = None
    created_on: Optional[date] = None
    created_by: Optional[str] = None
    shuffle_options: bool = True
    sources: list[str] = field(default_factory=list)
    updated_at: Optional[datetime] = None
    is_active: bool = True
    allow_multiple_answers: bool = False
