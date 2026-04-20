from app.models import Difficulty


def test_repository_fetches_data(repository):
    assert len(repository.categories) > 0
    assert len(repository.questions) > 0


def test_repository_can_flatten_categories(repository):
    flat = repository.get_all_categories()
    assert len(flat) > 0
    assert all(hasattr(c, "id") for c in flat)


def test_repository_can_get_category_by_id(repository):
    first = repository.get_all_categories()[0]
    found = repository.get_category_by_id(first.id)
    assert found.id == first.id


def test_repository_can_get_question_by_id(repository):
    first = repository.questions[0]
    found = repository.get_question_by_id(first.id)
    assert found.id == first.id
    assert found.question == first.question


def test_repository_can_filter_by_difficulty(repository):
    easy_questions = repository.get_questions_by_difficulty(Difficulty.EASY)
    assert all(q.difficulty == Difficulty.EASY for q in easy_questions)


def test_repository_can_search_questions(repository):
    first = repository.questions[0]
    token = first.question.split()[0]
    results = repository.search_questions(token)
    assert len(results) >= 1


def test_repository_random_question_is_valid(repository):
    q = repository.get_random_question()
    assert q in repository.questions


def test_repository_random_questions_count(repository):
    count = min(3, len(repository.questions))
    questions = repository.get_random_questions(count)
    assert len(questions) == count
    assert len({q.id for q in questions}) == count


def test_repository_filter_by_category(repository):
    question = repository.questions[0]
    assert len(question.categories) > 0

    category_id = question.categories[0].id
    results = repository.get_questions_by_category_id(category_id)

    assert any(q.id == question.id for q in results)


def test_repository_filter_questions_combined(repository):
    first = repository.questions[0]
    category_ids = [c.id for c in first.categories]
    difficulties = [first.difficulty]

    results = repository.filter_questions(
        category_ids=category_ids,
        difficulties=difficulties,
    )

    assert any(q.id == first.id for q in results)
