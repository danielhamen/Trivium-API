import json
import random
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

from app.models import Category, Difficulty, Hint, Option, Question


@dataclass
class DataRepository:
    categories: list[Category] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    reports: list[dict[str, Any]] = field(default_factory=list)

    def fetch(self) -> "DataRepository":
        data_dir = Path(__file__).resolve().parent.parent / "data"
        category_path = data_dir / "categories.json"
        question_path = data_dir / "questions.json"

        with category_path.open("r", encoding="utf-8") as file:
            category_obj = json.load(file)

        with question_path.open("r", encoding="utf-8") as file:
            question_obj = json.load(file)

        if not isinstance(category_obj, list):
            raise TypeError("categories.json must contain a list")
        if not isinstance(question_obj, list):
            raise TypeError("questions.json must contain a list")

        self.categories = [self._parse_category(x) for x in category_obj]
        self.questions = [self._parse_question(x) for x in question_obj]
        return self

    def _parse_category(self, obj: Any) -> Category:
        if not isinstance(obj, dict):
            raise TypeError("category must be an object")
        if "id" not in obj:
            raise ValueError("category missing `id`")
        if "title" not in obj:
            raise ValueError("category missing `title`")

        id_ = obj["id"]
        title = obj["title"]
        description = obj.get("description")
        children_raw = obj.get("children", [])

        if not isinstance(id_, str):
            raise TypeError("category id must be a string")
        if not isinstance(title, str):
            raise TypeError("category title must be a string")
        if description is not None and not isinstance(description, str):
            raise TypeError("category description must be a string or null")
        if not isinstance(children_raw, list):
            raise TypeError("category children must be a list")

        children = [self._parse_category(x) for x in children_raw]

        return Category(
            id=id_,
            title=title,
            description=description,
            children=children,
        )

    def _parse_question(self, obj: Any) -> Question:
        if not isinstance(obj, dict):
            raise TypeError("question must be an object")

        required = ["id", "categories", "question", "difficulty", "correct_answer"]
        for key in required:
            if key not in obj:
                raise ValueError(f"question missing `{key}`")

        id_ = obj["id"]
        question_text = obj["question"]
        difficulty = Difficulty.parse(obj["difficulty"])
        correct_answer = obj["correct_answer"]

        if not isinstance(id_, str):
            raise TypeError("question id must be a string")
        if not isinstance(question_text, str):
            raise TypeError("question text must be a string")
        if not isinstance(correct_answer, str):
            raise TypeError("correct_answer must be a string")

        category_ids = obj["categories"]
        if not isinstance(category_ids, list) or not all(
            isinstance(x, str) for x in category_ids
        ):
            raise TypeError("question categories must be a list of strings")
        categories = [self.get_category_by_id(x) for x in category_ids]

        explanation = obj.get("explanation")
        if explanation is not None and not isinstance(explanation, str):
            raise TypeError("explanation must be a string or null")

        options_raw = obj.get("options", [])
        if not isinstance(options_raw, list):
            raise TypeError("options must be a list")
        options = [self._parse_option(x) for x in options_raw]
        if len(options) > 8:
            raise ValueError("MAX 8 options allowed")

        hints_raw = obj.get("hints", [])
        if not isinstance(hints_raw, list) or not all(
            isinstance(x, str) for x in hints_raw
        ):
            raise TypeError("hints must be a list of strings")
        hints = [self._parse_hint(x) for x in hints_raw]
        if len(hints) > 3:
            raise ValueError("MAX 3 hints allowed")

        created_on_raw = obj.get("created_on")
        created_on: Optional[date] = None
        if created_on_raw is not None:
            if not isinstance(created_on_raw, str):
                raise TypeError("created_on must be an ISO date string or null")
            try:
                created_on = date.fromisoformat(created_on_raw)
            except ValueError as exc:
                raise ValueError("created_on must be in ISO format YYYY-MM-DD") from exc

        created_by = obj.get("created_by")
        if created_by is not None and not isinstance(created_by, str):
            raise TypeError("created_by must be a string or null")

        shuffle_options = obj.get("shuffle_options", True)
        if not isinstance(shuffle_options, bool):
            raise TypeError("shuffle_options must be a bool")

        sources_raw = obj.get("sources", [])
        if not isinstance(sources_raw, list) or not all(
            isinstance(x, str) for x in sources_raw
        ):
            raise TypeError("sources must be a list of strings")

        updated_at_raw = obj.get("updated_at")
        updated_at: Optional[datetime] = None
        if updated_at_raw is not None:
            if not isinstance(updated_at_raw, str):
                raise TypeError("updated_at must be an ISO datetime string or null")
            try:
                updated_at = datetime.fromisoformat(updated_at_raw)
            except ValueError as exc:
                raise ValueError(
                    "updated_at must be in ISO 8601 datetime format"
                ) from exc

        is_active = obj.get("is_active", True)
        if not isinstance(is_active, bool):
            raise TypeError("is_active must be a bool")

        allow_multiple_answers = obj.get("allow_multiple_answers", False)
        if not isinstance(allow_multiple_answers, bool):
            raise TypeError("allow_multiple_answers must be a bool")

        return Question(
            id=id_,
            question=question_text,
            categories=categories,
            difficulty=difficulty,
            correct_answer=correct_answer,
            options=options,
            hints=hints,
            explanation=explanation,
            created_on=created_on,
            created_by=created_by,
            shuffle_options=shuffle_options,
            sources=sources_raw,
            updated_at=updated_at,
            is_active=is_active,
            allow_multiple_answers=allow_multiple_answers,
        )

    def _parse_hint(self, obj: Any) -> Hint:
        if not isinstance(obj, str):
            raise TypeError("hint must be a string")
        return Hint(text=obj)

    def _parse_option(self, obj: Any) -> Option:
        if not isinstance(obj, dict):
            raise TypeError("option must be an object")
        if "text" not in obj or not isinstance(obj["text"], str):
            raise TypeError("option text must be a string")
        if "is_correct" not in obj or not isinstance(obj["is_correct"], bool):
            raise TypeError("option is_correct must be a bool")

        option_explanation = obj.get("explanation")
        if option_explanation is not None and not isinstance(option_explanation, bool):
            raise TypeError("option explanation must be a bool or null")

        return Option(
            text=obj["text"],
            is_correct=obj["is_correct"],
            explanation=option_explanation,
        )

    def get_all_categories(self) -> list[Category]:
        return self._flatten_categories(self.categories)

    def _flatten_categories(self, categories: list[Category]) -> list[Category]:
        result: list[Category] = []
        for category in categories:
            result.append(category)
            result.extend(self._flatten_categories(category.children))
        return result

    def get_category_by_id(self, id: str) -> Category:
        found = self._find_category_recursive(self.categories, id)
        if found is None:
            raise ValueError(f"category not found: {id}")
        return found

    def try_get_category_by_id(self, id: str) -> Optional[Category]:
        return self._find_category_recursive(self.categories, id)

    def find_categories_by_title(
        self,
        title: str,
        *,
        exact: bool = False,
        case_sensitive: bool = False,
    ) -> list[Category]:
        categories = self.get_all_categories()

        if not case_sensitive:
            needle = title.lower()
            if exact:
                return [c for c in categories if c.title.lower() == needle]
            return [c for c in categories if needle in c.title.lower()]

        if exact:
            return [c for c in categories if c.title == title]
        return [c for c in categories if title in c.title]

    def _find_category_recursive(
        self,
        categories: list[Category],
        id: str,
    ) -> Optional[Category]:
        for category in categories:
            if category.id == id:
                return category
            found = self._find_category_recursive(category.children, id)
            if found is not None:
                return found
        return None

    def get_all_questions(self) -> list[Question]:
        return list(self.questions)

    def count_questions(self) -> int:
        return len(self.questions)

    def get_question_by_id(self, id: str) -> Question:
        for question in self.questions:
            if question.id == id:
                return question
        raise ValueError(f"question not found: {id}")

    def try_get_question_by_id(self, id: str) -> Optional[Question]:
        for question in self.questions:
            if question.id == id:
                return question
        return None

    def search_questions(
        self,
        text: str,
        *,
        case_sensitive: bool = False,
        include_explanations: bool = True,
        include_answers: bool = False,
    ) -> list[Question]:
        results: list[Question] = []
        needle = text if case_sensitive else text.lower()

        for q in self.questions:
            haystacks = [q.question]
            if include_explanations and q.explanation:
                haystacks.append(q.explanation)
            if include_answers:
                haystacks.append(q.correct_answer)

            if not case_sensitive:
                haystacks = [h.lower() for h in haystacks]

            if any(needle in h for h in haystacks):
                results.append(q)

        return results

    def get_questions_by_difficulty(self, difficulty: Difficulty) -> list[Question]:
        return [q for q in self.questions if q.difficulty == difficulty]

    def get_questions_by_category_id(
        self,
        category_id: str,
        *,
        include_descendants: bool = False,
    ) -> list[Question]:
        if include_descendants:
            category = self.get_category_by_id(category_id)
            valid_ids = {c.id for c in self._flatten_categories([category])}
            return [
                q
                for q in self.questions
                if any(c.id in valid_ids for c in q.categories)
            ]

        return [
            q for q in self.questions if any(c.id == category_id for c in q.categories)
        ]

    def filter_questions(
        self,
        *,
        category_ids: Optional[list[str]] = None,
        difficulties: Optional[list[Difficulty]] = None,
        text: Optional[str] = None,
        match_all_categories: bool = False,
        include_category_descendants: bool = False,
    ) -> list[Question]:
        results = list(self.questions)

        if category_ids:
            valid_category_ids: set[str] = set()

            if include_category_descendants:
                for category_id in category_ids:
                    category = self.get_category_by_id(category_id)
                    valid_category_ids.update(
                        c.id for c in self._flatten_categories([category])
                    )
            else:
                valid_category_ids = set(category_ids)

            if match_all_categories:
                results = [
                    q
                    for q in results
                    if valid_category_ids.issubset({c.id for c in q.categories})
                ]
            else:
                results = [
                    q
                    for q in results
                    if any(c.id in valid_category_ids for c in q.categories)
                ]

        if difficulties:
            difficulty_set = set(difficulties)
            results = [q for q in results if q.difficulty in difficulty_set]

        if text:
            needle = text.lower()
            results = [q for q in results if needle in q.question.lower()]

        return results

    def get_random_question(self) -> Question:
        if not self.questions:
            raise ValueError("no questions available")
        return random.choice(self.questions)

    def get_random_questions(self, count: int) -> list[Question]:
        if count < 0:
            raise ValueError("count must be >= 0")
        if count > len(self.questions):
            raise ValueError("count cannot exceed number of questions")
        return random.sample(self.questions, count)

    def get_random_filtered_question(
        self,
        *,
        category_ids: Optional[list[str]] = None,
        difficulties: Optional[list[Difficulty]] = None,
        text: Optional[str] = None,
        match_all_categories: bool = False,
        include_category_descendants: bool = False,
    ) -> Question:
        questions = self.filter_questions(
            category_ids=category_ids,
            difficulties=difficulties,
            text=text,
            match_all_categories=match_all_categories,
            include_category_descendants=include_category_descendants,
        )
        if not questions:
            raise ValueError("no questions matched the given filters")
        return random.choice(questions)

    def create_category(
        self,
        *,
        id: str,
        title: str,
        description: str | None = None,
        parent_id: str | None = None,
    ) -> Category:
        if self.try_get_category_by_id(id):
            raise ValueError(f"category already exists: {id}")
        category = Category(id=id, title=title, description=description)
        if parent_id is None:
            self.categories.append(category)
            return category

        parent = self.try_get_category_by_id(parent_id)
        if parent is None:
            raise ValueError(f"parent category not found: {parent_id}")
        parent.children.append(category)
        return category

    def update_category(
        self,
        category_id: str,
        *,
        title: str,
        description: str | None = None,
    ) -> Category:
        category = self.try_get_category_by_id(category_id)
        if category is None:
            raise ValueError(f"category not found: {category_id}")
        category.title = title
        category.description = description
        return category

    def delete_category(self, category_id: str) -> None:
        category = self.try_get_category_by_id(category_id)
        if category is None:
            raise ValueError(f"category not found: {category_id}")
        descendants = self._flatten_categories([category])
        deleted_ids = {c.id for c in descendants}
        self.categories = self._remove_category_recursive(self.categories, category_id)
        self.questions = [
            q
            for q in self.questions
            if not any(c.id in deleted_ids for c in q.categories)
        ]

    def _remove_category_recursive(
        self, categories: list[Category], category_id: str
    ) -> list[Category]:
        result: list[Category] = []
        for category in categories:
            if category.id == category_id:
                continue
            category.children = self._remove_category_recursive(
                category.children, category_id
            )
            result.append(category)
        return result

    def create_question(
        self,
        *,
        id: str,
        question: str,
        category_ids: list[str],
        difficulty: Difficulty,
        correct_answer: str,
        options: list[dict[str, Any]] | None = None,
        hints: list[str] | None = None,
        explanation: str | None = None,
    ) -> Question:
        if self.try_get_question_by_id(id):
            raise ValueError(f"question already exists: {id}")
        categories = [self.get_category_by_id(category_id) for category_id in category_ids]
        parsed_options = [self._parse_option(option) for option in (options or [])]
        parsed_hints = [self._parse_hint(hint) for hint in (hints or [])]
        question_model = Question(
            id=id,
            question=question,
            categories=categories,
            difficulty=difficulty,
            correct_answer=correct_answer,
            options=parsed_options,
            hints=parsed_hints,
            explanation=explanation,
            created_on=date.today(),
            updated_at=datetime.utcnow(),
        )
        self.questions.append(question_model)
        return question_model

    def update_question(
        self,
        question_id: str,
        *,
        question: str,
        category_ids: list[str],
        difficulty: Difficulty,
        correct_answer: str,
        options: list[dict[str, Any]] | None = None,
        hints: list[str] | None = None,
        explanation: str | None = None,
        is_active: bool = True,
    ) -> Question:
        found = self.try_get_question_by_id(question_id)
        if found is None:
            raise ValueError(f"question not found: {question_id}")
        found.question = question
        found.categories = [self.get_category_by_id(category_id) for category_id in category_ids]
        found.difficulty = difficulty
        found.correct_answer = correct_answer
        found.options = [self._parse_option(option) for option in (options or [])]
        found.hints = [self._parse_hint(hint) for hint in (hints or [])]
        found.explanation = explanation
        found.is_active = is_active
        found.updated_at = datetime.utcnow()
        return found

    def delete_question(self, question_id: str) -> None:
        before = len(self.questions)
        self.questions = [q for q in self.questions if q.id != question_id]
        if len(self.questions) == before:
            raise ValueError(f"question not found: {question_id}")
        self.reports = [report for report in self.reports if report["question_id"] != question_id]

    def create_report(self, question_id: str, reason: str, notes: str | None = None) -> dict[str, Any]:
        question = self.try_get_question_by_id(question_id)
        if question is None:
            raise ValueError(f"question not found: {question_id}")
        report = {
            "id": str(uuid4()),
            "question_id": question_id,
            "question_text": question.question,
            "reason": reason,
            "notes": notes,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
        }
        self.reports.append(report)
        return report

    def list_reports(self) -> list[dict[str, Any]]:
        return list(self.reports)

    def update_report_status(self, report_id: str, status: str) -> dict[str, Any]:
        for report in self.reports:
            if report["id"] == report_id:
                report["status"] = status
                report["resolved_at"] = (
                    datetime.utcnow().isoformat() if status == "resolved" else None
                )
                return report
        raise ValueError(f"report not found: {report_id}")
