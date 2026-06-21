import client from './client'

export async function startAttempt(groupId) {
  const { data } = await client.post('/attempts', { group_id: groupId })
  return data
}

export async function submitAttempt(attemptId, responses) {
  const { data } = await client.post(`/attempts/${attemptId}/submit`, { responses })
  return data
}

export async function getAttempt(attemptId) {
  const { data } = await client.get(`/attempts/${attemptId}`)
  return data
}
