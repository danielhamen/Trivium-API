from collections import Counter


def flatten_category_dicts(categories: list[dict]) -> list[dict]:
    result = []

    def walk(nodes: list[dict]):
        for node in nodes:
            result.append(node)
            children = node.get("children", [])
            if children:
                walk(children)

    walk(categories)
    return result


def test_categories_file_is_list(categories_json):
    assert isinstance(categories_json, list)


def test_questions_file_is_list(questions_json):
    assert isinstance(questions_json, list)


def test_all_categories_have_required_fields(categories_json):
    all_categories = flatten_category_dicts(categories_json)

    for category in all_categories:
        assert "id" in category
        assert "title" in category
        assert isinstance(category["id"], str)
        assert category["id"].strip() != ""
        assert isinstance(category["title"], str)
        assert category["title"].strip() != ""


def test_category_ids_are_unique(categories_json):
    all_categories = flatten_category_dicts(categories_json)
    ids = [c["id"] for c in all_categories]
    counts = Counter(ids)
    duplicates = [k for k, v in counts.items() if v > 1]
    assert duplicates == []


def test_question_ids_are_unique(questions_json):
    ids = [q["id"] for q in questions_json]
    counts = Counter(ids)
    duplicates = [k for k, v in counts.items() if v > 1]
    assert duplicates == []


def test_questions_have_required_fields(questions_json):
    required = {"id", "topic", "categories", "question", "difficulty", "correct_answer"}

    for q in questions_json:
        assert required.issubset(q.keys())
        assert isinstance(q["id"], str)
        assert q["id"].strip() != ""
        assert isinstance(q["question"], str)
        assert q["question"].strip() != ""
        assert isinstance(q["topic"], str)
        assert q["topic"].strip() != ""
        assert isinstance(q["categories"], list)
        assert isinstance(q["correct_answer"], str)
        assert q["correct_answer"].strip() != ""


def test_question_difficulties_are_valid(questions_json):
    valid = {"easy", "medium", "hard"}

    for q in questions_json:
        assert q["difficulty"] in valid


def test_question_categories_are_string_ids(questions_json):
    for q in questions_json:
        assert all(isinstance(x, str) for x in q["categories"])


def test_question_option_limit(questions_json):
    for q in questions_json:
        if "options" in q:
            assert isinstance(q["options"], list)
            assert len(q["options"]) <= 8


def test_question_hint_limit(questions_json):
    for q in questions_json:
        if "hints" in q:
            assert isinstance(q["hints"], list)
            assert len(q["hints"]) <= 3


def test_question_options_shape(questions_json):
    for q in questions_json:
        for option in q.get("options", []):
            assert isinstance(option, dict)
            assert "text" in option
            assert "is_correct" in option
            assert isinstance(option["text"], str)
            assert isinstance(option["is_correct"], bool)


def test_all_question_category_ids_exist(categories_json, questions_json):
    all_categories = flatten_category_dicts(categories_json)
    valid_ids = {c["id"] for c in all_categories}

    missing_refs = []
    for q in questions_json:
        for category_id in q["categories"]:
            if category_id not in valid_ids:
                missing_refs.append((q["id"], category_id))

    assert missing_refs == []


def test_multiple_choice_questions_have_single_correct_option(questions_json):
    for q in questions_json:
        options = q.get("options", [])
        if options:
            correct_count = sum(1 for opt in options if opt["is_correct"])
            assert correct_count == 1, (
                f"Question {q['id']} has {correct_count} correct options"
            )


def test_correct_answer_matches_option_text_for_multiple_choice(questions_json):
    for q in questions_json:
        options = q.get("options", [])
        if options:
            option_texts = [opt["text"] for opt in options]
            assert q["correct_answer"] in option_texts, (
                f"Question {q['id']} correct_answer not found in options"
            )
