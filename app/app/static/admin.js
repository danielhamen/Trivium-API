const topicList = document.getElementById('topic-list');
const categoryList = document.getElementById('category-list');
const questionList = document.getElementById('question-list');
const reportList = document.getElementById('report-list');
const analytics = document.getElementById('analytics');
const analyticsJson = document.getElementById('analytics-json');

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

function makeCategoryTreeByTopic(topics, categories) {
  const rootById = new Map(categories.map((category) => [category.id, category]));
  return topics.map((topic) => ({ ...topic, categories: rootById.get(topic.id)?.children || [] }));
}

function normalizeDate(value) {
  return value && value.trim() ? value.trim() : null;
}

function normalizeDateTimeLocal(value) {
  if (!value || !value.trim()) return null;
  const iso = new Date(value).toISOString();
  return Number.isNaN(Date.parse(iso)) ? null : iso;
}

function buildQuestionPayloadFromRecord(question, overrides = {}) {
  return {
    question: question.question,
    topic_id: question.topic.id,
    category_ids: question.categories.map((c) => c.id),
    difficulty: question.difficulty,
    correct_answer: question.correct_answer,
    options: question.options,
    hints: question.hints.map((h) => h.text),
    explanation: question.explanation,
    created_on: question.created_on,
    created_by: question.created_by,
    shuffle_options: question.shuffle_options,
    sources: question.sources,
    updated_at: question.updated_at,
    is_active: question.is_active,
    allow_multiple_answers: question.allow_multiple_answers,
    ...overrides,
  };
}

function renderCategoryNode(node, list, depth = 0) {
  const li = document.createElement('li');
  li.innerHTML = `<strong>${'— '.repeat(depth)}${node.title}</strong> <span class="muted">(${node.id})</span><br>${node.description || ''}`;

  const actions = document.createElement('div');
  actions.className = 'inline-actions';

  const editButton = document.createElement('button');
  editButton.textContent = 'Edit';
  editButton.onclick = async () => {
    const title = prompt('New category title', node.title);
    if (!title) return;
    const description = prompt('Description', node.description || '') || null;
    await api(`/admin/api/categories/${node.id}`, {
      method: 'PUT',
      body: JSON.stringify({ title, description }),
    });
    await refreshAll();
  };

  const deleteButton = document.createElement('button');
  deleteButton.textContent = 'Delete';
  deleteButton.onclick = async () => {
    if (!confirm(`Delete category ${node.id}?`)) return;
    await api(`/admin/api/categories/${node.id}`, { method: 'DELETE' });
    await refreshAll();
  };

  actions.append(editButton, deleteButton);
  li.append(actions);
  list.append(li);

  for (const child of node.children || []) {
    renderCategoryNode(child, list, depth + 1);
  }
}

async function loadTopicsAndCategories() {
  const [topics, categories] = await Promise.all([api('/admin/api/topics'), api('/admin/api/categories')]);
  const tree = makeCategoryTreeByTopic(topics, categories);

  topicList.innerHTML = '';
  categoryList.innerHTML = '';

  for (const topic of topics) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${topic.title}</strong> <span class="muted">(${topic.id})</span><br>${topic.description || ''}`;

    const actions = document.createElement('div');
    actions.className = 'inline-actions';

    const editButton = document.createElement('button');
    editButton.textContent = 'Edit';
    editButton.onclick = async () => {
      const title = prompt('New topic title', topic.title);
      if (!title) return;
      const description = prompt('Description', topic.description || '') || null;
      await api(`/admin/api/topics/${topic.id}`, {
        method: 'PUT',
        body: JSON.stringify({ title, description }),
      });
      await refreshAll();
    };

    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = async () => {
      if (!confirm(`Delete topic ${topic.id}? This removes nested categories and questions.`)) return;
      await api(`/admin/api/topics/${topic.id}`, { method: 'DELETE' });
      await refreshAll();
    };

    actions.append(editButton, deleteButton);
    li.append(actions);
    topicList.append(li);
  }

  for (const topic of tree) {
    const details = document.createElement('details');
    details.open = true;
    details.innerHTML = `<summary><strong>${topic.title}</strong> <span class="muted">(${topic.id})</span></summary>`;
    const nested = document.createElement('ul');

    for (const category of topic.categories) {
      renderCategoryNode(category, nested, 0);
    }

    details.append(nested);
    categoryList.append(details);
  }
}

async function loadQuestions() {
  const questions = await api('/admin/api/questions');
  questionList.innerHTML = '';

  for (const question of questions) {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>${question.question}</strong>
      <div class="muted">ID: ${question.id} | Topic: ${question.topic.title} | Difficulty: ${question.difficulty}</div>
      <div><strong>Categories:</strong> ${question.categories.map((c) => c.title).join(', ')}</div>
      <div><strong>Correct answer:</strong> ${question.correct_answer}</div>
      <div><strong>Hints:</strong> ${question.hints.map((h) => h.text).join(' | ') || '—'}</div>
      <div><strong>Sources:</strong> ${question.sources.join(', ') || '—'}</div>
      <div><strong>Created:</strong> ${question.created_on || '—'} by ${question.created_by || '—'}</div>
      <div><strong>Updated:</strong> ${question.updated_at || '—'}</div>
      <div><strong>Flags:</strong> active=${question.is_active}, shuffle_options=${question.shuffle_options}, allow_multiple_answers=${question.allow_multiple_answers}</div>
      <details><summary>Options (${question.options.length})</summary><pre>${JSON.stringify(question.options, null, 2)}</pre></details>
      <details><summary>Explanation</summary><div>${question.explanation || '—'}</div></details>
    `;

    const actions = document.createElement('div');
    actions.className = 'inline-actions';

    const toggleButton = document.createElement('button');
    toggleButton.textContent = question.is_active ? 'Deactivate' : 'Activate';
    toggleButton.onclick = async () => {
      await api(`/admin/api/questions/${question.id}`, {
        method: 'PUT',
        body: JSON.stringify(buildQuestionPayloadFromRecord(question, { is_active: !question.is_active })),
      });
      await refreshAll();
    };

    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = async () => {
      if (!confirm(`Delete question ${question.id}?`)) return;
      await api(`/admin/api/questions/${question.id}`, { method: 'DELETE' });
      await refreshAll();
    };

    actions.append(toggleButton, deleteButton);
    li.append(actions);
    questionList.append(li);
  }
}

