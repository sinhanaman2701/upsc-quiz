import { useState, useEffect, useRef } from 'react'
import { getDocument } from '../api/documents'

export function useDocumentPolling(docId) {
  const [document, setDocument] = useState(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!docId) return

    setIsPolling(true)

    const poll = async () => {
      try {
        const doc = await getDocument(docId)
        setDocument(doc)
        if (doc.status !== 'processing') {
          setIsPolling(false)
          clearInterval(intervalRef.current)
        }
      } catch (e) {
        setError(e.message)
        setIsPolling(false)
        clearInterval(intervalRef.current)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2000)

    return () => clearInterval(intervalRef.current)
  }, [docId])

  return { document, isPolling, error }
}
