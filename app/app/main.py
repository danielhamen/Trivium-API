from contextlib import asynccontextmanager
from typing import Annotated
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import Difficulty, Question
from app.repository import DataRepository
from app.schemas import (
    AdminAnalyticsOut,
    CategoryCreateIn,
    CategoryOut,
    CategoryUpdateIn,
    QuestionOut,
    QuestionPublicOut,
    QuestionUpdateIn,
    QuestionUpsertIn,
    ReportCreateIn,
    ReportOut,
    ReportStatusUpdateIn,
    StatsOut,
)

repo = DataRepository()


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo.fetch()
    yield


app = FastAPI(
    title="Trivia API",
    version="1.0.0",
    description="Trivia question and category API",
    lifespan=lifespan,
)
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/admin/static", StaticFiles(directory=static_dir), name="admin-static")


def get_repo() -> DataRepository:
    return repo


def parse_difficulties(
    difficulties: list[str] | None,
) -> list[Difficulty] | None:
    if not difficulties:
        return None

    parsed: list[Difficulty] = []
    for value in difficulties:
        try:
            parsed.append(Difficulty.parse(value))
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Invalid difficulty: {value}"
            ) from exc
    return parsed


def to_public_question(question: Question) -> QuestionPublicOut:
    return QuestionPublicOut.model_validate(question, from_attributes=True)


@app.get("/")
def root():
    return {"message": "Trivia API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats", response_model=StatsOut)
def get_stats(repository: Annotated[DataRepository, Depends(get_repo)]):
    return StatsOut(
        question_count=repository.count_questions(),
        category_count=len(repository.get_all_categories()),
    )


