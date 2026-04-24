def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_stats(client):
    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert "question_count" in body
    assert "category_count" in body
    assert body["question_count"] >= 0
    assert body["category_count"] >= 0


def test_get_categories(client):
    response = client.get("/categories")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_get_flat_categories(client):
    response = client.get("/categories?flat=true")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0


def test_get_category_by_id(client, repository):
    category = repository.get_all_categories()[0]
    response = client.get(f"/categories/{category.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == category.id


def test_get_missing_category_returns_404(client):
    response = client.get("/categories/does-not-exist")
    assert response.status_code == 404


def test_search_categories(client, repository):
    category = repository.get_all_categories()[0]
    query = category.title[:3]
    response = client.get("/categories/search", params={"q": query})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_get_questions(client):
    response = client.get("/questions")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)

    if body:
        question = body[0]
        assert "id" in question
        assert "question" in question
        assert "correct_answer" not in question
        assert "topic" in question
        assert isinstance(question["categories"], list)
        if question["categories"]:
            assert "children" not in question["categories"][0]


def test_get_all_questions_with_answers(client):
    response = client.get("/questions/all")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)

    if body:
        question = body[0]
        assert "correct_answer" in question
        assert "topic" in question
        assert isinstance(question["categories"], list)
        if question["categories"]:
            assert "children" not in question["categories"][0]


def test_get_question_by_id(client, repository):
    question = repository.questions[0]
    response = client.get(f"/questions/{question.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == question.id
    assert "correct_answer" in body


def test_get_public_question_by_id(client, repository):
    question = repository.questions[0]
    response = client.get(f"/questions/{question.id}/public")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == question.id
    assert "correct_answer" not in body


def test_get_missing_question_returns_404(client):
    response = client.get("/questions/does-not-exist")
    assert response.status_code == 404


def test_filter_questions_by_text(client, repository):
    question = repository.questions[0]
    token = question.question.split()[0]
    response = client.get("/questions", params={"text": token})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_filter_questions_by_difficulty(client):
    response = client.get("/questions", params=[("difficulties", "easy")])
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)

    for question in body:
        assert question["difficulty"] == "easy"


def test_filter_questions_by_invalid_difficulty_returns_400(client):
    response = client.get("/questions", params=[("difficulties", "impossible")])
    assert response.status_code == 400


def test_random_one(client):
    response = client.get("/questions/random/one")
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert "correct_answer" not in body


def test_random_many(client):
    response = client.get("/questions/random/many", params={"count": 3})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) <= 3


def test_search_questions(client, repository):
    question = repository.questions[0]
    token = question.question.split()[0]
    response = client.get("/questions/search", params={"q": token})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_admin_dashboard_page(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Trivia Admin Dashboard" in response.text


def test_create_report_and_resolve(client, repository):
    question = repository.questions[0]
    create = client.post(
        f"/questions/{question.id}/report",
        json={"reason": "wrong answer", "notes": "looks incorrect"},
    )
    assert create.status_code == 201
    report = create.json()
    assert report["question_id"] == question.id
    report_id = report["id"]

    update = client.put(f"/admin/api/reports/{report_id}", json={"status": "resolved"})
    assert update.status_code == 200
    assert update.json()["status"] == "resolved"


def test_admin_create_and_delete_question(client):
    categories_response = client.get("/categories", params={"flat": True})
    category_id = categories_response.json()[0]["id"]
    payload = {
        "id": "admin-test-question",
        "question": "Admin test question?",
        "topic_id": category_id.split(".")[0],
        "category_ids": [category_id],
        "difficulty": "easy",
        "correct_answer": "yes",
        "options": [],
        "hints": ["hint"],
        "explanation": "explanation",
        "is_active": True,
    }
    create = client.post("/admin/api/questions", json=payload)
    assert create.status_code == 201
    assert create.json()["id"] == payload["id"]

    delete = client.delete(f"/admin/api/questions/{payload['id']}")
    assert delete.status_code == 204
