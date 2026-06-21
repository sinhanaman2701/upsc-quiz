import client from './client'

export async function getGroups(docId) {
  const { data } = await client.get(`/documents/${docId}/groups`)
  return data
}

export async function getQuestions(groupId) {
  const { data } = await client.get(`/groups/${groupId}/questions`)
  return data
}
