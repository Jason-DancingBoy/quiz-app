const BASE = '/api'

async function request(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (resp.status === 401) {
    // Trigger browser to show Basic Auth dialog
    window.location.reload()
    throw new Error('Unauthorized')
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export const api = {
  // Documents
  createDocument(title, content) {
    return request('/documents', {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    })
  },
  listDocuments() {
    return request('/documents')
  },
  deleteDocument(id) {
    return request(`/documents/${id}`, { method: 'DELETE' })
  },

  // Quizzes
  generate(docId, difficulty, questionCount) {
    return request(`/documents/${docId}/generate`, {
      method: 'POST',
      body: JSON.stringify({ difficulty, question_count: questionCount }),
    })
  },
  getQuiz(quizId) {
    return request(`/quizzes/${quizId}`)
  },
  submitQuiz(quizId, answers) {
    return request(`/quizzes/${quizId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    })
  },
  getReview(quizId) {
    return request(`/quizzes/${quizId}/review`)
  },
  listQuizzes() {
    return request('/quizzes')
  },
}
