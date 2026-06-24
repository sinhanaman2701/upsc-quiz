import client from './client'

export async function submitSupportTicket(message, imageFile) {
  const form = new FormData()
  form.append('message', message)
  if (imageFile) {
    form.append('image', imageFile)
  }

  const { data } = await client.post('/support', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listSupportTickets() {
  const { data } = await client.get('/support')
  return data
}

export async function toggleResolve(id) {
  const { data } = await client.patch(`/support/${id}/resolve`)
  return data
}
