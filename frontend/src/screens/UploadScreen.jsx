import { useState, useCallback, useEffect } from 'react'
import { uploadDocument } from '../api/documents'
import { useDocumentPolling } from '../hooks/useDocumentPolling'

export default function UploadScreen({ onDocumentReady }) {
  const [docId, setDocId] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [uploadError, setUploadError] = useState(null)

  const { document, isPolling, error: pollError } = useDocumentPolling(docId)

  // Navigate once parsing is done
  useEffect(() => {
    if (document && document.status === 'ready') {
      onDocumentReady(document.id)
    }
  }, [document, onDocumentReady])

  const MAX_SIZE_MB = 50

  const handleFile = useCallback(async (file) => {
    if (!file || !file.name.endsWith('.pdf')) {
      setUploadError('Please upload a PDF file.')
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setUploadError(`File is too large. Maximum size is ${MAX_SIZE_MB} MB.`)
      return
    }
    setUploadError(null)
    setUploading(true)
    try {
      const doc = await uploadDocument(file)
      setDocId(doc.id)
    } catch {
      setUploadError('Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const onInputChange = (e) => handleFile(e.target.files[0])

  const isProcessing = uploading || isPolling

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <h1 className="text-3xl font-semibold text-gray-900 mb-2">UPSC Quiz</h1>
      <p className="text-gray-500 mb-10">Upload a PDF to start practicing</p>

      <div
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`w-full max-w-lg border-2 border-dashed rounded-2xl p-12 flex flex-col items-center gap-4 transition-colors
          ${dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'}`}
      >
        {isProcessing ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600 text-sm">
              {uploading ? 'Uploading...' : 'Parsing PDF, extracting questions...'}
            </p>
          </div>
        ) : (
          <>
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 16v-8m0 0l-3 3m3-3l3 3M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1" />
            </svg>
            <p className="text-gray-600">Drag and drop a PDF here, or</p>
            <label className="cursor-pointer bg-gray-900 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors">
              Browse file
              <input type="file" accept=".pdf" className="hidden" onChange={onInputChange} />
            </label>
            <p className="text-gray-400 text-xs">Maximum file size: 50 MB</p>
          </>
        )}
      </div>

      {(uploadError || pollError || document?.status === 'failed') && (
        <p className="mt-4 text-red-500 text-sm">
          {uploadError || pollError || 'Parsing failed. Please try a different PDF.'}
        </p>
      )}
    </div>
  )
}
