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

function flattenCategories(items, depth = 0, out = []) {
  for (const item of items) {
    out.push({ ...item, depth });
    flattenCategories(item.children || [], depth + 1, out);
  }
  return out;
}

async function loadCategories() {
  const categories = await api('/admin/api/categories');
  const flat = flattenCategories(categories);
  categoryList.innerHTML = '';
  for (const category of flat) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${'— '.repeat(category.depth)}${category.title}</strong> <span class="muted">(${category.id})</span><br>${category.description || ''}`;

    const actions = document.createElement('div');
    actions.className = 'inline-actions';

    const editButton = document.createElement('button');
    editButton.textContent = 'Edit';
    editButton.onclick = async () => {
      const title = prompt('New category title', category.title);
      if (!title) return;
      const description = prompt('Description', category.description || '') || null;
      await api(`/admin/api/categories/${category.id}`, {
        method: 'PUT',
        body: JSON.stringify({ title, description }),
      });
      await refreshAll();
    };

    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = async () => {
      if (!confirm(`Delete category ${category.id}?`)) return;
      await api(`/admin/api/categories/${category.id}`, { method: 'DELETE' });
      await refreshAll();
    };

    actions.append(editButton, deleteButton);
    li.append(actions);
    categoryList.append(li);
  }
}

async function loadQuestions() {
  const questions = await api('/admin/api/questions');
  questionList.innerHTML = '';

  for (const question of questions) {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>${question.question}</strong>
      <div class="muted">ID: ${question.id} | Difficulty: ${question.difficulty}</div>
      <div>Categories: ${question.categories.map((c) => c.title).join(', ')}</div>
      <div>Answer: ${question.correct_answer}</div>
    `;

    const actions = document.createElement('div');
    actions.className = 'inline-actions';

    const toggleButton = document.createElement('button');
    toggleButton.textContent = question.is_active ? 'Deactivate' : 'Activate';
    toggleButton.onclick = async () => {
      await api(`/admin/api/questions/${question.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          question: question.question,
          category_ids: question.categories.map((c) => c.id),
          difficulty: question.difficulty,
          correct_answer: question.correct_answer,
          options: question.options,
          hints: question.hints.map((h) => h.text),
          explanation: question.explanation,
          is_active: !question.is_active,
        }),
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
  analyticsJson.textContent = JSON.stringify({
    questions_by_difficulty: data.questions_by_difficulty,
    questions_per_category: data.questions_per_category,
  }, null, 2);
}

async function refreshAll() {
  try {
    await Promise.all([loadCategories(), loadQuestions(), loadReports(), loadAnalytics()]);
  } catch (error) {
    alert(error.message);
  }
}

document.getElementById('category-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  const payload = {
    id: form.id.value.trim(),
    title: form.title.value.trim(),
    description: form.description.value.trim() || null,
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
  const payload = {
    id: form.id.value.trim(),
    question: form.question.value.trim(),
    category_ids: form.category_ids.value.split(',').map((x) => x.trim()).filter(Boolean),
    difficulty: form.difficulty.value,
    correct_answer: form.correct_answer.value.trim(),
    options: [],
    hints: form.hints.value.split(',').map((x) => x.trim()).filter(Boolean),
    explanation: form.explanation.value.trim() || null,
    is_active: true,
  };

  try {
    await api('/admin/api/questions', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    await refreshAll();
  } catch (error) {
    alert(error.message);
  }
});

refreshAll();
