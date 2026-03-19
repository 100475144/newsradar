const API_BASE_URL = 'http://localhost:8000/api/v1'

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error(`Error ${response.status}`)
  }

  return response.json()
}