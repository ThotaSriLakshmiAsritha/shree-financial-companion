const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function readableApiMessage(value, fallback) {
  if (typeof value === 'string' && value.trim()) return value
  if (Array.isArray(value)) {
    const messages = value
      .map((item) => (typeof item === 'string' ? item : item?.msg || item?.message))
      .filter(Boolean)
    if (messages.length) return messages.join('. ')
  }
  if (value && typeof value === 'object') {
    if (typeof value.message === 'string' && value.message.trim()) return value.message
    if (typeof value.error === 'string' && value.error.trim()) return value.error
  }
  return fallback
}

async function request(path, options = {}, accessToken) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('Unable to reach the Sahachari API.')
  }

  if (!response.ok) {
    let message = 'The API request failed.'
    try {
      const body = await response.json()
      message = readableApiMessage(body?.detail ?? body?.error?.message, message)
    } catch {
      // Keep the stable fallback when the server response is not JSON.
    }
    throw new ApiError(message, response.status)
  }

  return response.json()
}

export function createTransactionProposal(payload, accessToken) {
  return request('/financial/proposals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function confirmTransactionProposal(proposalId, accessToken) {
  return request(`/financial/proposals/${proposalId}/confirm`, {
    method: 'POST',
  }, accessToken)
}

export function updatePreferredLanguage(language, accessToken) {
  return request('/auth/me', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferred_language: language }),
  }, accessToken)
}

export function updateProfile(payload, accessToken) {
  return request('/auth/me', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function getCurrentUser(accessToken) {
  return request('/auth/me', {}, accessToken)
}

export function getFinancialContext(accessToken) {
  return request('/financial/context', {}, accessToken)
}

export function getGoals(accessToken) {
  return request('/financial/goals', {}, accessToken)
}

export function createGoal(payload, accessToken) {
  return request('/financial/goals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function getGoalDetails(goalId, accessToken) {
  return request(`/financial/goals/${goalId}`, {}, accessToken)
}

export function distributeSavings(payload, accessToken) {
  return request('/financial/goals/savings/distribute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function getTransactions(accessToken) {
  return request('/financial/transactions', {}, accessToken)
}

export function getCurrentStory(language, accessToken) {
  const query = language ? `?language=${encodeURIComponent(language)}` : ''
  return request(`/stories/current${query}`, {}, accessToken)
}

export function narrateStoryScene(slug, sceneIndex, language, accessToken) {
  return request(`/stories/${encodeURIComponent(slug)}/narrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scene_index: sceneIndex, language }),
  }, accessToken)
}

export function narrateStory(slug, language, accessToken) {
  const query = language ? `?language=${encodeURIComponent(language)}` : ''
  return request(`/stories/${encodeURIComponent(slug)}/narrate-full${query}`, {
    method: 'POST',
  }, accessToken)
}

export function sendConversationMessage(payload, accessToken) {
  return request('/conversation/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function sendBrowserVoiceTurn(payload, accessToken) {
  return request('/voice/sarvam/browser/turn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}

export function transcribeBrowserVoice(payload, accessToken) {
  return request('/voice/sarvam/browser/transcribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, accessToken)
}
