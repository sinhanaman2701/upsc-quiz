import { useState } from 'react'
import UploadScreen from './screens/UploadScreen'
import DocumentOverview from './screens/DocumentOverview'
import QuizScreen from './screens/QuizScreen'
import ResultsScreen from './screens/ResultsScreen'

export default function App() {
  const [screen, setScreen] = useState('upload')
  const [docId, setDocId] = useState(null)
  const [groupId, setGroupId] = useState(null)
  const [attemptId, setAttemptId] = useState(null)

  if (screen === 'upload') return (
    <UploadScreen onDocumentReady={(id) => { setDocId(id); setScreen('overview') }} />
  )

  if (screen === 'overview') return (
    <DocumentOverview
      docId={docId}
      onStartQuiz={(gid) => { setGroupId(gid); setScreen('quiz') }}
      onBack={() => setScreen('upload')}
    />
  )

  if (screen === 'quiz') return (
    <QuizScreen
      groupId={groupId}
      onComplete={(aid) => { setAttemptId(aid); setScreen('results') }}
      onBack={() => setScreen('overview')}
    />
  )

  if (screen === 'results') return (
    <ResultsScreen
      attemptId={attemptId}
      onRetry={() => setScreen('quiz')}
      onPickGroup={() => setScreen('overview')}
    />
  )
}
