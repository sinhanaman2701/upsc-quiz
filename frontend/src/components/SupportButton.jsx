import { useState, useCallback } from 'react'
import SupportModal from './SupportModal'

export default function SupportButton() {
  const [open, setOpen] = useState(false)
  const handleClose = useCallback(() => setOpen(false), [])

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-2xl font-semibold text-white shadow-lg transition-colors hover:bg-gray-700"
        aria-label="Open support form"
      >
        ?
      </button>

      {open && <SupportModal onClose={handleClose} />}
    </>
  )
}
