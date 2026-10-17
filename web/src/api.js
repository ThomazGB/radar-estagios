const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Small wrapper around fetch: builds the URL, sends JSON and turns HTTP errors into exceptions
export async function api(path, { method = 'GET', body, params } = {}) {
  const url = new URL(path, API_URL)
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value) url.searchParams.set(key, value)
  }
  const response = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail ?? `Erro ${response.status}`)
  }
  return response.status === 204 ? null : response.json()
}

export const STATUSES = [
  { id: 'interessado', label: 'Interessado' },
  { id: 'candidatei', label: 'Candidatei' },
  { id: 'entrevista', label: 'Entrevista' },
  { id: 'resultado', label: 'Resultado' },
]
