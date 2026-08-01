const BASE = '/api'

// Trigger browser's native Basic Auth dialog via hidden iframe.
// Browsers only show the auth dialog for navigation requests, not fetch().
function triggerAuth() {
  return new Promise((resolve) => {
    const iframe = document.createElement('iframe')
    iframe.style.display = 'none'
    iframe.src = BASE + '/documents'
    iframe.onload = () => {
      document.body.removeChild(iframe)
      resolve()
    }
    document.body.appendChild(iframe)
  })
}

async function request(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (resp.status === 401) {
    await triggerAuth()
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
  async uploadDocument(file) {
    const formData = new FormData()
    formData.append('file', file)
    const resp = await fetch(BASE + '/documents/upload', {
      method: 'POST',
      body: formData,
    })
    if (resp.status === 401) {
      await triggerAuth()
      window.location.reload()
      throw new Error('Unauthorized')
    }
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }))
      throw new Error(err.detail || `HTTP ${resp.status}`)
    }
    return resp.json()
  },
  listDocuments() {
    return request('/documents')
  },
  getDocument(id) {
    return request(`/documents/${id}?include_content=true`)
  },
  deleteDocument(id) {
    return request(`/documents/${id}`, { method: 'DELETE' })
  },

  // Vault
  vaultGenerate(difficulty, questionCount) {
    return request('/vault/generate', {
      method: 'POST',
      body: JSON.stringify({ difficulty, question_count: questionCount }),
    })
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