@app.get("/categories", response_model=list[CategoryOut])
def get_categories(
    flat: bool = Query(False),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    categories = repository.get_all_categories() if flat else repository.categories
    return categories


@app.get("/categories/search", response_model=list[CategoryOut])
def search_categories(
    q: str = Query(..., min_length=1),
    exact: bool = Query(False),
    case_sensitive: bool = Query(False),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    return repository.find_categories_by_title(
        q,
        exact=exact,
        case_sensitive=case_sensitive,
    )


@app.get("/categories/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: str,
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    try:
        return repository.get_category_by_id(category_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/questions", response_model=list[QuestionPublicOut])
def get_questions(
    category_ids: list[str] | None = Query(None),
    difficulties: list[str] | None = Query(None),
    text: str | None = Query(None),
    match_all_categories: bool = Query(False),
    include_category_descendants: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    parsed_difficulties = parse_difficulties(difficulties)

    try:
        questions = repository.filter_questions(
            category_ids=category_ids,
            difficulties=parsed_difficulties,
            text=text,
            match_all_categories=match_all_categories,
            include_category_descendants=include_category_descendants,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    paginated = questions[offset : offset + limit]
    return [to_public_question(q) for q in paginated]


@app.get("/questions/all", response_model=list[QuestionOut])
def get_all_questions_with_answers(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    return repository.get_all_questions()[offset : offset + limit]


@app.get("/questions/search", response_model=list[QuestionPublicOut])
def search_questions(
    q: str = Query(..., min_length=1),
    include_explanations: bool = Query(True),
    include_answers: bool = Query(False),
    case_sensitive: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    questions = repository.search_questions(
        q,
        case_sensitive=case_sensitive,
        include_explanations=include_explanations,
        include_answers=include_answers,
    )
    paginated = questions[offset : offset + limit]
    return [to_public_question(q) for q in paginated]


@app.get("/questions/random/one", response_model=QuestionPublicOut)
def get_random_question(
    category_ids: list[str] | None = Query(None),
    difficulties: list[str] | None = Query(None),
    text: str | None = Query(None),
    match_all_categories: bool = Query(False),
    include_category_descendants: bool = Query(False),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    parsed_difficulties = parse_difficulties(difficulties)

    try:
        question = repository.get_random_filtered_question(
            category_ids=category_ids,
            difficulties=parsed_difficulties,
            text=text,
            match_all_categories=match_all_categories,
            include_category_descendants=include_category_descendants,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return to_public_question(question)


@app.get("/questions/random/many", response_model=list[QuestionPublicOut])
def get_random_questions(
    count: int = Query(10, ge=1, le=100),
    category_ids: list[str] | None = Query(None),
    difficulties: list[str] | None = Query(None),
    text: str | None = Query(None),
    match_all_categories: bool = Query(False),
    include_category_descendants: bool = Query(False),
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    parsed_difficulties = parse_difficulties(difficulties)

    try:
        questions = repository.filter_questions(
            category_ids=category_ids,
            difficulties=parsed_difficulties,
            text=text,
            match_all_categories=match_all_categories,
            include_category_descendants=include_category_descendants,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not questions:
        raise HTTPException(
            status_code=404, detail="no questions matched the given filters"
        )

    if count > len(questions):
        count = len(questions)

    import random

    chosen = random.sample(questions, count)
    return [to_public_question(q) for q in chosen]


@app.get("/questions/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: str,
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    question = repository.try_get_question_by_id(question_id)
    if question is None:
        raise HTTPException(
            status_code=404, detail=f"question not found: {question_id}"
        )
    return question


@app.get("/questions/{question_id}/public", response_model=QuestionPublicOut)
def get_public_question(
    question_id: str,
    repository: Annotated[DataRepository, Depends(get_repo)] = None,
):
    question = repository.try_get_question_by_id(question_id)
    if question is None:
        raise HTTPException(
            status_code=404, detail=f"question not found: {question_id}"
        )
    return to_public_question(question)


@app.get("/admin", response_class=FileResponse)
def admin_dashboard():
    return FileResponse(static_dir / "admin.html")


@app.get("/admin/api/questions", response_model=list[QuestionOut])
def admin_list_questions(
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    return repository.get_all_questions()


@app.post("/admin/api/questions", response_model=QuestionOut, status_code=201)
def admin_create_question(
    payload: QuestionUpsertIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        return repository.create_question(
            id=payload.id,
            question=payload.question,
            category_ids=payload.category_ids,
            difficulty=payload.difficulty,
            correct_answer=payload.correct_answer,
            options=[option.model_dump() for option in payload.options],
            hints=payload.hints,
            explanation=payload.explanation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/admin/api/questions/{question_id}", response_model=QuestionOut)
def admin_update_question(
    question_id: str,
    payload: QuestionUpdateIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        return repository.update_question(
            question_id=question_id,
            question=payload.question,
            category_ids=payload.category_ids,
            difficulty=payload.difficulty,
            correct_answer=payload.correct_answer,
            options=[option.model_dump() for option in payload.options],
            hints=payload.hints,
            explanation=payload.explanation,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/admin/api/questions/{question_id}", status_code=204)
def admin_delete_question(
    question_id: str,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        repository.delete_question(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/admin/api/categories", response_model=list[CategoryOut])
def admin_list_categories(
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    return repository.categories


@app.post("/admin/api/categories", response_model=CategoryOut, status_code=201)
def admin_create_category(
    payload: CategoryCreateIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        return repository.create_category(
            id=payload.id,
            title=payload.title,
            description=payload.description,
            parent_id=payload.parent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/admin/api/categories/{category_id}", response_model=CategoryOut)
def admin_update_category(
    category_id: str,
    payload: CategoryUpdateIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        return repository.update_category(
            category_id, title=payload.title, description=payload.description
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/admin/api/categories/{category_id}", status_code=204)
def admin_delete_category(
    category_id: str,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        repository.delete_category(category_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/questions/{question_id}/report", response_model=ReportOut, status_code=201)
def report_question(
    question_id: str,
    payload: ReportCreateIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    try:
        return repository.create_report(
            question_id=question_id, reason=payload.reason, notes=payload.notes
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/admin/api/reports", response_model=list[ReportOut])
def admin_list_reports(
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    return repository.list_reports()


@app.put("/admin/api/reports/{report_id}", response_model=ReportOut)
def admin_update_report(
    report_id: str,
    payload: ReportStatusUpdateIn,
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    if payload.status not in {"open", "resolved", "ignored"}:
        raise HTTPException(status_code=400, detail="invalid status")
    try:
        return repository.update_report_status(report_id=report_id, status=payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/admin/api/analytics", response_model=AdminAnalyticsOut)
def admin_analytics(
    repository: Annotated[DataRepository, Depends(get_repo)],
):
    questions = repository.get_all_questions()
    reports = repository.list_reports()
    categories = repository.get_all_categories()
    questions_per_category: dict[str, int] = {c.title: 0 for c in categories}
    for question in questions:
        for category in question.categories:
            questions_per_category[category.title] = (
                questions_per_category.get(category.title, 0) + 1
            )
    by_difficulty = {"easy": 0, "medium": 0, "hard": 0}
    for question in questions:
        by_difficulty[question.difficulty.value] += 1
    return AdminAnalyticsOut(
        total_questions=len(questions),
        total_categories=len(categories),
        active_questions=sum(1 for q in questions if q.is_active),
        inactive_questions=sum(1 for q in questions if not q.is_active),
        open_reports=sum(1 for r in reports if r["status"] == "open"),
        resolved_reports=sum(1 for r in reports if r["status"] == "resolved"),
        questions_by_difficulty=by_difficulty,
        questions_per_category=questions_per_category,
    )
