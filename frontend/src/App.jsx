import { useState, useCallback } from 'react'
import UploadScreen from './screens/UploadScreen'
import DocumentOverview from './screens/DocumentOverview'
import QuizScreen from './screens/QuizScreen'
import ResultsScreen from './screens/ResultsScreen'
import SupportModal from './components/SupportModal'

export default function App() {
  const [screen, setScreen] = useState('upload')
  const [docId, setDocId] = useState(null)
  const [groupId, setGroupId] = useState(null)
  const [attemptId, setAttemptId] = useState(null)
  const [supportOpen, setSupportOpen] = useState(false)
  const handleSupportClose = useCallback(() => setSupportOpen(false), [])

  let content = null

  if (screen === 'upload') {
    content = <UploadScreen onDocumentReady={(id) => { setDocId(id); setScreen('overview') }} />
  } else if (screen === 'overview') {
    content = (
      <DocumentOverview
        docId={docId}
        onStartQuiz={(gid) => { setGroupId(gid); setScreen('quiz') }}
        onBack={() => setScreen('upload')}
      />
    )
  } else if (screen === 'quiz') {
    content = (
      <QuizScreen
        groupId={groupId}
        onComplete={(aid) => { setAttemptId(aid); setScreen('results') }}
        onBack={() => setScreen('overview')}
      />
    )
  } else if (screen === 'results') {
    content = (
      <ResultsScreen
        attemptId={attemptId}
        onRetry={() => setScreen('quiz')}
        onPickGroup={() => setScreen('overview')}
      />
    )
  }

  return (
    <div className="flex flex-col min-h-screen">
      <header className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-5 shrink-0 z-40">
        <span className="text-sm font-semibold text-gray-900 tracking-tight">UPSC Quiz</span>
        <button
          type="button"
          onClick={() => setSupportOpen(true)}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 transition-colors"
          aria-label="Open support form"
        >
          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full border border-gray-400 text-xs font-bold leading-none">?</span>
          Support
        </button>
      </header>

      <div className="flex-1 min-h-0">
        {content}
      </div>

      {supportOpen && <SupportModal onClose={handleSupportClose} />}
    </div>
  )
}