async function loadReports() {
  const reports = await api('/admin/api/reports');
  reportList.innerHTML = '';

  for (const report of reports) {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>${report.reason}</strong> <span class="muted">(${report.status})</span>
      <div>Question: ${report.question_text}</div>
      <div class="muted">${report.notes || ''}</div>
    `;

    const actions = document.createElement('div');
    actions.className = 'inline-actions';

    for (const status of ['open', 'resolved', 'ignored']) {
      const button = document.createElement('button');
      button.textContent = status;
      button.onclick = async () => {
        await api(`/admin/api/reports/${report.id}`, {
          method: 'PUT',
          body: JSON.stringify({ status }),
        });
        await refreshAll();
      };
      actions.append(button);
    }

    li.append(actions);
    reportList.append(li);
  }
}

async function loadAnalytics() {
  const data = await api('/admin/api/analytics');
  analytics.innerHTML = '';
  for (const [key, value] of Object.entries(data)) {
    if (typeof value === 'object') continue;
    const box = document.createElement('div');
    box.className = 'stat';
    box.innerHTML = `<span class="muted">${key}</span><strong>${value}</strong>`;
    analytics.append(box);
  }

  analyticsJson.textContent = JSON.stringify(
    {
      questions_by_difficulty: data.questions_by_difficulty,
      questions_per_category: data.questions_per_category,
    },
    null,
    2,
  );
}

async function refreshAll() {
  try {
    await Promise.all([loadTopicsAndCategories(), loadQuestions(), loadReports(), loadAnalytics()]);
  } catch (error) {
    alert(error.message);
  }
}

document.getElementById('topic-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;

  const payload = {
    id: form.id.value.trim(),
    title: form.title.value.trim(),
    description: form.description.value.trim() || null,
  };

  try {
    await api('/admin/api/topics', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    await refreshAll();
  } catch (error) {
    alert(error.message);
  }
});

document.getElementById('category-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;

  const payload = {
    id: form.id.value.trim(),
    title: form.title.value.trim(),
    description: form.description.value.trim() || null,
    topic_id: form.topic_id.value.trim() || null,
    parent_id: form.parent_id.value.trim() || null,
  };

  try {
    await api('/admin/api/categories', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    await refreshAll();
  } catch (error) {
    alert(error.message);
  }
});

document.getElementById('question-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;

  let options = [];
  const optionsRaw = form.options_json.value.trim();
  if (optionsRaw) {
    try {
      options = JSON.parse(optionsRaw);
      if (!Array.isArray(options)) throw new Error('options must be a JSON array');
    } catch (error) {
      alert(`Invalid options JSON: ${error.message}`);
      return;
    }
  }

  const payload = {
    id: form.id.value.trim(),
    question: form.question.value.trim(),
    topic_id: form.topic_id.value.trim(),
    category_ids: form.category_ids.value.split(',').map((x) => x.trim()).filter(Boolean),
    difficulty: form.difficulty.value,
    correct_answer: form.correct_answer.value.trim(),
    options,
    hints: form.hints.value.split(',').map((x) => x.trim()).filter(Boolean),
    explanation: form.explanation.value.trim() || null,
    created_on: normalizeDate(form.created_on.value),
    created_by: form.created_by.value.trim() || null,
    shuffle_options: form.shuffle_options.checked,
    sources: form.sources.value.split(',').map((x) => x.trim()).filter(Boolean),
    updated_at: normalizeDateTimeLocal(form.updated_at.value),
    is_active: form.is_active.checked,
    allow_multiple_answers: form.allow_multiple_answers.checked,
  };

  try {
    await api('/admin/api/questions', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    form.shuffle_options.checked = true;
    form.is_active.checked = true;
    await refreshAll();
  } catch (error) {
    alert(error.message);
  }
});

refreshAll();
