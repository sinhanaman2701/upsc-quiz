import client from './client'

export async function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getDocument(id) {
  const { data } = await client.get(`/documents/${id}`)
  return data
}

export async function listDocuments() {
  const { data } = await client.get('/documents')
  return data
}
