import client from './client'

export async function uploadDocument(file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
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
