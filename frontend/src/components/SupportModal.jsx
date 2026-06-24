import { useEffect, useState } from 'react'
import { submitSupportTicket } from '../api/support'

export default function SupportModal({ onClose }) {
  const [message, setMessage] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    if (!previewUrl) return undefined

    return () => {
      URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  useEffect(() => {
    if (!successMessage) return undefined

    const timeoutId = window.setTimeout(() => {
      onClose()
    }, 2000)

    return () => window.clearTimeout(timeoutId)
  }, [onClose, successMessage])

  const handleImageChange = (event) => {
    const file = event.target.files?.[0] ?? null
    setImageFile(file)
    setErrorMessage('')

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    setPreviewUrl(file ? URL.createObjectURL(file) : null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!message.trim()) {
      setErrorMessage('Please describe the issue.')
      return
    }

    setSubmitting(true)
    setErrorMessage('')

    try {
      await submitSupportTicket(message.trim(), imageFile)
      setSuccessMessage('Thank you! Your report has been submitted.')
    } catch {
      setErrorMessage('Could not submit your report.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 px-4 py-6">
      <div className="relative w-full max-w-lg rounded-3xl border border-gray-200 bg-white p-6 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
          aria-label="Close support form"
        >
          ×
        </button>

        <div className="mb-6 pr-10">
          <h2 className="text-xl font-semibold text-gray-900">Report an issue</h2>
          <p className="mt-1 text-sm text-gray-500">Tell us what went wrong and attach a screenshot if helpful.</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-2">
            <span className="text-sm font-medium text-gray-700">Issue description</span>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Describe the issue"
              required
              rows={5}
              className="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-gray-400"
            />
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-sm font-medium text-gray-700">Screenshot (optional)</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:rounded-xl file:border-0 file:bg-gray-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-gray-700"
            />
          </label>

          {previewUrl && (
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-gray-50">
              <img src={previewUrl} alt="Selected support attachment preview" className="max-h-64 w-full object-contain" />
            </div>
          )}

          {successMessage && <p className="text-sm text-green-600">{successMessage}</p>}
          {errorMessage && <p className="text-sm text-red-500">{errorMessage}</p>}

          <button
            type="submit"
            disabled={submitting || !!successMessage}
            className="rounded-2xl bg-gray-900 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? 'Submitting' : 'Submit'}
          </button>
        </form>
      </div>
    </div>
  )
}
